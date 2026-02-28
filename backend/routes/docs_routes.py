"""Documentation generation routes."""

from flask import Blueprint, request, jsonify
from middleware.auth_middleware import require_auth, get_current_uid
from services.repo_service import get_repo
from services.firebase_service import (
    add_document, get_document, update_document,
    query_collection, log_analytics_event
)
from engine.doc_generator import ReadmeGenerator, DocGenerator

docs_bp = Blueprint("docs", __name__)


@docs_bp.route("/<repo_id>/readme", methods=["POST"])
@require_auth
def generate_readme(repo_id):
    """Generate README for a repository."""
    uid = get_current_uid()
    repo = get_repo(repo_id)

    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    analysis = repo.get("analysis_result")
    if not analysis:
        return jsonify({"error": "Run analysis first"}), 400

    generator = ReadmeGenerator(analysis, repo.get("name", "Project"))
    content = generator.generate()

    doc_id = add_document("documents", {
        "repo_id": repo_id,
        "owner_uid": uid,
        "type": "readme",
        "content": content,
        "format": "markdown",
    })

    log_analytics_event("document", uid, repo_id, {"type": "readme"})

    return jsonify({"doc_id": doc_id, "content": content, "type": "readme"}), 201


@docs_bp.route("/<repo_id>/api-doc", methods=["POST"])
@require_auth
def generate_api_doc(repo_id):
    """Generate API documentation."""
    uid = get_current_uid()
    repo = get_repo(repo_id)

    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    analysis = repo.get("analysis_result")
    if not analysis:
        return jsonify({"error": "Run analysis first"}), 400

    generator = DocGenerator(analysis, repo.get("name", "Project"))
    content = generator.generate_api_doc()

    doc_id = add_document("documents", {
        "repo_id": repo_id,
        "owner_uid": uid,
        "type": "api_doc",
        "content": content,
        "format": "markdown",
    })

    log_analytics_event("document", uid, repo_id, {"type": "api_doc"})

    return jsonify({"doc_id": doc_id, "content": content, "type": "api_doc"}), 201


@docs_bp.route("/<repo_id>/report", methods=["POST"])
@require_auth
def generate_report(repo_id):
    """Generate technical report."""
    uid = get_current_uid()
    repo = get_repo(repo_id)

    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    analysis = repo.get("analysis_result")
    if not analysis:
        return jsonify({"error": "Run analysis first"}), 400

    generator = DocGenerator(analysis, repo.get("name", "Project"))
    content = generator.generate_tech_report()

    doc_id = add_document("documents", {
        "repo_id": repo_id,
        "owner_uid": uid,
        "type": "tech_report",
        "content": content,
        "format": "markdown",
    })

    log_analytics_event("document", uid, repo_id, {"type": "tech_report"})

    return jsonify({"doc_id": doc_id, "content": content, "type": "tech_report"}), 201


@docs_bp.route("/<repo_id>/module-breakdown", methods=["POST"])
@require_auth
def generate_module_breakdown(repo_id):
    """Generate module breakdown."""
    uid = get_current_uid()
    repo = get_repo(repo_id)

    if not repo:
        return jsonify({"error": "Repository not found"}), 404

    analysis = repo.get("analysis_result")
    if not analysis:
        return jsonify({"error": "Run analysis first"}), 400

    generator = DocGenerator(analysis, repo.get("name", "Project"))
    content = generator.generate_module_breakdown()

    doc_id = add_document("documents", {
        "repo_id": repo_id,
        "owner_uid": uid,
        "type": "module_breakdown",
        "content": content,
        "format": "markdown",
    })

    return jsonify({"doc_id": doc_id, "content": content, "type": "module_breakdown"}), 201


@docs_bp.route("/<repo_id>", methods=["GET"])
@require_auth
def list_docs(repo_id):
    """List documents for a repository."""
    docs = query_collection(
        "documents",
        filters=[("repo_id", "==", repo_id)],
        limit=50,
    )
    return jsonify({"documents": docs}), 200


@docs_bp.route("/<doc_id>/edit", methods=["PUT"])
@require_auth
def edit_doc(doc_id):
    """Edit a document's content."""
    uid = get_current_uid()
    doc = get_document("documents", doc_id)

    if not doc:
        return jsonify({"error": "Document not found"}), 404
    if doc.get("owner_uid") != uid:
        return jsonify({"error": "Access denied"}), 403

    data = request.get_json()
    content = data.get("content")
    if content is None:
        return jsonify({"error": "content field required"}), 400

    update_document("documents", doc_id, {"content": content})
    return jsonify({"message": "Document updated"}), 200


@docs_bp.route("/<doc_id>/export/<fmt>", methods=["GET"])
@require_auth
def export_doc(doc_id, fmt):
    """Export document in specified format."""
    doc = get_document("documents", doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    content = doc.get("content", "")

    if fmt == "markdown" or fmt == "md":
        return content, 200, {"Content-Type": "text/markdown"}

    elif fmt == "pdf":
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.set_font("Helvetica", size=10)

            for line in content.split("\n"):
                # Basic markdown → text conversion
                line = line.replace("#", "").strip()
                if line.startswith("**") and line.endswith("**"):
                    pdf.set_font("Helvetica", "B", 11)
                    line = line[2:-2]
                elif line.startswith("# "):
                    pdf.set_font("Helvetica", "B", 16)
                    line = line[2:]
                elif line.startswith("## "):
                    pdf.set_font("Helvetica", "B", 14)
                    line = line[3:]
                else:
                    pdf.set_font("Helvetica", size=10)

                pdf.multi_cell(0, 5, line)

            pdf_bytes = pdf.output()
            return pdf_bytes, 200, {
                "Content-Type": "application/pdf",
                "Content-Disposition": f"attachment; filename=document.pdf",
            }
        except Exception as e:
            return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500

    return jsonify({"error": "Format must be: markdown, md, pdf"}), 400
