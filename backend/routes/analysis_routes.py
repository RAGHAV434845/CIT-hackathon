"""Analysis routes."""

from flask import Blueprint, jsonify
from middleware.auth_middleware import require_auth, get_current_uid
from services.repo_service import get_repo, get_repo_path
from services.firebase_service import update_document, log_analytics_event
from engine.analyzer import CodebaseAnalyzer

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/<repo_id>", methods=["POST"])
@require_auth
def start_analysis(repo_id):
    """Start static code analysis on a repository."""
    uid = get_current_uid()
    repo = get_repo(repo_id)

    if not repo:
        return jsonify({"error": "Repository not found"}), 404
    if repo.get("owner_uid") != uid:
        return jsonify({"error": "Access denied"}), 403

    repo_path = get_repo_path(repo_id)
    if not repo_path:
        return jsonify({"error": "Repository files not found. Please re-upload."}), 404

    # Update status to analyzing
    update_document("repositories", repo_id, {"status": "analyzing"})

    try:
        analyzer = CodebaseAnalyzer(repo_path)
        result = analyzer.analyze()

        # Store results
        update_document("repositories", repo_id, {
            "status": "completed",
            "analysis_result": result,
        })

        log_analytics_event("analysis", uid, repo_id, {
            "framework": result.get("framework"),
            "total_files": result.get("total_files"),
        })

        return jsonify({
            "status": "completed",
            "analysis": result,
        }), 200

    except Exception as e:
        update_document("repositories", repo_id, {"status": "failed"})
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


@analysis_bp.route("/<repo_id>", methods=["GET"])
@require_auth
def get_analysis(repo_id):
    """Get analysis results for a repository."""
    repo = get_repo(repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    analysis = repo.get("analysis_result")
    if not analysis:
        return jsonify({"error": "Analysis not yet completed", "status": repo.get("status")}), 404

    return jsonify({
        "status": repo.get("status"),
        "analysis": analysis,
    }), 200


@analysis_bp.route("/<repo_id>/status", methods=["GET"])
@require_auth
def get_analysis_status(repo_id):
    """Get analysis status."""
    repo = get_repo(repo_id)
    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    return jsonify({"status": repo.get("status", "unknown")}), 200
