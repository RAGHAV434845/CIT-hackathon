"""HOD management routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, require_role, get_current_uid
from services.firebase_service import (
    add_document, get_document, update_document,
    query_collection, log_analytics_event, get_user_doc
)

hod_bp = Blueprint("hod", __name__)


@hod_bp.route("/faculty", methods=["GET"])
@require_auth
@require_role("hod")
def list_faculty():
    """List all faculty members."""
    dept = request.args.get("department", "")
    filters = [("role", "==", "faculty")]
    if dept:
        filters.append(("department", "==", dept))

    faculty = query_collection("users", filters=filters, limit=200)
    return jsonify({"faculty": faculty}), 200


@hod_bp.route("/students", methods=["GET"])
@require_auth
@require_role("hod")
def list_all_students():
    """List all students."""
    dept = request.args.get("department", "")
    filters = [("role", "==", "student")]
    if dept:
        filters.append(("department", "==", dept))

    students = query_collection("users", filters=filters, limit=500)
    return jsonify({"students": students}), 200


@hod_bp.route("/assign-mentor", methods=["POST"])
@require_auth
@require_role("hod")
def assign_mentor():
    """Assign a faculty mentor to a student."""
    uid = get_current_uid()
    data = request.get_json()

    faculty_uid = data.get("faculty_uid")
    student_uid = data.get("student_uid")

    if not faculty_uid or not student_uid:
        return jsonify({"error": "faculty_uid and student_uid required"}), 400

    # Verify both exist
    faculty = get_user_doc(faculty_uid)
    student = get_user_doc(student_uid)

    if not faculty or faculty.get("role") != "faculty":
        return jsonify({"error": "Invalid faculty UID"}), 404
    if not student or student.get("role") != "student":
        return jsonify({"error": "Invalid student UID"}), 404

    # Update student's mentor
    update_document("users", student_uid, {"mentor_id": faculty_uid})

    # Create assignment record
    assignment_id = add_document("mentor_assignments", {
        "hod_uid": uid,
        "faculty_uid": faculty_uid,
        "student_uid": student_uid,
        "department": student.get("department", ""),
    })

    log_analytics_event("mentor_assigned", uid, metadata={
        "faculty_uid": faculty_uid,
        "student_uid": student_uid,
    })

    return jsonify({
        "message": "Mentor assigned",
        "assignment_id": assignment_id,
    }), 201


@hod_bp.route("/faculty/<faculty_uid>/score", methods=["PUT"])
@require_auth
@require_role("hod")
def score_faculty(faculty_uid):
    """Score a faculty member."""
    uid = get_current_uid()
    faculty = get_user_doc(faculty_uid)

    if not faculty or faculty.get("role") != "faculty":
        return jsonify({"error": "Faculty not found"}), 404

    data = request.get_json()
    score = data.get("score")
    feedback = data.get("feedback", "")

    if score is None or not isinstance(score, (int, float)) or score < 0 or score > 10:
        return jsonify({"error": "score must be a number 0-10"}), 400

    # Store score as a document
    score_id = add_document("faculty_scores", {
        "hod_uid": uid,
        "faculty_uid": faculty_uid,
        "score": score,
        "feedback": feedback,
    })

    log_analytics_event("faculty_scored", uid, metadata={"faculty_uid": faculty_uid})

    return jsonify({"message": "Faculty scored", "score_id": score_id}), 201


@hod_bp.route("/repositories", methods=["GET"])
@require_auth
@require_role("hod")
def list_all_repos():
    """List all repositories (HOD can see everything)."""
    dept = request.args.get("department", "")

    # Get all repos
    repos = query_collection("repositories", limit=500)

    # Optionally filter by department (via user lookup)
    if dept:
        dept_users = query_collection("users", filters=[("department", "==", dept)], limit=500)
        dept_uids = {u.get("uid") or u.get("id") for u in dept_users}
        repos = [r for r in repos if r.get("owner_uid") in dept_uids]

    return jsonify({"repositories": repos}), 200


@hod_bp.route("/analytics", methods=["GET"])
@require_auth
@require_role("hod")
def department_analytics():
    """Get department-wide analytics."""
    dept = request.args.get("department", "")

    # Count users by role
    students = query_collection("users", filters=[("role", "==", "student")], limit=500)
    faculty = query_collection("users", filters=[("role", "==", "faculty")], limit=500)

    if dept:
        students = [s for s in students if s.get("department") == dept]
        faculty = [f for f in faculty if f.get("department") == dept]

    all_repos = query_collection("repositories", limit=1000)
    all_user_uids = {s.get("uid") or s.get("id") for s in students + faculty}
    dept_repos = [r for r in all_repos if r.get("owner_uid") in all_user_uids] if dept else all_repos

    stats = {
        "total_students": len(students),
        "total_faculty": len(faculty),
        "total_repos": len(dept_repos),
        "analyzed_repos": len([r for r in dept_repos if r.get("status") == "completed"]),
        "total_security_issues": sum(
            r.get("security_scan", {}).get("total_issues", 0) for r in dept_repos
        ),
    }

    return jsonify(stats), 200
