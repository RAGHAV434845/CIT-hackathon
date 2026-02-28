"""
Static Code Analysis Engine
============================
Rule-based analysis using:
- AST parsing (Python)
- Regex scanning
- Dependency file analysis
- Import graph detection
- Folder heuristic classification

NO ML TRAINING. Deterministic analysis only.
"""

import os
import ast
import re
import json
import logging
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# File extension → language mapping
# ---------------------------------------------------------------------------
LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".cpp": "cpp",
    ".c": "c",
    ".rs": "rust",
    ".swift": "swift",
    ".kt": "kotlin",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
    ".sh": "shell",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".xml": "xml",
    ".md": "markdown",
    ".txt": "text",
}

# Directories to always skip
SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
    ".next", ".nuxt", "vendor", "target", ".idea", ".vscode",
    "coverage", ".cache", "egg-info",
}

SKIP_FILES = {
    ".DS_Store", "Thumbs.db", ".gitignore", ".gitattributes",
    "package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock",
}

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB per file


class CodebaseAnalyzer:
    """Main analysis orchestrator."""

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
        self.files = []          # list of relative paths
        self.file_contents = {}  # rel_path → content
        self.languages = defaultdict(int)  # language → line count
        self.total_files = 0
        self.total_lines = 0

    # ------------------------------------------------------------------
    # 1. Scan file tree
    # ------------------------------------------------------------------
    def scan_files(self):
        """Walk directory tree, catalogue files, read contents."""
        for root, dirs, filenames in os.walk(self.repo_path):
            # Prune skip dirs in-place
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for fname in filenames:
                if fname in SKIP_FILES:
                    continue
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, self.repo_path).replace("\\", "/")

                # Skip large files
                try:
                    size = os.path.getsize(abs_path)
                    if size > MAX_FILE_SIZE:
                        continue
                except OSError:
                    continue

                ext = os.path.splitext(fname)[1].lower()
                lang = LANGUAGE_MAP.get(ext)

                self.files.append(rel_path)
                self.total_files += 1

                # Read text files
                if lang and lang not in ("json", "xml", "markdown", "text"):
                    try:
                        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        self.file_contents[rel_path] = content
                        line_count = content.count("\n") + 1
                        self.languages[lang] += line_count
                        self.total_lines += line_count
                    except Exception:
                        pass
                elif lang:
                    # Still count these
                    try:
                        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        self.file_contents[rel_path] = content
                        self.total_lines += content.count("\n") + 1
                    except Exception:
                        pass

        logger.info(
            f"Scanned {self.total_files} files, {self.total_lines} lines in {self.repo_path}"
        )

    # ------------------------------------------------------------------
    # 2. Full analysis pipeline
    # ------------------------------------------------------------------
    def analyze(self) -> dict:
        """Run complete analysis pipeline. Returns structured result."""
        self.scan_files()

        framework = detect_framework(self.repo_path, self.file_contents, self.files)
        tech_stack = detect_tech_stack(self.repo_path, self.file_contents, self.files)
        entry_points = detect_entry_points(self.repo_path, self.file_contents, self.files)
        architecture = classify_architecture(self.files, self.file_contents)
        components = detect_components(self.files, self.file_contents)
        db_usage = detect_database_usage(self.file_contents)
        api_endpoints = detect_api_endpoints(self.file_contents)
        dependency_graph = build_import_graph(self.file_contents)
        folder_structure = build_folder_tree(self.files)

        return {
            "framework": framework,
            "tech_stack": tech_stack,
            "entry_points": entry_points,
            "architecture_type": architecture,
            "components": components,
            "database_usage": db_usage,
            "api_endpoints": api_endpoints,
            "dependency_graph": dependency_graph,
            "folder_structure": folder_structure,
            "languages": dict(self.languages),
            "total_files": self.total_files,
            "total_lines": self.total_lines,
            "files": self.files[:500],  # cap for storage
        }


# ======================================================================
# FRAMEWORK DETECTION — rule-based, dependency + import + file scanning
# ======================================================================

# Mapping: (dependency_file_pattern, key) → framework name
FRAMEWORK_RULES = [
    # Python
    {"files": ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py"],
     "keywords": {"flask": "Flask", "django": "Django", "fastapi": "FastAPI",
                  "tornado": "Tornado", "bottle": "Bottle", "pyramid": "Pyramid",
                  "streamlit": "Streamlit", "gradio": "Gradio"}},
    # JavaScript / TypeScript
    {"files": ["package.json"],
     "keywords": {"react": "React", "next": "Next.js", "vue": "Vue.js",
                  "nuxt": "Nuxt.js", "angular": "Angular", "svelte": "Svelte",
                  "express": "Express.js", "nestjs": "NestJS", "koa": "Koa",
                  "fastify": "Fastify", "gatsby": "Gatsby", "remix": "Remix",
                  "electron": "Electron"}},
    # Java
    {"files": ["pom.xml", "build.gradle", "build.gradle.kts"],
     "keywords": {"spring": "Spring Boot", "quarkus": "Quarkus"}},
    # Ruby
    {"files": ["Gemfile"],
     "keywords": {"rails": "Ruby on Rails", "sinatra": "Sinatra"}},
    # Go
    {"files": ["go.mod"],
     "keywords": {"gin": "Gin", "echo": "Echo", "fiber": "Fiber"}},
    # PHP
    {"files": ["composer.json"],
     "keywords": {"laravel": "Laravel", "symfony": "Symfony"}},
]


def detect_framework(repo_path, file_contents, files):
    """Detect primary framework from dependency files and imports."""
    detected = []

    for rule in FRAMEWORK_RULES:
        for dep_file in rule["files"]:
            if dep_file in file_contents:
                content_lower = file_contents[dep_file].lower()
                for kw, name in rule["keywords"].items():
                    if kw in content_lower:
                        detected.append(name)

    # Also scan imports in code
    for path, content in file_contents.items():
        if path.endswith(".py"):
            for kw, name in FRAMEWORK_RULES[0]["keywords"].items():
                if re.search(rf"^\s*(import|from)\s+{kw}", content, re.MULTILINE):
                    if name not in detected:
                        detected.append(name)
        elif path.endswith((".js", ".jsx", ".ts", ".tsx")):
            for kw, name in FRAMEWORK_RULES[1]["keywords"].items():
                if re.search(
                    rf"""require\(['"]{kw}|from\s+['"]{kw}""", content
                ):
                    if name not in detected:
                        detected.append(name)

    return detected if detected else ["Unknown"]


# ======================================================================
# TECH STACK DETECTION
# ======================================================================

TECH_STACK_SIGNALS = {
    # Databases
    "mongodb": {"files": [], "keywords": ["pymongo", "mongoose", "mongodb", "mongoclient"]},
    "postgresql": {"files": [], "keywords": ["psycopg", "pg ", "postgresql", "postgres"]},
    "mysql": {"files": [], "keywords": ["mysql", "mysqlclient", "mysql2"]},
    "sqlite": {"files": [], "keywords": ["sqlite3", "sqlite"]},
    "redis": {"files": [], "keywords": ["redis", "ioredis"]},
    "firebase": {"files": [], "keywords": ["firebase", "firestore"]},
    "supabase": {"files": [], "keywords": ["supabase"]},

    # ORMs
    "sqlalchemy": {"files": [], "keywords": ["sqlalchemy"]},
    "prisma": {"files": ["prisma/schema.prisma"], "keywords": ["prisma"]},
    "sequelize": {"files": [], "keywords": ["sequelize"]},
    "typeorm": {"files": [], "keywords": ["typeorm"]},

    # Auth
    "jwt": {"files": [], "keywords": ["jsonwebtoken", "pyjwt", "jwt"]},
    "oauth": {"files": [], "keywords": ["oauth", "passport"]},

    # Cloud
    "aws": {"files": [], "keywords": ["boto3", "aws-sdk", "@aws-sdk"]},
    "gcp": {"files": [], "keywords": ["google-cloud", "@google-cloud"]},
    "docker": {"files": ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"], "keywords": []},

    # Testing
    "pytest": {"files": [], "keywords": ["pytest"]},
    "jest": {"files": [], "keywords": ["jest"]},
    "mocha": {"files": [], "keywords": ["mocha"]},

    # CSS
    "tailwindcss": {"files": ["tailwind.config.js", "tailwind.config.ts"], "keywords": ["tailwindcss"]},
    "bootstrap": {"files": [], "keywords": ["bootstrap"]},

    # Build tools
    "webpack": {"files": ["webpack.config.js"], "keywords": ["webpack"]},
    "vite": {"files": ["vite.config.js", "vite.config.ts"], "keywords": ["vite"]},
}


def detect_tech_stack(repo_path, file_contents, files):
    """Detect tech stack components."""
    detected = set()
    all_content = "\n".join(file_contents.values()).lower()

    for tech, signals in TECH_STACK_SIGNALS.items():
        # Check file existence
        for sig_file in signals.get("files", []):
            if sig_file in files:
                detected.add(tech)
                break

        # Check keywords in content
        for kw in signals.get("keywords", []):
            if kw in all_content:
                detected.add(tech)
                break

    return sorted(detected)


# ======================================================================
# ENTRY POINT DETECTION
# ======================================================================

ENTRY_POINT_PATTERNS = {
    "python": [
        (r'if\s+__name__\s*==\s*["\']__main__["\']', "main guard"),
        (r"app\.run\(", "Flask app.run()"),
        (r"uvicorn\.run\(", "Uvicorn run"),
        (r"manage\.py", "Django manage.py"),
    ],
    "javascript": [
        (r"app\.listen\(", "Express listen"),
        (r"createServer\(", "HTTP server"),
        (r"ReactDOM\.render\(|createRoot\(", "React entry"),
    ],
    "typescript": [
        (r"app\.listen\(", "Express listen"),
        (r"bootstrap\(\)", "NestJS bootstrap"),
    ],
}

ENTRY_POINT_FILES = [
    "main.py", "app.py", "run.py", "server.py", "wsgi.py", "asgi.py",
    "manage.py", "index.py",
    "index.js", "server.js", "app.js", "main.js",
    "index.ts", "server.ts", "app.ts", "main.ts",
    "index.tsx", "main.tsx", "App.tsx",
    "Main.java", "Application.java",
    "main.go", "cmd/main.go",
]


def detect_entry_points(repo_path, file_contents, files):
    """Find entry points in the codebase."""
    results = []

    # Check well-known entry point filenames
    for f in files:
        basename = os.path.basename(f)
        if basename in ENTRY_POINT_FILES:
            results.append({"file": f, "reason": f"Known entry point filename: {basename}"})

    # Pattern matching in file content
    for path, content in file_contents.items():
        ext = os.path.splitext(path)[1].lower()
        lang = LANGUAGE_MAP.get(ext)
        if lang and lang in ENTRY_POINT_PATTERNS:
            for pattern, reason in ENTRY_POINT_PATTERNS[lang]:
                if re.search(pattern, content):
                    entry = {"file": path, "reason": reason}
                    if entry not in results:
                        results.append(entry)

    return results


# ======================================================================
# ARCHITECTURE CLASSIFICATION (heuristic folder-based)
# ======================================================================

ARCHITECTURE_PATTERNS = {
    "MVC": {
        "required": ["model", "view", "controller"],
        "dirs": ["models", "views", "controllers", "templates"],
    },
    "MVVM": {
        "required": ["model", "view", "viewmodel"],
        "dirs": ["models", "views", "viewmodels"],
    },
    "Microservices": {
        "required": [],
        "dirs": ["services", "gateway", "api-gateway"],
        "files": ["docker-compose.yml", "docker-compose.yaml"],
    },
    "Layered / N-Tier": {
        "required": [],
        "dirs": ["controllers", "services", "repositories", "models"],
    },
    "Component-Based (React/Vue)": {
        "required": [],
        "dirs": ["components", "pages", "hooks", "store", "context"],
    },
    "Monolithic": {
        "required": [],
        "dirs": [],
    },
}


def classify_architecture(files, file_contents):
    """Classify architecture pattern from folder structure."""
    dir_names = set()
    for f in files:
        parts = f.split("/")
        for p in parts[:-1]:
            dir_names.add(p.lower())

    file_basenames = {os.path.basename(f) for f in files}

    for arch, pattern in ARCHITECTURE_PATTERNS.items():
        if arch == "Monolithic":
            continue
        required = pattern.get("required", [])
        dirs = pattern.get("dirs", [])
        indicator_files = pattern.get("files", [])

        dir_match = sum(1 for d in dirs if d in dir_names)
        file_match = sum(1 for f in indicator_files if f in file_basenames)

        if len(required) > 0 and all(r in dir_names for r in required):
            return arch
        if dir_match >= 3:
            return arch
        if dir_match >= 2 and file_match >= 1:
            return arch

    return "Monolithic"


# ======================================================================
# COMPONENT DETECTION (controllers, services, models, config)
# ======================================================================

COMPONENT_HEURISTICS = {
    "controllers": ["controller", "handler", "endpoint", "resource", "view"],
    "services": ["service", "manager", "helper", "util", "utils"],
    "models": ["model", "schema", "entity", "dto"],
    "routes": ["route", "router", "url", "urls"],
    "middleware": ["middleware", "interceptor", "guard"],
    "config": ["config", "settings", "env", "constant"],
    "tests": ["test", "spec", "__tests__"],
    "migrations": ["migration", "migrate"],
}


def detect_components(files, file_contents):
    """Classify files into architectural components."""
    components = defaultdict(list)

    for f in files:
        lower = f.lower()
        categorized = False
        for category, keywords in COMPONENT_HEURISTICS.items():
            for kw in keywords:
                if kw in lower:
                    components[category].append(f)
                    categorized = True
                    break
            if categorized:
                break
        if not categorized:
            components["other"].append(f)

    return {k: v[:50] for k, v in components.items()}  # cap per category


# ======================================================================
# DATABASE USAGE DETECTION
# ======================================================================

DB_PATTERNS = [
    (r"CREATE\s+TABLE", "SQL (CREATE TABLE)"),
    (r"SELECT\s+.+\s+FROM", "SQL (SELECT)"),
    (r"INSERT\s+INTO", "SQL (INSERT)"),
    (r"db\.collection\(", "Firestore / MongoDB"),
    (r"mongoose\.model\(", "MongoDB (Mongoose)"),
    (r"Model\.objects\.", "Django ORM"),
    (r"session\.query\(", "SQLAlchemy"),
    (r"prisma\.\w+\.", "Prisma ORM"),
    (r"sequelize\.define\(", "Sequelize"),
    (r"knex\(", "Knex.js"),
    (r"firebase.*firestore", "Firebase Firestore"),
    (r"dynamodb", "AWS DynamoDB"),
]


def detect_database_usage(file_contents):
    """Detect database usage patterns."""
    results = []
    seen = set()

    for path, content in file_contents.items():
        for pattern, db_name in DB_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                if db_name not in seen:
                    results.append({"database": db_name, "file": path})
                    seen.add(db_name)

    return results


# ======================================================================
# API ENDPOINT DETECTION
# ======================================================================

API_PATTERNS = [
    # Flask
    (r'@\w+\.route\(["\'](.+?)["\'].*?\)\s*\ndef\s+(\w+)',
     "Flask", ["python"]),
    # Django
    (r'path\(["\'](.+?)["\'].*?,\s*(\w+)',
     "Django", ["python"]),
    # Express.js
    (r'(?:app|router)\.(get|post|put|delete|patch)\(["\'](.+?)["\']',
     "Express", ["javascript", "typescript"]),
    # FastAPI
    (r'@\w+\.(get|post|put|delete|patch)\(["\'](.+?)["\']',
     "FastAPI", ["python"]),
]


def detect_api_endpoints(file_contents):
    """Detect API endpoints from route definitions."""
    endpoints = []

    for path, content in file_contents.items():
        ext = os.path.splitext(path)[1].lower()
        lang = LANGUAGE_MAP.get(ext, "")

        for pattern, framework, langs in API_PATTERNS:
            if lang not in langs:
                continue
            for match in re.finditer(pattern, content):
                groups = match.groups()
                if framework == "Express":
                    method = groups[0].upper()
                    route = groups[1]
                elif framework == "FastAPI":
                    method = groups[0].upper()
                    route = groups[1]
                else:
                    route = groups[0]
                    method = "GET"  # default
                    # Try to detect method from decorators
                    preceding = content[:match.start()]
                    if "methods=" in preceding[-200:]:
                        m = re.search(r'methods=\[(.+?)\]', preceding[-200:])
                        if m:
                            method = m.group(1).replace("'", "").replace('"', "").strip()

                endpoints.append({
                    "method": method,
                    "route": route,
                    "file": path,
                    "framework": framework,
                })

    return endpoints


# ======================================================================
# IMPORT / DEPENDENCY GRAPH
# ======================================================================

def build_import_graph(file_contents):
    """Build module-level import/dependency graph."""
    graph = defaultdict(list)

    for path, content in file_contents.items():
        ext = os.path.splitext(path)[1].lower()

        if ext == ".py":
            # Python AST-based import extraction
            try:
                tree = ast.parse(content, filename=path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            graph[path].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            graph[path].append(node.module)
            except SyntaxError:
                # Fallback to regex
                for m in re.finditer(r"^\s*(?:from|import)\s+([\w.]+)", content, re.MULTILINE):
                    graph[path].append(m.group(1))

        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            # JS/TS: require() and import ... from
            for m in re.finditer(
                r"""(?:require|import\s+.*?\s+from)\s*\(\s*['"](.+?)['"]\s*\)|import\s+.*?\s+from\s+['"](.+?)['"]""",
                content,
            ):
                dep = m.group(1) or m.group(2)
                if dep:
                    graph[path].append(dep)

        elif ext == ".java":
            for m in re.finditer(r"^import\s+([\w.]+);", content, re.MULTILINE):
                graph[path].append(m.group(1))

        elif ext == ".go":
            for m in re.finditer(r'"([\w./-]+)"', content):
                graph[path].append(m.group(1))

    # Filter to top 100 nodes for storage
    top_files = sorted(graph.keys(), key=lambda k: len(graph[k]), reverse=True)[:100]
    return {k: graph[k] for k in top_files}


# ======================================================================
# FOLDER TREE BUILDER
# ======================================================================

def build_folder_tree(files, max_depth=4):
    """Build a hierarchical folder structure dict."""
    tree = {}
    for f in files:
        parts = f.split("/")
        node = tree
        for i, part in enumerate(parts):
            if i >= max_depth:
                break
            if i == len(parts) - 1:
                # File leaf
                node[part] = "file"
            else:
                if part not in node:
                    node[part] = {}
                node = node[part]
    return tree


def folder_tree_to_string(tree, prefix="", max_lines=100):
    """Convert folder tree dict to readable string."""
    lines = []
    items = sorted(tree.items(), key=lambda x: (x[1] == "file", x[0]))

    for i, (name, value) in enumerate(items):
        if len(lines) >= max_lines:
            lines.append(f"{prefix}... (truncated)")
            break

        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        extension = "    " if is_last else "│   "

        if value == "file":
            lines.append(f"{prefix}{connector}{name}")
        else:
            lines.append(f"{prefix}{connector}{name}/")
            sub = folder_tree_to_string(value, prefix + extension, max_lines - len(lines))
            if sub:
                lines.append(sub)

    return "\n".join(lines)
