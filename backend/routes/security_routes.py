"""Security scanning routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, get_current_uid
from services.repo_service import get_repo, get_repo_path
from services.firebase_service import update_document, log_analytics_event
from engine.security_scanner import SecurityScanner, auto_remove_secrets

security_bp = Blueprint("security", __name__)


@security_bp.route("/<repo_id>", methods=["GET"])
@require_auth
def get_security_scan(repo_id):
    """Run security scan and return results."""
    uid = get_current_uid()
    repo = get_repo(repo_id)

    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    repo_path = get_repo_path(repo_id)
    if not repo_path:
        return jsonify({"error": "Repository files not found"}), 404

    scanner = SecurityScanner(repo_path)
    issues = scanner.scan()

    # Store results
    scan_result = {
        "total_issues": len(issues),
        "resolved": 0,
        "issues": issues[:200],  # Cap for storage
    }

    update_document("repositories", repo_id, {"security_scan": scan_result})
    log_analytics_event("security_scan", uid, repo_id, {"total_issues": len(issues)})

    return jsonify(scan_result), 200


@security_bp.route("/<repo_id>/resolve", methods=["POST"])
@require_auth
def resolve_issues(repo_id):
    """Resolve security issues (auto-remove, ignore, mask)."""
    uid = get_current_uid()
    repo = get_repo(repo_id)

    if not repo:
        return jsonify({"error": "Repository not found"}), 404
    if repo.get("owner_uid") != uid:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    action = data.get("action", "").lower()  # auto_remove, ignore, mask

    repo_path = get_repo_path(repo_id)
    scan = repo.get("security_scan", {})
    issues = scan.get("issues", [])

    if action == "auto_remove":
        if not repo_path:
            return jsonify({"error": "Repository files not found"}), 404
        removed = auto_remove_secrets(repo_path, issues)
        scan["resolved"] = removed
        scan["issues"] = issues
        update_document("repositories", repo_id, {"security_scan": scan})
        return jsonify({"message": f"Auto-removed {removed} secrets", "resolved": removed}), 200

    elif action == "ignore":
        issue_indices = data.get("indices", [])
        for idx in issue_indices:
            if 0 <= idx < len(issues):
                issues[idx]["status"] = "ignored"
        scan["issues"] = issues
        update_document("repositories", repo_id, {"security_scan": scan})
        return jsonify({"message": f"Ignored {len(issue_indices)} issues"}), 200

    elif action == "mask":
        for issue in issues:
            if issue.get("status") == "detected":
                issue["status"] = "masked"
        scan["issues"] = issues
        update_document("repositories", repo_id, {"security_scan": scan})
        return jsonify({"message": "All detected issues masked"}), 200

    return jsonify({"error": "action must be: auto_remove, ignore, mask"}), 400
