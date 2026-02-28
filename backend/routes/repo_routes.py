"""Repository management routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, get_current_uid
from services.repo_service import (
    create_repo_record, clone_github_repo, handle_zip_upload,
    list_user_repos, get_repo, delete_repo
)
from services.firebase_service import update_document
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
    """List current user's repositories."""
    uid = get_current_uid()
    repos = list_user_repos(uid)
    return jsonify({"repositories": repos}), 200


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
