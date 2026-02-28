"""Chatbot routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, get_current_uid
from services.repo_service import get_repo
from services.chatbot_service import ChatbotService
from services.firebase_service import log_analytics_event

chat_bp = Blueprint("chat", __name__)

# Cache chatbot instances per repo
_chatbot_cache = {}


@chat_bp.route("/<repo_id>", methods=["POST"])
@require_auth
def chat_with_repo(repo_id):
    """Send a message to the chatbot about a repository."""
    uid = get_current_uid()
    repo = get_repo(repo_id)

    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    analysis = repo.get("analysis_result")
    if not analysis:
        return jsonify({"error": "Run analysis first before chatting"}), 400

    data = request.get_json()
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "message field required"}), 400

    # Get or create chatbot instance
    if repo_id not in _chatbot_cache:
        _chatbot_cache[repo_id] = ChatbotService(analysis, repo.get("name", "Project"))

    chatbot = _chatbot_cache[repo_id]
    response = chatbot.chat(message)

    log_analytics_event("chat", uid, repo_id, {"message_length": len(message)})

    return jsonify({
        "response": response,
        "repo_id": repo_id,
    }), 200
