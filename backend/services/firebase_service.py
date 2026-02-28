"""Firebase initialization and Firestore helpers."""

import firebase_admin
from firebase_admin import credentials, firestore, auth as firebase_auth
import logging
import os

logger = logging.getLogger(__name__)

db = None


def init_firebase(app):
    """Initialize Firebase Admin SDK."""
    global db
    cred_path = app.config.get("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")

    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized with credentials file")
    else:
        # Use default credentials (for Cloud Run / GCE)
        try:
            firebase_admin.initialize_app()
            logger.info("Firebase initialized with default credentials")
        except Exception:
            logger.warning(
                "Firebase credentials not found. Running in mock mode. "
                "Place firebase-credentials.json in backend/ for full functionality."
            )
            return

    db = firestore.client()
    logger.info("Firestore client initialized")


def get_db():
    """Get Firestore client."""
    global db
    if db is None:
        try:
            db = firestore.client()
        except Exception:
            logger.error("Firestore not initialized")
            return None
    return db


def verify_firebase_token(id_token):
    """Verify Firebase ID token and return decoded claims."""
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None


def get_user_doc(uid):
    """Get user document from Firestore."""
    db = get_db()
    if not db:
        return None
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        data = doc.to_dict()
        data["uid"] = uid
        return data
    return None


def create_user_doc(uid, data):
    """Create user document in Firestore."""
    db = get_db()
    if not db:
        return False
    from datetime import datetime
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()
    db.collection("users").document(uid).set(data)
    return True


def update_user_doc(uid, data):
    """Update user document in Firestore."""
    db = get_db()
    if not db:
        return False
    from datetime import datetime
    data["updated_at"] = datetime.utcnow()
    db.collection("users").document(uid).update(data)
    return True


def add_document(collection, data):
    """Add document to collection, return doc ID."""
    db = get_db()
    if not db:
        return None
    from datetime import datetime
    data["created_at"] = datetime.utcnow()
    _, doc_ref = db.collection(collection).add(data)
    return doc_ref.id


def get_document(collection, doc_id):
    """Get single document."""
    db = get_db()
    if not db:
        return None
    doc = db.collection(collection).document(doc_id).get()
    if doc.exists:
        data = doc.to_dict()
        data["id"] = doc.id
        return data
    return None


def update_document(collection, doc_id, data):
    """Update document."""
    db = get_db()
    if not db:
        return False
    from datetime import datetime
    data["updated_at"] = datetime.utcnow()
    db.collection(collection).document(doc_id).update(data)
    return True


def delete_document(collection, doc_id):
    """Delete document."""
    db = get_db()
    if not db:
        return False
    db.collection(collection).document(doc_id).delete()
    return True


def query_collection(collection, filters=None, order_by=None, limit=50):
    """Query collection with optional filters."""
    db = get_db()
    if not db:
        return []
    ref = db.collection(collection)
    if filters:
        for field, op, value in filters:
            ref = ref.where(field, op, value)
    if order_by:
        ref = ref.order_by(order_by)
    if limit:
        ref = ref.limit(limit)
    docs = ref.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        results.append(data)
    return results


def log_analytics_event(event_type, user_uid, repo_id=None, metadata=None):
    """Log an analytics event."""
    add_document("analytics", {
        "event_type": event_type,
        "user_uid": user_uid,
        "repo_id": repo_id,
        "metadata": metadata or {},
    })
