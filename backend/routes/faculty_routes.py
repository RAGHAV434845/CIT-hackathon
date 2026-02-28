"""Faculty management routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, require_role, get_current_uid
from services.firebase_service import (
    add_document, get_document, update_document,
    query_collection, log_analytics_event
)
from services.repo_service import get_repo

faculty_bp = Blueprint("faculty", __name__)


@faculty_bp.route("/projects", methods=["POST"])
@require_auth
@require_role("faculty", "hod")
def create_project():
    """Create a project folder."""
    uid = get_current_uid()
    data = request.get_json()

    if not data or "title" not in data:
        return jsonify({"error": "title required"}), 400

    project = {
        "faculty_uid": uid,
        "title": data["title"],
        "description": data.get("description", ""),
        "student_uids": data.get("student_uids", []),
        "repo_ids": data.get("repo_ids", []),
        "scores": {
            "architecture": 0,
            "documentation": 0,
            "code_quality": 0,
            "overall": 0,
        },
        "status": "active",
    }

    project_id = add_document("projects", project)
    log_analytics_event("project_created", uid, metadata={"project_id": project_id})

    return jsonify({"project_id": project_id, "project": project}), 201


@faculty_bp.route("/projects", methods=["GET"])
@require_auth
@require_role("faculty", "hod")
def list_projects():
    """List faculty's projects."""
    uid = get_current_uid()
    projects = query_collection(
        "projects",
        filters=[("faculty_uid", "==", uid)],
        limit=100,
    )
    return jsonify({"projects": projects}), 200


@faculty_bp.route("/projects/<project_id>", methods=["GET"])
@require_auth
@require_role("faculty", "hod")
def get_project(project_id):
    """Get project details."""
    project = get_document("projects", project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404
    return jsonify(project), 200


@faculty_bp.route("/projects/<project_id>/score", methods=["PUT"])
@require_auth
@require_role("faculty", "hod")
def score_project(project_id):
    """Score a project."""
    uid = get_current_uid()
    project = get_document("projects", project_id)

    if not project:
        return jsonify({"error": "Project not found"}), 404
    if project.get("faculty_uid") != uid:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    scores = {}

    for field in ["architecture", "documentation", "code_quality", "overall"]:
        if field in data:
            val = data[field]
            if not isinstance(val, (int, float)) or val < 0 or val > 10:
                return jsonify({"error": f"{field} must be a number 0-10"}), 400
            scores[f"scores.{field}"] = val

    if not scores:
        return jsonify({"error": "Provide at least one score field"}), 400

    update_document("projects", project_id, scores)
    log_analytics_event("project_scored", uid, metadata={"project_id": project_id})

    return jsonify({"message": "Scores updated"}), 200


@faculty_bp.route("/projects/<project_id>/add-student", methods=["POST"])
@require_auth
@require_role("faculty", "hod")
def add_student_to_project(project_id):
    """Add a student to a project."""
    data = request.get_json()
    student_uid = data.get("student_uid")
    if not student_uid:
        return jsonify({"error": "student_uid required"}), 400

    project = get_document("projects", project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    students = project.get("student_uids", [])
    if student_uid not in students:
        students.append(student_uid)
        update_document("projects", project_id, {"student_uids": students})

    return jsonify({"message": "Student added"}), 200


@faculty_bp.route("/projects/<project_id>/add-repo", methods=["POST"])
@require_auth
@require_role("faculty", "hod")
def add_repo_to_project(project_id):
    """Add a repository to a project."""
    data = request.get_json()
    repo_id = data.get("repo_id")
    if not repo_id:
        return jsonify({"error": "repo_id required"}), 400

    project = get_document("projects", project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    repos = project.get("repo_ids", [])
    if repo_id not in repos:
        repos.append(repo_id)
        update_document("projects", project_id, {"repo_ids": repos})

    return jsonify({"message": "Repository added"}), 200


@faculty_bp.route("/students", methods=["GET"])
@require_auth
@require_role("faculty", "hod")
def list_students():
    """List students (optionally filtered by department)."""
    dept = request.args.get("department", "")

    filters = [("role", "==", "student")]
    if dept:
        filters.append(("department", "==", dept))

    students = query_collection("users", filters=filters, limit=200)
    # Remove sensitive fields
    for s in students:
        s.pop("mentor_id", None)

    return jsonify({"students": students}), 200
