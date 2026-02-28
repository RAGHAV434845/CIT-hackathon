"""Analytics routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, require_role, get_current_uid, get_current_user
from services.firebase_service import query_collection, get_db
from collections import defaultdict

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard", methods=["GET"])
@require_auth
def dashboard_stats():
    """Get dashboard analytics for current user."""
    uid = get_current_uid()
    user = get_current_user()
    role = user.get("role", "student")

    # Base stats for all users
    stats = {
        "projects_analyzed": 0,
        "documents_generated": 0,
        "diagrams_generated": 0,
        "security_issues_found": 0,
        "recent_activity": [],
    }

    # Count user's repos
    repos = query_collection("repositories", filters=[("owner_uid", "==", uid)], limit=500)
    stats["projects_analyzed"] = len([r for r in repos if r.get("status") == "completed"])
    stats["total_repos"] = len(repos)

    # Sum security issues
    for repo in repos:
        scan = repo.get("security_scan") or {}
        stats["security_issues_found"] += scan.get("total_issues", 0)

    # Count documents
    docs = query_collection("documents", filters=[("owner_uid", "==", uid)], limit=500)
    stats["documents_generated"] = len(docs)

    # Count diagrams
    diagrams = query_collection("diagrams", filters=[("owner_uid", "==", uid)], limit=500)
    stats["diagrams_generated"] = len(diagrams)

    # Recent analytics events
    events = query_collection(
        "analytics",
        filters=[("user_uid", "==", uid)],
        limit=20,
    )
    stats["recent_activity"] = events[:20]

    # Monthly breakdown (from repos)
    monthly = defaultdict(int)
    for repo in repos:
        created = repo.get("created_at")
        if created:
            try:
                key = created.strftime("%Y-%m") if hasattr(created, 'strftime') else str(created)[:7]
                monthly[key] += 1
            except Exception:
                pass
    stats["projects_per_month"] = dict(monthly)

    return jsonify(stats), 200


@analytics_bp.route("/user/<target_uid>", methods=["GET"])
@require_auth
@require_role("faculty", "hod")
def user_stats(target_uid):
    """Get analytics for a specific user (faculty/HOD only)."""
    repos = query_collection("repositories", filters=[("owner_uid", "==", target_uid)], limit=500)

    stats = {
        "total_repos": len(repos),
        "completed_analyses": len([r for r in repos if r.get("status") == "completed"]),
        "total_security_issues": sum(
            (r.get("security_scan") or {}).get("total_issues", 0) for r in repos
        ),
    }

    docs = query_collection("documents", filters=[("owner_uid", "==", target_uid)], limit=500)
    stats["total_documents"] = len(docs)

    return jsonify(stats), 200
