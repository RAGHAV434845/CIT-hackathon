"""Repository management routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, get_current_uid
from services.repo_service import (
    create_repo_record, clone_github_repo, handle_zip_upload,
    list_user_repos, get_repo, delete_repo
)
from services.firebase_service import update_document, query_collection, get_user_doc
import requests as http_requests

repo_bp = Blueprint("repos", __name__)


@repo_bp.route("", methods=["POST"])
@require_auth
def create_repository():
    """Create a new repository (upload ZIP or clone GitHub URL)."""
    uid = get_current_uid()
    source = request.form.get("source") or (request.get_json() or {}).get("source")

    if source == "github":
        data = request.get_json() or {}
        github_url = data.get("github_url", "").strip()
        name = data.get("name", github_url.split("/")[-1] if "/" in github_url else "repo")

        if not github_url:
            return jsonify({"error": "github_url required"}), 400

        repo_id = create_repo_record(uid, name, "github", github_url)
        if not repo_id:
            return jsonify({"error": "Failed to create repository record"}), 500

        # Clone in foreground (within 2-min timeout)
        local_path = clone_github_repo(github_url, repo_id)
        if not local_path:
            update_document("repositories", repo_id, {"status": "failed"})
            return jsonify({"error": "Failed to clone repository"}), 500

        update_document("repositories", repo_id, {"status": "pending"})
        return jsonify({"repo_id": repo_id, "name": name, "status": "pending"}), 201

    elif source == "upload":
        file = request.files.get("file")
        name = request.form.get("name", "uploaded-project")

        if not file:
            return jsonify({"error": "ZIP file required"}), 400
        if not file.filename.endswith(".zip"):
            return jsonify({"error": "Only ZIP files supported"}), 400

        repo_id = create_repo_record(uid, name, "upload")
        if not repo_id:
            return jsonify({"error": "Failed to create repository record"}), 500

        local_path = handle_zip_upload(file, repo_id)
        if not local_path:
            update_document("repositories", repo_id, {"status": "failed"})
            return jsonify({"error": "Failed to extract ZIP"}), 500

        update_document("repositories", repo_id, {"status": "pending"})
        return jsonify({"repo_id": repo_id, "name": name, "status": "pending"}), 201

    return jsonify({"error": "source must be 'github' or 'upload'"}), 400


@repo_bp.route("", methods=["GET"])
@require_auth
def list_repos():
    """List current user's repositories + repos shared via collaboration."""
    uid = get_current_uid()
    own_repos = list_user_repos(uid)

    # Also include repos where user is a collaborator
    all_repos = query_collection("repositories", limit=1000)
    collab_repos = [r for r in all_repos
                    if uid in r.get("collaborators", []) and r.get("owner_uid") != uid]

    # Merge, avoiding duplicates
    own_ids = {r.get("id") for r in own_repos}
    for cr in collab_repos:
        if cr.get("id") not in own_ids:
            cr["is_collaborator"] = True
            own_repos.append(cr)

    return jsonify({"repositories": own_repos}), 200


@repo_bp.route("/<repo_id>", methods=["GET"])
@require_auth
def get_repo_details(repo_id):
    """Get repository details."""
    repo = get_repo(repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404
    return jsonify(repo), 200


@repo_bp.route("/<repo_id>", methods=["DELETE"])
@require_auth
def delete_repository(repo_id):
    """Delete a repository."""
    uid = get_current_uid()
    success = delete_repo(repo_id, uid)
    if success:
        return jsonify({"message": "Repository deleted"}), 200
    return jsonify({"error": "Repository not found or access denied"}), 404


@repo_bp.route("/search", methods=["GET"])
@require_auth
def search_public_repos():
    """Search GitHub public repositories."""
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Search query (q) required"}), 400

    try:
        resp = http_requests.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "per_page": 10, "sort": "stars"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            results = [
                {
                    "name": r["full_name"],
                    "description": r.get("description", ""),
                    "url": r["html_url"],
                    "stars": r["stargazers_count"],
                    "language": r.get("language", ""),
                }
                for r in data.get("items", [])
            ]
            return jsonify({"results": results}), 200
        return jsonify({"error": "GitHub API error"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ────────────── Collaborator endpoints ──────────────

@repo_bp.route("/<repo_id>/collaborators", methods=["GET"])
@require_auth
def get_collaborators(repo_id):
    """List collaborators of a repository."""
    repo = get_repo(repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    uid = get_current_uid()
    if repo.get("owner_uid") != uid and uid not in repo.get("collaborators", []):
        return jsonify({"error": "Access denied"}), 403

    collaborator_uids = repo.get("collaborators", [])
    collaborators = []
    for c_uid in collaborator_uids:
        user_doc = get_user_doc(c_uid)
        if user_doc:
            collaborators.append({
                "uid": c_uid,
                "email": user_doc.get("email", ""),
                "name": user_doc.get("name", user_doc.get("email", "")),
            })
        else:
            collaborators.append({"uid": c_uid, "email": "", "name": "Unknown"})

    return jsonify({"collaborators": collaborators}), 200


@repo_bp.route("/<repo_id>/collaborators", methods=["POST"])
@require_auth
def add_collaborator(repo_id):
    """Add a collaborator to a repository by email."""
    repo = get_repo(repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    uid = get_current_uid()
    if repo.get("owner_uid") != uid:
        return jsonify({"error": "Only the owner can add collaborators"}), 403

    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    if not email:
        return jsonify({"error": "email is required"}), 400

    # Look up user by email
    all_users = query_collection("users", limit=5000)
    target_user = None
    for u in all_users:
        if u.get("email", "").lower() == email:
            target_user = u
            break

    if not target_user:
        return jsonify({"error": f"No user found with email {email}"}), 404

    target_uid = target_user.get("id") or target_user.get("uid")
    if not target_uid:
        return jsonify({"error": "Could not resolve user ID"}), 500

    if target_uid == uid:
        return jsonify({"error": "Cannot add yourself as a collaborator"}), 400

    collaborators = repo.get("collaborators", [])
    if target_uid in collaborators:
        return jsonify({"message": "User is already a collaborator"}), 200

    collaborators.append(target_uid)
    update_document("repositories", repo_id, {"collaborators": collaborators})

    return jsonify({"message": f"Added {email} as collaborator"}), 200


@repo_bp.route("/<repo_id>/collaborators/<collab_uid>", methods=["DELETE"])
@require_auth
def remove_collaborator(repo_id, collab_uid):
    """Remove a collaborator from a repository."""
    repo = get_repo(repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    uid = get_current_uid()
    if repo.get("owner_uid") != uid:
        return jsonify({"error": "Only the owner can remove collaborators"}), 403

    collaborators = repo.get("collaborators", [])
    if collab_uid not in collaborators:
        return jsonify({"error": "User is not a collaborator"}), 404

    collaborators.remove(collab_uid)
    update_document("repositories", repo_id, {"collaborators": collaborators})

    return jsonify({"message": "Collaborator removed"}), 200
