"""
README & Documentation Generator
==================================
Generates structured documentation from analysis results.
Supports: Markdown, PDF export.
"""

import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ReadmeGenerator:
    """Generate README.md from analysis results."""

    def __init__(self, analysis_result: dict, repo_name: str = "Project"):
        self.result = analysis_result
        self.repo_name = repo_name

    def generate(self) -> str:
        """Generate complete README markdown."""
        sections = [
            self._header(),
            self._description(),
            self._tech_stack(),
            self._architecture(),
            self._folder_structure(),
            self._installation(),
            self._api_endpoints(),
            self._features(),
            self._database(),
            self._license(),
        ]
        return "\n\n".join(filter(None, sections))

    def _header(self) -> str:
        frameworks = ", ".join(self.result.get("framework", ["Unknown"]))
        return f"""# {self.repo_name}

> Built with {frameworks}

![Status](https://img.shields.io/badge/status-active-success.svg)
![Languages](https://img.shields.io/badge/languages-{len(self.result.get('languages', {}))}-blue.svg)
"""

    def _description(self) -> str:
        arch = self.result.get("architecture_type", "Unknown")
        total_files = self.result.get("total_files", 0)
        total_lines = self.result.get("total_lines", 0)

        return f"""## 📋 Description

This project follows a **{arch}** architecture pattern.

| Metric | Value |
|--------|-------|
| Total Files | {total_files} |
| Total Lines | {total_lines:,} |
| Architecture | {arch} |
| Frameworks | {', '.join(self.result.get('framework', ['Unknown']))} |
"""

    def _tech_stack(self) -> str:
        stack = self.result.get("tech_stack", [])
        if not stack:
            return ""

        items = "\n".join(f"- {tech}" for tech in stack)
        return f"""## 🛠️ Tech Stack

{items}
"""

    def _architecture(self) -> str:
        arch = self.result.get("architecture_type", "Unknown")
        components = self.result.get("components", {})

        comp_lines = []
        for category, files in components.items():
            if category == "other":
                continue
            comp_lines.append(f"- **{category.title()}**: {len(files)} files")

        comp_str = "\n".join(comp_lines) if comp_lines else "- Standard structure"

        return f"""## 🏗️ Architecture

**Pattern**: {arch}

### Components

{comp_str}
"""

    def _folder_structure(self) -> str:
        tree = self.result.get("folder_structure", {})
        if not tree:
            return ""

        from engine.analyzer import folder_tree_to_string
        tree_str = folder_tree_to_string(tree, max_lines=40)

        return f"""## 📁 Folder Structure

```
{self.repo_name}/
{tree_str}
```
"""

    def _installation(self) -> str:
        frameworks = self.result.get("framework", [])
        tech_stack = self.result.get("tech_stack", [])

        steps = [f"```bash", f"git clone <repository-url>", f"cd {self.repo_name}", "```"]

        # Detect package manager
        if any(f in ["Flask", "Django", "FastAPI"] for f in frameworks):
            steps.extend([
                "",
                "### Python Setup",
                "```bash",
                "python -m venv venv",
                "source venv/bin/activate  # Linux/Mac",
                "# venv\\Scripts\\activate  # Windows",
                "pip install -r requirements.txt",
                "```",
            ])

        if any(f in ["React", "Next.js", "Vue.js", "Express.js", "Angular"] for f in frameworks):
            steps.extend([
                "",
                "### Node.js Setup",
                "```bash",
                "npm install",
                "# or",
                "yarn install",
                "```",
            ])

        # Entry points
        entry_points = self.result.get("entry_points", [])
        if entry_points:
            steps.append("")
            steps.append("### Running the Application")
            for ep in entry_points[:3]:
                f = ep.get("file", "")
                reason = ep.get("reason", "")
                if f.endswith(".py"):
                    steps.append(f"```bash\npython {f}  # {reason}\n```")
                elif f.endswith((".js", ".ts")):
                    steps.append(f"```bash\nnode {f}  # {reason}\n```")

        return "## 🚀 Installation\n\n" + "\n".join(steps)

    def _api_endpoints(self) -> str:
        endpoints = self.result.get("api_endpoints", [])
        if not endpoints:
            return ""

        rows = []
        for ep in endpoints[:30]:
            method = ep.get("method", "GET")
            route = ep.get("route", "")
            file = ep.get("file", "")
            rows.append(f"| `{method}` | `{route}` | `{file}` |")

        table = "\n".join(rows)
        return f"""## 🔌 API Endpoints

| Method | Route | File |
|--------|-------|------|
{table}
"""

    def _features(self) -> str:
        components = self.result.get("components", {})
        features = []

        if "controllers" in components:
            features.append("- RESTful API endpoints")
        if "models" in components:
            features.append("- Data models and schemas")
        if "middleware" in components:
            features.append("- Middleware layer")
        if "tests" in components:
            features.append("- Test suite")
        if "migrations" in components:
            features.append("- Database migrations")

        db = self.result.get("database_usage", [])
        if db:
            features.append(f"- Database integration ({', '.join(d['database'] for d in db[:3])})")

        if not features:
            return ""

        return "## ✨ Features\n\n" + "\n".join(features)

    def _database(self) -> str:
        db = self.result.get("database_usage", [])
        if not db:
            return ""

        items = "\n".join(f"- **{d['database']}** (found in `{d['file']}`)" for d in db)
        return f"""## 💾 Database

{items}
"""

    def _license(self) -> str:
        return """## 📄 License

This project is licensed under the MIT License.

---

*Generated by AI Codebase Analyzer*
"""


class DocGenerator:
    """Generate technical documentation from analysis results."""

    def __init__(self, analysis_result: dict, repo_name: str = "Project"):
        self.result = analysis_result
        self.repo_name = repo_name

    def generate_api_doc(self) -> str:
        """Generate API documentation."""
        endpoints = self.result.get("api_endpoints", [])
        if not endpoints:
            return f"# {self.repo_name} - API Documentation\n\nNo API endpoints detected."

        sections = [f"# {self.repo_name} - API Documentation\n"]
        sections.append(f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n")
        sections.append(f"**Total Endpoints**: {len(endpoints)}\n")

        # Group by file
        by_file = {}
        for ep in endpoints:
            f = ep.get("file", "unknown")
            by_file.setdefault(f, []).append(ep)

        for file, eps in by_file.items():
            sections.append(f"\n## `{file}`\n")
            for ep in eps:
                method = ep.get("method", "GET")
                route = ep.get("route", "")
                sections.append(f"### {method} `{route}`\n")
                sections.append(f"- **File**: `{file}`")
                sections.append(f"- **Framework**: {ep.get('framework', 'Unknown')}")
                sections.append("")

        return "\n".join(sections)

    def generate_tech_report(self) -> str:
        """Generate technical report."""
        sections = [
            f"# {self.repo_name} - Technical Report",
            f"\n**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "## Executive Summary",
            "",
            f"This report provides a comprehensive technical analysis of the {self.repo_name} codebase.",
            f"The project uses a **{self.result.get('architecture_type', 'Unknown')}** architecture"
            f" built with **{', '.join(self.result.get('framework', ['Unknown']))}**.",
            "",
            "## Codebase Metrics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Total Files | {self.result.get('total_files', 0)} |",
            f"| Total Lines | {self.result.get('total_lines', 0):,} |",
            f"| Languages | {len(self.result.get('languages', {}))} |",
            f"| API Endpoints | {len(self.result.get('api_endpoints', []))} |",
            f"| Entry Points | {len(self.result.get('entry_points', []))} |",
            "",
            "## Language Breakdown",
            "",
        ]

        langs = self.result.get("languages", {})
        total = sum(langs.values()) or 1
        for lang, lines in sorted(langs.items(), key=lambda x: x[1], reverse=True):
            pct = (lines / total) * 100
            sections.append(f"- **{lang}**: {lines:,} lines ({pct:.1f}%)")

        sections.extend([
            "",
            "## Framework & Technology",
            "",
            f"- **Frameworks**: {', '.join(self.result.get('framework', ['Unknown']))}",
            f"- **Tech Stack**: {', '.join(self.result.get('tech_stack', []))}",
            f"- **Architecture**: {self.result.get('architecture_type', 'Unknown')}",
            "",
            "## Component Analysis",
            "",
        ])

        components = self.result.get("components", {})
        for cat, files in components.items():
            if cat == "other":
                continue
            sections.append(f"### {cat.title()} ({len(files)} files)")
            for f in files[:10]:
                sections.append(f"  - `{f}`")
            if len(files) > 10:
                sections.append(f"  - ... and {len(files) - 10} more")
            sections.append("")

        sections.extend([
            "## Database Usage",
            "",
        ])
        for db in self.result.get("database_usage", []):
            sections.append(f"- **{db['database']}** in `{db['file']}`")

        sections.extend([
            "",
            "## Entry Points",
            "",
        ])
        for ep in self.result.get("entry_points", []):
            sections.append(f"- `{ep['file']}` — {ep['reason']}")

        sections.extend([
            "",
            "---",
            "*Generated by AI Codebase Analyzer*",
        ])

        return "\n".join(sections)

    def generate_module_breakdown(self) -> str:
        """Generate module breakdown documentation."""
        sections = [
            f"# {self.repo_name} - Module Breakdown",
            f"\n**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            "",
        ]

        dep_graph = self.result.get("dependency_graph", {})
        components = self.result.get("components", {})

        for cat, files in components.items():
            if cat == "other" or not files:
                continue
            sections.append(f"## {cat.title()}")
            sections.append("")
            for f in files[:20]:
                sections.append(f"### `{f}`")
                deps = dep_graph.get(f, [])
                if deps:
                    sections.append("**Dependencies:**")
                    for d in deps[:10]:
                        sections.append(f"  - `{d}`")
                sections.append("")

        return "\n".join(sections)
