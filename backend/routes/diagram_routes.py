"""Diagram generation routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, get_current_uid
from services.repo_service import get_repo
from services.firebase_service import (
    add_document, get_document, update_document,
    query_collection, log_analytics_event
)
from engine.diagram_generator import DiagramGenerator

diagram_bp = Blueprint("diagrams", __name__)


@diagram_bp.route("/<repo_id>", methods=["POST"])
@require_auth
def generate_diagrams(repo_id):
    """Generate all diagrams for a repository."""
    uid = get_current_uid()
    repo = get_repo(repo_id)

    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    analysis = repo.get("analysis_result")
    if not analysis:
        return jsonify({"error": "Run analysis first"}), 400

    data = request.get_json() or {}
    diagram_type = data.get("type", "all")  # architecture, flow, dependency, all

    generator = DiagramGenerator(analysis)

    if diagram_type == "all":
        diagrams = generator.generate_all()
        results = []
        for dtype, ddata in diagrams.items():
            doc_id = add_document("diagrams", {
                "repo_id": repo_id,
                "owner_uid": uid,
                "type": ddata["type"],
                "mermaid_code": ddata["mermaid_code"],
                "custom_positions": {},
            })
            results.append({"diagram_id": doc_id, **ddata})

        log_analytics_event("diagram", uid, repo_id, {"type": "all"})
        return jsonify({"diagrams": results}), 201

    # Single diagram type
    if diagram_type == "architecture":
        code = generator.generate_architecture_diagram()
    elif diagram_type == "flow":
        code = generator.generate_flow_diagram()
    elif diagram_type == "dependency":
        code = generator.generate_dependency_graph()
    else:
        return jsonify({"error": "type must be: architecture, flow, dependency, all"}), 400

    doc_id = add_document("diagrams", {
        "repo_id": repo_id,
        "owner_uid": uid,
        "type": diagram_type,
        "mermaid_code": code,
        "custom_positions": {},
    })

    log_analytics_event("diagram", uid, repo_id, {"type": diagram_type})

    return jsonify({
        "diagram_id": doc_id,
        "type": diagram_type,
        "mermaid_code": code,
    }), 201


@diagram_bp.route("/<repo_id>", methods=["GET"])
@require_auth
def list_diagrams(repo_id):
    """List diagrams for a repository."""
    diagrams = query_collection(
        "diagrams",
        filters=[("repo_id", "==", repo_id)],
        limit=20,
    )
    return jsonify({"diagrams": diagrams}), 200


@diagram_bp.route("/<diagram_id>/edit", methods=["PUT"])
@require_auth
def update_diagram(diagram_id):
    """Update diagram (mermaid code or positions)."""
    uid = get_current_uid()
    doc = get_document("diagrams", diagram_id)

    if not doc:
        return jsonify({"error": "Diagram not found"}), 404
    if doc.get("owner_uid") != uid:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    update = {}
    if "mermaid_code" in data:
        update["mermaid_code"] = data["mermaid_code"]
    if "custom_positions" in data:
        update["custom_positions"] = data["custom_positions"]

    if update:
        update_document("diagrams", diagram_id, update)
        return jsonify({"message": "Diagram updated"}), 200

    return jsonify({"error": "Nothing to update"}), 400
