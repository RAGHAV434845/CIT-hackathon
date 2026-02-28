"""
Security Scanner
=================
Regex-based detection of:
- API keys, tokens, secrets, passwords
- AWS keys, GCP keys
- Database connection strings
- Private keys

Reports file + line number.
Supports auto-remove, manual-remove, ignore, mask.
"""

import re
import os
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Secret detection patterns: (name, regex, severity)
# ---------------------------------------------------------------------------
SECRET_PATTERNS = [
    # Generic API keys
    ("Generic API Key",
     r"""(?i)(?:api[_-]?key|apikey)\s*[:=]\s*['"]([A-Za-z0-9_\-]{20,})['"]""",
     "high"),

    # Generic Secret / Token
    ("Generic Secret",
     r"""(?i)(?:secret|token|auth[_-]?token|access[_-]?token|bearer)\s*[:=]\s*['"]([A-Za-z0-9_\-/.+=]{20,})['"]""",
     "high"),

    # Passwords
    ("Password",
     r"""(?i)(?:password|passwd|pwd|pass)\s*[:=]\s*['"]([^'"]{6,})['"]""",
     "high"),

    # AWS Access Key ID
    ("AWS Access Key",
     r"""(?:AKIA|ABIA|ACCA|ASIA)[A-Z0-9]{16}""",
     "critical"),

    # AWS Secret Key
    ("AWS Secret Key",
     r"""(?i)aws[_-]?secret[_-]?access[_-]?key\s*[:=]\s*['"]([A-Za-z0-9/+=]{40})['"]""",
     "critical"),

    # Google API Key
    ("Google API Key",
     r"""AIza[A-Za-z0-9_\-]{35}""",
     "high"),

    # Firebase Config
    ("Firebase Config",
     r"""(?i)firebase[_-]?(?:api[_-]?key|auth[_-]?domain|project[_-]?id|storage[_-]?bucket)\s*[:=]\s*['"]([^'"]+)['"]""",
     "medium"),

    # Private Key (PEM)
    ("Private Key",
     r"""-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----""",
     "critical"),

    # GitHub Token
    ("GitHub Token",
     r"""(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}""",
     "critical"),

    # Slack Token
    ("Slack Token",
     r"""xox[bpors]-[A-Za-z0-9\-]{10,}""",
     "high"),

    # Stripe Key
    ("Stripe Key",
     r"""(?:sk|pk)_(?:test|live)_[A-Za-z0-9]{20,}""",
     "critical"),

    # Database Connection String
    ("Database URL",
     r"""(?i)(?:postgres|mysql|mongodb|redis)://[^\s'"]+""",
     "high"),

    # JWT Token (hardcoded)
    ("Hardcoded JWT",
     r"""eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_\-+/=]{10,}""",
     "high"),

    # SendGrid API Key
    ("SendGrid Key",
     r"""SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43}""",
     "high"),

    # Twilio
    ("Twilio Key",
     r"""SK[a-f0-9]{32}""",
     "medium"),

    # Heroku API Key
    ("Heroku API Key",
     r"""(?i)heroku[_-]?api[_-]?key\s*[:=]\s*['"]([A-Za-z0-9\-]{36,})['"]""",
     "high"),

    # .env-style secrets
    ("ENV Secret Assignment",
     r"""(?i)^(?:export\s+)?(?:SECRET|TOKEN|API_KEY|PRIVATE_KEY|DB_PASS|DATABASE_URL)\s*=\s*['"]?([^\s'"#]+)""",
     "high"),
]

# Files to always scan
PRIORITY_FILES = [".env", ".env.local", ".env.production", ".env.development"]

# Files to skip
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".zip", ".tar", ".gz", ".rar",
    ".pdf", ".doc", ".docx",
    ".lock", ".map",
}

SKIP_DIRS = {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}


class SecurityScanner:
    """Scan codebase for secrets and sensitive data."""

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self.issues: List[Dict] = []

    def scan(self) -> List[Dict]:
        """Run full security scan. Returns list of issues."""
        self.issues = []

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext in SKIP_EXTENSIONS:
                    continue

                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, self.repo_path).replace("\\", "/")

                # Skip large files
                try:
                    if os.path.getsize(abs_path) > 512 * 1024:  # 512KB
                        continue
                except OSError:
                    continue

                try:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                except Exception:
                    continue

                self._scan_file(rel_path, lines)

        # Sort: critical first, then high, medium, low
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.issues.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))

        logger.info(f"Security scan found {len(self.issues)} issues in {self.repo_path}")
        return self.issues

    def _scan_file(self, rel_path: str, lines: List[str]):
        """Scan a single file for secrets."""
        for line_num, line in enumerate(lines, 1):
            # Skip comments (basic heuristic)
            stripped = line.strip()
            if stripped.startswith(("#", "//", "<!--", "/*", "*")):
                # Still scan .env files even with comments
                if not rel_path.startswith(".env"):
                    continue

            for name, pattern, severity in SECRET_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    # Get the matched secret value (mask it)
                    secret_val = match.group(0)
                    masked = self._mask_secret(secret_val)

                    self.issues.append({
                        "type": name,
                        "file": rel_path,
                        "line": line_num,
                        "severity": severity,
                        "status": "detected",
                        "snippet": masked,
                        "original_line": line.rstrip(),
                    })
                    break  # One issue per line

    @staticmethod
    def _mask_secret(value: str, visible_chars: int = 4) -> str:
        """Mask a secret value, showing only first few chars."""
        if len(value) <= visible_chars + 4:
            return "*" * len(value)
        return value[:visible_chars] + "*" * (len(value) - visible_chars)


def auto_remove_secrets(repo_path: str, issues: List[Dict]) -> int:
    """Auto-remove detected secrets from files. Returns count of removals."""
    removed = 0
    files_modified = {}

    for issue in issues:
        if issue.get("status") != "detected":
            continue

        file_path = os.path.join(repo_path, issue["file"])
        if file_path not in files_modified:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    files_modified[file_path] = f.readlines()
            except Exception:
                continue

        lines = files_modified[file_path]
        line_idx = issue["line"] - 1

        if 0 <= line_idx < len(lines):
            original = lines[line_idx]
            # Replace the secret with placeholder
            for _, pattern, _ in SECRET_PATTERNS:
                replaced = re.sub(pattern, lambda m: '"REMOVED_SECRET"', original)
                if replaced != original:
                    lines[line_idx] = replaced
                    issue["status"] = "removed"
                    removed += 1
                    break

    # Write modified files
    for file_path, lines in files_modified.items():
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception as e:
            logger.error(f"Failed to write {file_path}: {e}")

    return removed


def mask_secrets_in_content(content: str) -> str:
    """Mask any secrets found in content string (for safe processing)."""
    for name, pattern, severity in SECRET_PATTERNS:
        content = re.sub(
            pattern,
            lambda m: m.group(0)[:4] + "*" * max(0, len(m.group(0)) - 4),
            content,
        )
    return content
