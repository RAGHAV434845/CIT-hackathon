"""Auth routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, get_current_user, get_current_uid
from services.firebase_service import (
    create_user_doc, get_user_doc, update_user_doc, verify_firebase_token
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user after Firebase Auth signup."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    required = ["uid", "username", "email", "role"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"Missing field: {field}"}), 400

    role = data["role"]
    if role not in ("student", "faculty", "hod"):
        return jsonify({"error": "Invalid role. Must be: student, faculty, hod"}), 400

    # Check if user already exists — allow re-registration (upsert)
    existing = get_user_doc(data["uid"])
    if existing:
        # Update existing doc with new info if it was a stub
        update_user_doc(data["uid"], user_data)
        return jsonify({"message": "User profile updated", "uid": data["uid"]}), 200

    user_data = {
        "username": data["username"],
        "email": data["email"],
        "role": role,
        "github_link": data.get("github_link", ""),
        "department": data.get("department", ""),
        "mentor_id": None,
    }

    success = create_user_doc(data["uid"], user_data)
    if success:
        return jsonify({"message": "User registered successfully", "uid": data["uid"]}), 201
    return jsonify({"error": "Failed to create user"}), 500


@auth_bp.route("/profile", methods=["GET"])
@require_auth
def get_profile():
    """Get current user profile."""
    user = get_current_user()
    return jsonify(user), 200


@auth_bp.route("/profile", methods=["PUT"])
@require_auth
def update_profile():
    """Update user profile."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Request body required"}), 400

    # Only allow updating these fields
    allowed = {"username", "github_link", "department"}
    update_data = {k: v for k, v in data.items() if k in allowed}

    if not update_data:
        return jsonify({"error": "No valid fields to update"}), 400

    uid = get_current_uid()
    success = update_user_doc(uid, update_data)
    if success:
        return jsonify({"message": "Profile updated"}), 200
    return jsonify({"error": "Update failed"}), 500
