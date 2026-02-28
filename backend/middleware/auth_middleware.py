"""Authentication middleware and decorators."""

from functools import wraps
from flask import request, jsonify, g
from services.firebase_service import verify_firebase_token, get_user_doc
import logging

logger = logging.getLogger(__name__)


def require_auth(f):
    """Decorator: require valid Firebase ID token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split("Bearer ")[1]
        decoded = verify_firebase_token(token)
        if not decoded:
            return jsonify({"error": "Invalid or expired token"}), 401

        uid = decoded.get("uid")
        user = get_user_doc(uid)
        if not user:
            # User exists in Firebase Auth but not Firestore yet — allow through with minimal info
            user = {"uid": uid, "email": decoded.get("email", ""), "role": "student", "_stub": True}

        g.user = user
        g.uid = uid
        return f(*args, **kwargs)

    return decorated


def require_role(*roles):
    """Decorator: require specific role(s). Must be used after @require_auth."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = getattr(g, "user", None)
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            if user.get("role") not in roles:
                return jsonify({
                    "error": f"Access denied. Required role: {', '.join(roles)}"
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user():
    """Get current authenticated user from request context."""
    return getattr(g, "user", None)


def get_current_uid():
    """Get current user's UID."""
    return getattr(g, "uid", None)
