"""
Diagram Generator
==================
Auto-generate Mermaid.js diagrams:
- Architecture diagram
- Flow diagram
- Dependency graph
"""

import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class DiagramGenerator:
    """Generate Mermaid.js diagram code from analysis results."""

    def __init__(self, analysis_result: dict):
        self.result = analysis_result

    def generate_architecture_diagram(self) -> str:
        """Generate architecture diagram in Mermaid syntax."""
        components = self.result.get("components", {})
        framework = self.result.get("framework", ["Unknown"])[0]
        arch = self.result.get("architecture_type", "Monolithic")

        lines = ["graph TB"]
        lines.append(f'    title["{framework} - {arch} Architecture"]')
        lines.append('    style title fill:#f9f,stroke:#333,stroke-width:2px')
        lines.append("")

        # Client layer
        lines.append("    subgraph Client")
        lines.append('        UI["User Interface / Browser"]')
        lines.append("    end")
        lines.append("")

        # API layer
        if "routes" in components or "controllers" in components:
            lines.append("    subgraph API Layer")
            if "routes" in components:
                route_files = components["routes"][:5]
                for i, f in enumerate(route_files):
                    name = f.split("/")[-1].replace(".py", "").replace(".js", "")
                    lines.append(f'        R{i}["{name}"]')
            if "controllers" in components:
                ctrl_files = components["controllers"][:5]
                for i, f in enumerate(ctrl_files):
                    name = f.split("/")[-1].replace(".py", "").replace(".js", "")
                    lines.append(f'        C{i}["{name}"]')
            lines.append("    end")
            lines.append("")

        # Service layer
        if "services" in components:
            lines.append("    subgraph Service Layer")
            svc_files = components["services"][:5]
            for i, f in enumerate(svc_files):
                name = f.split("/")[-1].replace(".py", "").replace(".js", "")
                lines.append(f'        S{i}["{name}"]')
            lines.append("    end")
            lines.append("")

        # Model layer
        if "models" in components:
            lines.append("    subgraph Data Layer")
            model_files = components["models"][:5]
            for i, f in enumerate(model_files):
                name = f.split("/")[-1].replace(".py", "").replace(".js", "")
                lines.append(f'        M{i}["{name}"]')
            lines.append("    end")
            lines.append("")

        # Database
        db_usage = self.result.get("database_usage", [])
        if db_usage:
            db_names = list(set(d["database"] for d in db_usage))[:3]
            lines.append("    subgraph Database")
            for i, db in enumerate(db_names):
                lines.append(f'        DB{i}[("{db}")]')
            lines.append("    end")
            lines.append("")

        # Connections
        lines.append("    UI --> API Layer")
        if "services" in components:
            lines.append("    API Layer --> Service Layer")
            if "models" in components:
                lines.append("    Service Layer --> Data Layer")
            if db_usage:
                lines.append("    Service Layer --> Database")
        elif "models" in components:
            lines.append("    API Layer --> Data Layer")
            if db_usage:
                lines.append("    Data Layer --> Database")
        elif db_usage:
            lines.append("    API Layer --> Database")

        return "\n".join(lines)

    def generate_flow_diagram(self) -> str:
        """Generate request flow diagram."""
        endpoints = self.result.get("api_endpoints", [])
        entry_points = self.result.get("entry_points", [])

        lines = ["flowchart LR"]

        if not endpoints and not entry_points:
            lines.append('    A["Start"] --> B["Application"]')
            return "\n".join(lines)

        lines.append('    User["👤 User"] --> Request["HTTP Request"]')

        if entry_points:
            ep = entry_points[0]
            name = ep["file"].split("/")[-1]
            lines.append(f'    Request --> Entry["{name}"]')

            if endpoints:
                # Group endpoints by method
                methods = defaultdict(list)
                for ep in endpoints[:10]:
                    methods[ep.get("method", "GET")].append(ep.get("route", "/"))

                lines.append('    Entry --> Router["Router / URL Dispatcher"]')

                for method, routes in methods.items():
                    method_id = method.replace(" ", "")
                    lines.append(f'    Router --> {method_id}["{method}"]')
                    for i, route in enumerate(routes[:3]):
                        safe_route = route.replace('"', "'")
                        lines.append(f'    {method_id} --> {method_id}R{i}["{safe_route}"]')

                lines.append('    Router --> Response["Response"]')
                lines.append('    Response --> User')
        else:
            lines.append('    Request --> App["Application"]')
            lines.append('    App --> Response["Response"]')
            lines.append('    Response --> User')

        return "\n".join(lines)

    def generate_dependency_graph(self) -> str:
        """Generate dependency graph from import analysis."""
        dep_graph = self.result.get("dependency_graph", {})

        if not dep_graph:
            return 'graph LR\n    A["No dependencies detected"]'

        lines = ["graph LR"]

        # Limit to top 20 files with most dependencies
        sorted_files = sorted(dep_graph.items(), key=lambda x: len(x[1]), reverse=True)[:20]

        node_ids = {}
        counter = 0

        for file_path, deps in sorted_files:
            if file_path not in node_ids:
                node_ids[file_path] = f"N{counter}"
                counter += 1

            file_id = node_ids[file_path]
            short_name = file_path.split("/")[-1]
            lines.append(f'    {file_id}["{short_name}"]')

            # Only show local deps (not external packages)
            local_deps = [d for d in deps if not d.startswith(("os", "sys", "re", "json",
                          "datetime", "collections", "typing", "pathlib", "logging",
                          "functools", "io", "math", "hashlib", "uuid", "time",
                          "react", "vue", "@", "express", "path", "fs", "http", "url"))]

            for dep in local_deps[:5]:
                dep_short = dep.split(".")[-1] if "." in dep else dep
                if dep not in node_ids:
                    node_ids[dep] = f"N{counter}"
                    counter += 1
                dep_id = node_ids[dep]
                if f'    {dep_id}["{dep_short}"]' not in lines:
                    lines.append(f'    {dep_id}["{dep_short}"]')
                lines.append(f"    {file_id} --> {dep_id}")

        return "\n".join(lines)

    def generate_all(self) -> dict:
        """Generate all diagram types."""
        return {
            "architecture": {
                "type": "architecture",
                "mermaid_code": self.generate_architecture_diagram(),
            },
            "flow": {
                "type": "flow",
                "mermaid_code": self.generate_flow_diagram(),
            },
            "dependency": {
                "type": "dependency",
                "mermaid_code": self.generate_dependency_graph(),
            },
        }
