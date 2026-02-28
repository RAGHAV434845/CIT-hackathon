"""Faculty management routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, require_role, get_current_uid
from services.firebase_service import (
    add_document, get_document, update_document,
    query_collection, log_analytics_event, get_user_doc
)
from services.repo_service import get_repo
from datetime import datetime

faculty_bp = Blueprint("faculty", __name__)


# ── helper ──────────────────────────────────────────────
def _resolve_uid(identifier):
    """Resolve an email or UID string to a Firebase UID.
    Returns (uid, email) or (None, None)."""
    identifier = identifier.strip()
    if not identifier:
        return None, None

    # If it looks like an email, search users collection
    if "@" in identifier:
        users = query_collection("users", limit=5000)
        for u in users:
            if u.get("email", "").lower() == identifier.lower():
                return u.get("uid") or u.get("id"), u.get("email")
        return None, None

    # Otherwise treat as UID directly; verify it exists
    from services.firebase_service import get_user_doc
    user = get_user_doc(identifier)
    if user:
        return identifier, user.get("email", "")
    return identifier, ""   # allow even if doc missing – auth UID may exist


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
        "deadline": data.get("deadline", ""),
        "student_uids": [],
        "submissions": {},       # {student_uid: {github_url, submitted_at}}
        "student_marks": {},     # {student_uid: {marks, comments}}
        "status": "active",
    }

    project_id = add_document("projects", project)
    log_analytics_event("project_created", uid, metadata={"project_id": project_id})

    return jsonify({"project_id": project_id, "project": project}), 201


@faculty_bp.route("/projects", methods=["GET"])
@require_auth
@require_role("faculty", "hod")
def list_projects():
    """List faculty's projects with student details."""
    uid = get_current_uid()
    projects = query_collection(
        "projects",
        filters=[("faculty_uid", "==", uid)],
        limit=100,
    )

    # Enrich each project with student info
    for p in projects:
        enriched_students = []
        for s_uid in p.get("student_uids", []):
            from services.firebase_service import get_user_doc
            u = get_user_doc(s_uid)
            sub = (p.get("submissions") or {}).get(s_uid)
            marks_info = (p.get("student_marks") or {}).get(s_uid)
            enriched_students.append({
                "uid": s_uid,
                "email": u.get("email", "") if u else "",
                "name": u.get("username", u.get("email", "")) if u else s_uid,
                "submission": sub,
                "marks": marks_info.get("marks") if marks_info else None,
                "comments": marks_info.get("comments", "") if marks_info else "",
            })
        p["students_detail"] = enriched_students

    return jsonify({"projects": projects}), 200


@faculty_bp.route("/projects/<project_id>", methods=["GET"])
@require_auth
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
    """Give marks to a specific student's submission (out of 100)."""
    uid = get_current_uid()
    project = get_document("projects", project_id)

    if not project:
        return jsonify({"error": "Project not found"}), 404
    if project.get("faculty_uid") != uid:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    student_uid = data.get("student_uid", "").strip()
    marks = data.get("marks")
    comments = data.get("comments", "")

    if not student_uid:
        return jsonify({"error": "student_uid is required"}), 400
    if student_uid not in project.get("student_uids", []):
        return jsonify({"error": "Student not assigned to this project"}), 400
    if marks is None or not isinstance(marks, (int, float)) or marks < 0 or marks > 100:
        return jsonify({"error": "marks must be a number 0-100"}), 400

    student_marks = project.get("student_marks") or {}
    student_marks[student_uid] = {"marks": marks, "comments": comments}

    update_document("projects", project_id, {"student_marks": student_marks})
    log_analytics_event("project_scored", uid,
                        metadata={"project_id": project_id, "student_uid": student_uid, "marks": marks})

    return jsonify({"message": "Marks updated", "marks": marks}), 200


@faculty_bp.route("/projects/<project_id>/add-student", methods=["POST"])
@require_auth
@require_role("faculty", "hod")
def add_student_to_project(project_id):
    """Add a student to a project (accepts email or UID)."""
    data = request.get_json()
    identifier = data.get("student_uid", "").strip()
    if not identifier:
        return jsonify({"error": "student email or UID required"}), 400

    resolved_uid, email = _resolve_uid(identifier)
    if not resolved_uid:
        return jsonify({"error": f"No user found for '{identifier}'"}), 404

    project = get_document("projects", project_id)
    if not project:
        return jsonify({"error": "Project not found"}), 404

    students = project.get("student_uids", [])
    if resolved_uid not in students:
        students.append(resolved_uid)
        update_document("projects", project_id, {"student_uids": students})

    return jsonify({"message": f"Student added ({email or resolved_uid})"}), 200


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
    for s in students:
        s.pop("mentor_id", None)

    return jsonify({"students": students}), 200


# =========================================================
# Student-facing endpoints
# =========================================================

@faculty_bp.route("/my-projects", methods=["GET"])
@require_auth
def student_my_projects():
    """List projects assigned to the current student (with their marks)."""
    uid = get_current_uid()
    user = get_user_doc(uid)
    user_email = (user.get("email", "") if user else "").lower()

    all_projects = query_collection("projects", limit=500)
    # Match by UID or email (handles old projects that stored email instead of UID)
    my_projects = []
    for p in all_projects:
        s_uids = p.get("student_uids", [])
        if uid in s_uids or (user_email and user_email in [s.lower() for s in s_uids]):
            my_projects.append(p)

    # Flatten per-student marks & submission into top-level for convenience
    result = []
    for p in my_projects:
        proj = dict(p)
        # Try matching by UID first, then by email
        marks_dict = p.get("student_marks") or {}
        sub_dict = p.get("submissions") or {}
        my_marks = marks_dict.get(uid) or (marks_dict.get(user_email) if user_email else None)
        my_sub = sub_dict.get(uid) or (sub_dict.get(user_email) if user_email else None)
        proj["my_marks"] = my_marks.get("marks") if my_marks else None
        proj["my_comments"] = my_marks.get("comments", "") if my_marks else ""
        proj["my_submission"] = my_sub
        result.append(proj)

    return jsonify({"projects": result}), 200


@faculty_bp.route("/projects/<project_id>/submit", methods=["POST"])
@require_auth
def submit_project(project_id):
    """Student submits a GitHub URL for an assigned project."""
    uid = get_current_uid()
    project = get_document("projects", project_id)

    if not project:
        return jsonify({"error": "Project not found"}), 404
    s_uids = project.get("student_uids", [])
    from services.firebase_service import get_user_doc as _get_user
    _user = _get_user(uid)
    _email = (_user.get("email", "") if _user else "").lower()
    if uid not in s_uids and _email not in [s.lower() for s in s_uids]:
        return jsonify({"error": "You are not assigned to this project"}), 403

    data = request.get_json() or {}
    github_url = data.get("github_url", "").strip()
    if not github_url:
        return jsonify({"error": "github_url required"}), 400

    submissions = project.get("submissions") or {}
    submissions[uid] = {
        "github_url": github_url,
        "submitted_at": datetime.utcnow().isoformat(),
    }
    update_document("projects", project_id, {"submissions": submissions})

    return jsonify({"message": "Submission recorded", "github_url": github_url}), 200
