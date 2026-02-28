"""
Repository management service.
Handles: create, upload ZIP, clone from GitHub, search, list.
"""

import os
import shutil
import zipfile
import tempfile
import logging
import subprocess
from typing import Optional
from services.firebase_service import (
    add_document, get_document, update_document,
    delete_document, query_collection, log_analytics_event
)

logger = logging.getLogger(__name__)


def get_upload_dir():
    """Get upload directory path."""
    upload_dir = os.environ.get("UPLOAD_FOLDER", os.path.join(os.getcwd(), "temp_repos"))
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


def create_repo_record(owner_uid: str, name: str, source: str,
                       github_url: Optional[str] = None) -> Optional[str]:
    """Create a repository record in Firestore."""
    data = {
        "owner_uid": owner_uid,
        "name": name,
        "source": source,
        "github_url": github_url,
        "status": "pending",
        "analysis_result": None,
        "security_scan": None,
    }
    repo_id = add_document("repositories", data)
    if repo_id:
        log_analytics_event("repo_created", owner_uid, repo_id, {"source": source})
    return repo_id


def clone_github_repo(github_url: str, repo_id: str) -> Optional[str]:
    """Clone a GitHub repository. Returns local path or None."""
    upload_dir = get_upload_dir()
    dest = os.path.join(upload_dir, repo_id)

    try:
        # Basic URL validation
        if not github_url.startswith(("https://github.com/", "http://github.com/",
                                       "https://gitlab.com/")):
            logger.error(f"Invalid GitHub URL: {github_url}")
            return None

        # Clone (shallow for speed)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", github_url, dest],
            capture_output=True, text=True, timeout=120
        )

        if result.returncode != 0:
            logger.error(f"Git clone failed: {result.stderr}")
            return None

        logger.info(f"Cloned {github_url} to {dest}")
        return dest

    except subprocess.TimeoutExpired:
        logger.error(f"Git clone timeout for {github_url}")
        shutil.rmtree(dest, ignore_errors=True)
        return None
    except Exception as e:
        logger.error(f"Git clone error: {e}")
        shutil.rmtree(dest, ignore_errors=True)
        return None


def handle_zip_upload(file_storage, repo_id: str) -> Optional[str]:
    """Extract uploaded ZIP file. Returns local path or None."""
    upload_dir = get_upload_dir()
    dest = os.path.join(upload_dir, repo_id)

    try:
        # Save ZIP to temp
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            file_storage.save(tmp.name)
            tmp_path = tmp.name

        # Extract
        os.makedirs(dest, exist_ok=True)
        with zipfile.ZipFile(tmp_path, "r") as zf:
            # Security: check for path traversal
            for member in zf.namelist():
                if member.startswith("/") or ".." in member:
                    logger.error(f"Dangerous path in ZIP: {member}")
                    shutil.rmtree(dest, ignore_errors=True)
                    return None
            zf.extractall(dest)

        # Remove temp ZIP
        os.unlink(tmp_path)

        # If ZIP contained a single root folder, use that
        contents = os.listdir(dest)
        if len(contents) == 1 and os.path.isdir(os.path.join(dest, contents[0])):
            inner = os.path.join(dest, contents[0])
            # Move contents up
            for item in os.listdir(inner):
                shutil.move(os.path.join(inner, item), os.path.join(dest, item))
            os.rmdir(inner)

        logger.info(f"Extracted ZIP to {dest}")
        return dest

    except zipfile.BadZipFile:
        logger.error("Invalid ZIP file")
        return None
    except Exception as e:
        logger.error(f"ZIP extraction error: {e}")
        shutil.rmtree(dest, ignore_errors=True)
        return None


def get_repo_path(repo_id: str) -> Optional[str]:
    """Get local path for a repository."""
    upload_dir = get_upload_dir()
    path = os.path.join(upload_dir, repo_id)
    if os.path.isdir(path):
        return path
    return None


def cleanup_repo(repo_id: str):
    """Delete local repository files."""
    path = get_repo_path(repo_id)
    if path:
        shutil.rmtree(path, ignore_errors=True)
        logger.info(f"Cleaned up repo {repo_id}")


def list_user_repos(owner_uid: str):
    """List repositories owned by a user."""
    return query_collection(
        "repositories",
        filters=[("owner_uid", "==", owner_uid)],
        order_by=None,
        limit=100,
    )


def get_repo(repo_id: str):
    """Get repository record."""
    return get_document("repositories", repo_id)


def delete_repo(repo_id: str, owner_uid: str) -> bool:
    """Delete repository record and files."""
    repo = get_repo(repo_id)
    if not repo or repo.get("owner_uid") != owner_uid:
        return False
    cleanup_repo(repo_id)
    delete_document("repositories", repo_id)
    log_analytics_event("repo_deleted", owner_uid, repo_id)
    return True
