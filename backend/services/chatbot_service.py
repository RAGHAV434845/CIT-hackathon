"""
AI Chatbot Service
===================
Intelligent assistant that uses structured analysis results
to answer questions about the repository.

Uses Google Gemini API for natural language responses.
Does NOT send entire repository — only structured metadata.
"""

import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import Gemini
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not installed. Chatbot will use fallback mode.")


# ---------------------------------------------------------------------------
# System prompt template — provides structured context to the LLM
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an AI assistant specialized in understanding codebases.
You have been given structured analysis results of a repository. Use ONLY the provided
metadata to answer questions. Be specific, reference actual file names and structures.

REPOSITORY ANALYSIS DATA:
========================

Project: {repo_name}
Framework(s): {frameworks}
Architecture: {architecture}
Tech Stack: {tech_stack}
Total Files: {total_files}
Total Lines: {total_lines}

Languages:
{languages}

Entry Points:
{entry_points}

API Endpoints:
{api_endpoints}

Components:
{components}

Database Usage:
{database_usage}

Folder Structure:
{folder_structure}

INSTRUCTIONS:
- Answer based ONLY on the provided analysis data
- Reference specific files and paths when possible
- If asked about something not in the data, say you don't have that information
- Be concise and technical
- When explaining flows, trace through the actual files
- For architecture questions, reference the component breakdown
"""

# ---------------------------------------------------------------------------
# Pre-built responses for common queries (no LLM needed)
# ---------------------------------------------------------------------------
DETERMINISTIC_QUERIES = {
    "tech stack": lambda r: f"**Tech Stack:** {', '.join(r.get('tech_stack', ['Not detected']))}",
    "framework": lambda r: f"**Frameworks:** {', '.join(r.get('framework', ['Not detected']))}",
    "architecture": lambda r: f"**Architecture:** {r.get('architecture_type', 'Unknown')}",
    "entry point": lambda r: _format_entry_points(r),
    "api endpoint": lambda r: _format_endpoints(r),
    "database": lambda r: _format_database(r),
    "how many files": lambda r: f"The project has **{r.get('total_files', 0)}** files and **{r.get('total_lines', 0):,}** lines of code.",
    "languages": lambda r: _format_languages(r),
    "folder structure": lambda r: _format_folder_structure(r),
}


def _format_entry_points(r):
    eps = r.get("entry_points", [])
    if not eps:
        return "No entry points detected."
    lines = ["**Entry Points:**"]
    for ep in eps[:10]:
        lines.append(f"- `{ep['file']}` — {ep['reason']}")
    return "\n".join(lines)


def _format_endpoints(r):
    endpoints = r.get("api_endpoints", [])
    if not endpoints:
        return "No API endpoints detected."
    lines = ["**API Endpoints:**"]
    for ep in endpoints[:15]:
        lines.append(f"- `{ep.get('method', 'GET')}` `{ep.get('route', '/')}` in `{ep.get('file', '')}`")
    if len(endpoints) > 15:
        lines.append(f"... and {len(endpoints) - 15} more")
    return "\n".join(lines)


def _format_database(r):
    dbs = r.get("database_usage", [])
    if not dbs:
        return "No database usage detected."
    lines = ["**Database Usage:**"]
    for db in dbs:
        lines.append(f"- **{db['database']}** in `{db['file']}`")
    return "\n".join(lines)


def _format_languages(r):
    langs = r.get("languages", {})
    if not langs:
        return "No languages detected."
    total = sum(langs.values()) or 1
    lines = ["**Language Breakdown:**"]
    for lang, count in sorted(langs.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total) * 100
        lines.append(f"- **{lang}**: {count:,} lines ({pct:.1f}%)")
    return "\n".join(lines)


def _format_folder_structure(r):
    from engine.analyzer import folder_tree_to_string
    tree = r.get("folder_structure", {})
    if not tree:
        return "No folder structure available."
    tree_str = folder_tree_to_string(tree, max_lines=30)
    return f"**Folder Structure:**\n```\n{tree_str}\n```"


class ChatbotService:
    """Repository-aware chatbot."""

    def __init__(self, analysis_result: dict, repo_name: str = "Project"):
        self.result = analysis_result
        self.repo_name = repo_name
        self.model = None

        if GEMINI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel(
                        os.getenv("GEMINI_MODEL", "gemini-pro")
                    )
                    logger.info("Gemini model initialized for chatbot")
                except Exception as e:
                    logger.error(f"Failed to init Gemini: {e}")

    def _build_context(self) -> str:
        """Build structured context string from analysis."""
        return SYSTEM_PROMPT.format(
            repo_name=self.repo_name,
            frameworks=", ".join(self.result.get("framework", ["Unknown"])),
            architecture=self.result.get("architecture_type", "Unknown"),
            tech_stack=", ".join(self.result.get("tech_stack", [])),
            total_files=self.result.get("total_files", 0),
            total_lines=self.result.get("total_lines", 0),
            languages=json.dumps(self.result.get("languages", {}), indent=2),
            entry_points=json.dumps(self.result.get("entry_points", [])[:10], indent=2),
            api_endpoints=json.dumps(self.result.get("api_endpoints", [])[:20], indent=2),
            components=json.dumps(
                {k: v[:10] for k, v in self.result.get("components", {}).items()},
                indent=2,
            ),
            database_usage=json.dumps(self.result.get("database_usage", []), indent=2),
            folder_structure=json.dumps(self.result.get("folder_structure", {}), indent=2)[:2000],
        )

    def chat(self, user_message: str) -> str:
        """Process user message and return response."""
        msg_lower = user_message.lower().strip()

        # Try deterministic response first
        for keyword, handler in DETERMINISTIC_QUERIES.items():
            if keyword in msg_lower:
                return handler(self.result)

        # Special commands
        if "unused files" in msg_lower or "dead code" in msg_lower:
            return self._find_unused_files()

        if "circular" in msg_lower and "depend" in msg_lower:
            return self._detect_circular_deps()

        # Fall back to LLM
        if self.model:
            return self._llm_response(user_message)

        return self._fallback_response(user_message)

    def _llm_response(self, user_message: str) -> str:
        """Get response from Gemini."""
        try:
            context = self._build_context()
            prompt = f"{context}\n\nUser Question: {user_message}"
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._fallback_response(user_message)

    def _fallback_response(self, user_message: str) -> str:
        """Provide basic response without LLM."""
        msg_lower = user_message.lower()

        if "login" in msg_lower or "auth" in msg_lower:
            auth_files = [f for f in self.result.get("files", [])
                         if "auth" in f.lower() or "login" in f.lower()]
            if auth_files:
                return f"Authentication-related files found:\n" + "\n".join(f"- `{f}`" for f in auth_files[:10])
            return "No authentication files detected in the codebase."

        if "test" in msg_lower:
            test_files = self.result.get("components", {}).get("tests", [])
            if test_files:
                return f"**Test files ({len(test_files)}):**\n" + "\n".join(f"- `{f}`" for f in test_files[:10])
            return "No test files detected."

        # Generic response
        return (
            f"I have analysis data for **{self.repo_name}** "
            f"({self.result.get('total_files', 0)} files, "
            f"{', '.join(self.result.get('framework', ['Unknown']))} framework). "
            f"Try asking about: tech stack, architecture, entry points, API endpoints, "
            f"database usage, folder structure, or specific components."
        )

    def _find_unused_files(self) -> str:
        """Find files not imported by any other file."""
        dep_graph = self.result.get("dependency_graph", {})
        all_files = set(self.result.get("files", []))
        imported_files = set()

        for deps in dep_graph.values():
            for dep in deps:
                # Approximate: check if any file matches the dep
                for f in all_files:
                    if dep.replace(".", "/") in f or dep in f:
                        imported_files.add(f)

        # Files that import things but are never imported
        source_files = set(dep_graph.keys())
        potentially_unused = source_files - imported_files

        if not potentially_unused:
            return "No obviously unused source files detected (all tracked files appear to be referenced)."

        lines = [f"**Potentially unused files ({len(potentially_unused)}):**"]
        for f in sorted(potentially_unused)[:15]:
            lines.append(f"- `{f}`")
        lines.append("\n*Note: These files are not imported by other tracked files. They may be entry points or configuration.*")
        return "\n".join(lines)

    def _detect_circular_deps(self) -> str:
        """Detect circular dependencies in import graph."""
        dep_graph = self.result.get("dependency_graph", {})
        cycles = []

        # Simple DFS cycle detection
        visited = set()
        rec_stack = set()

        def dfs(node, path):
            visited.add(node)
            rec_stack.add(node)

            for dep in dep_graph.get(node, []):
                # Find if dep matches any file
                matching = [f for f in dep_graph.keys()
                          if dep.replace(".", "/") in f or dep in f]
                for m in matching:
                    if m in rec_stack:
                        cycle = path[path.index(m):] + [m] if m in path else [node, m]
                        cycles.append(cycle)
                    elif m not in visited:
                        dfs(m, path + [m])

            rec_stack.discard(node)

        for node in dep_graph:
            if node not in visited:
                dfs(node, [node])

        if not cycles:
            return "No circular dependencies detected in the import graph."

        lines = [f"**Circular Dependencies Found ({len(cycles)}):**"]
        for i, cycle in enumerate(cycles[:5]):
            lines.append(f"\n**Cycle {i+1}:**")
            lines.append(" → ".join(f"`{c}`" for c in cycle))

        return "\n".join(lines)
