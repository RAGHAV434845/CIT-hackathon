import os
import logging
from flask import Flask
from flask_cors import CORS
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # CORS
    CORS(app, origins=config_class.CORS_ORIGINS, supports_credentials=True)

    # Ensure temp directory exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "temp_repos"), exist_ok=True)

    # Initialize Firebase
    from services.firebase_service import init_firebase
    init_firebase(app)

    # Register blueprints
    from routes.auth_routes import auth_bp
    from routes.repo_routes import repo_bp
    from routes.analysis_routes import analysis_bp
    from routes.security_routes import security_bp
    from routes.docs_routes import docs_bp
    from routes.diagram_routes import diagram_bp
    from routes.chat_routes import chat_bp
    from routes.analytics_routes import analytics_bp
    from routes.faculty_routes import faculty_bp
    from routes.hod_routes import hod_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(repo_bp, url_prefix="/api/repos")
    app.register_blueprint(analysis_bp, url_prefix="/api/analysis")
    app.register_blueprint(security_bp, url_prefix="/api/security")
    app.register_blueprint(docs_bp, url_prefix="/api/docs")
    app.register_blueprint(diagram_bp, url_prefix="/api/diagrams")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(faculty_bp, url_prefix="/api/faculty")
    app.register_blueprint(hod_bp, url_prefix="/api/hod")

    # Health check
    @app.route("/api/health")
    def health():
        return {"status": "healthy", "version": "1.0.0"}

    logger.info("Application initialized successfully")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
