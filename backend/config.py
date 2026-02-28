import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # Firebase
    FIREBASE_CREDENTIALS_PATH = os.getenv(
        "FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json"
    )
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")

    # File storage
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.getcwd(), "temp_repos"))
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max upload

    # Analysis
    ANALYSIS_TIMEOUT = 120  # 2 minutes max
    SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "java", "go", "ruby"]

    # AI / Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")

    # Rate limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002").split(",")
