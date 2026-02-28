

import os
import json
import ast
import re
import requests
import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# =====================================================
# 🔐 SECRET PATTERNS (Regex Detection)
# =====================================================

SECRET_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "Generic API Key": r"(?i)api[_-]?key\s*=\s*[\"'][^\"']+[\"']",
    "JWT Token": r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
    "Private Key": r"-----BEGIN PRIVATE KEY-----",
    "Bearer Token": r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
    "Password Assignment": r"(?i)password\s*=\s*[\"'][^\"']+[\"']"
}

class OllamaAnalyzerService:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.structure = defaultdict(list)
        self.summary_data = {}
        self.ai_result = {}
        self.architecture_name = "Unknown"
        self.ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3")

    def _is_ollama_available(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            # Check only the base URL to see if it's up
            base_url = self.ollama_url.replace("/api/generate", "")
            requests.get(base_url, timeout=2)
            return True
        except:
            return False

    def scan_structure(self):
        """Scan the project folder structure."""
        if not os.path.exists(self.root_path):
            logger.error(f"Root path does not exist: {self.root_path}")
            return

        for root, dirs, files in os.walk(self.root_path):
            # Skip hidden dirs and node_modules/venv
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
            for file in files:
                relative = os.path.relpath(root, self.root_path)
                if relative == ".":
                    relative = "root"
                self.structure[relative].append(file)

    def collect_summary(self):
        """Collect dependency files for analysis."""
        dependency_files = {}

        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                if file in ["requirements.txt", "package.json", "pom.xml", "Dockerfile"]:
                    try:
                        path = os.path.join(root, file)
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                            dependency_files[file] = content[:3000] # Limit size
                    except Exception as e:
                        logger.warning(f"Failed to read {file}: {e}")

        self.summary_data = {
            "folders": list(self.structure.keys()),
            "dependency_files": dependency_files
        }

    def analyze_architecture(self) -> str:
        """Ask Ollama for Tech Stack + Architecture analysis."""
        if not self._is_ollama_available():
            return "Ollama is not available for architectural analysis."

        self.scan_structure()
        self.collect_summary()

        prompt = f"""
You are a senior software architect.
Analyze this project based on its structure and dependencies.

Folders:
{self.summary_data["folders"]}

Dependency Files:
{json.dumps(self.summary_data["dependency_files"], indent=2)}

Return ONLY a valid JSON object:
{{
    "backend": "detected backend tech",
    "frontend": "detected frontend tech",
    "database": "detected database",
    "language": "primary languages",
    "deployment": "deployment method",
    "architecture": "MVC, Layered, Microservices, etc.",
    "confidence": "percentage"
}}
"""

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return f"Error from Ollama: {response.status_code}"

            raw = response.json()["response"]
            
            # Extract JSON
            start = raw.find("{")
            end = raw.rfind("}") + 1
            if start != -1 and end != -1:
                self.ai_result = json.loads(raw[start:end])
                self.architecture_name = self.ai_result.get("architecture", "Unknown")
                
                # Format a nice markdown response
                res = f"### 🤖 Architectural Analysis (Ollama)\n\n"
                res += f"- **Architecture**: {self.ai_result.get('architecture', 'Unknown')}\n"
                res += f"- **Backend**: {self.ai_result.get('backend', 'Unknown')}\n"
                res += f"- **Frontend**: {self.ai_result.get('frontend', 'Unknown')}\n"
                res += f"- **Database**: {self.ai_result.get('database', 'Unknown')}\n"
                res += f"- **Language**: {self.ai_result.get('language', 'Unknown')}\n"
                res += f"- **Deployment**: {self.ai_result.get('deployment', 'Unknown')}\n"
                res += f"- **Confidence**: {self.ai_result.get('confidence', 'Unknown')}\n"
                return res
            else:
                return f"Failed to parse architectural analysis from Ollama.\n\nRaw response:\n{raw}"
        except Exception as e:
            logger.error(f"Ollama integration error: {e}")
            return f"Error connecting to Ollama: {str(e)}"

    def detect_syntax_errors(self) -> str:
        """Scan for Python syntax errors and get AI explanations."""
        results = []
        python_files = []
        
        for root, dirs, files in os.walk(self.root_path):
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        if not python_files:
            return "No Python files found to check syntax."

        results.append("### 🔎 Python Syntax Check\n")
        errors_found = 0

        for path in python_files[:20]: # Limit scan for chat context
            file_name = os.path.relpath(path, self.root_path)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
                ast.parse(code)
            except SyntaxError as e:
                errors_found += 1
                results.append(f"❌ **{file_name}** - Syntax Error at line {e.lineno}")
                results.append(f"> {e}")
                
                if self._is_ollama_available():
                    explanation = self._ask_ollama_syntax_explain(code, e)
                    results.append(f"\n**AI Explanation:**\n{explanation}\n")
                else:
                    results.append("\n(AI explanation unavailable)\n")
            except Exception as e:
                logger.warning(f"Failed to check {path}: {e}")

        if errors_found == 0:
            results.append("✅ No syntax errors detected in the checked Python files.")

        return "\n".join(results)

    def _ask_ollama_syntax_explain(self, code: str, error: Exception) -> str:
        """Get syntax error explanation from Ollama."""
        prompt = f"""
You are a Python expert.
Explain this syntax error and show a corrected snippet.

Syntax Error:
{error}

Code Snippet (partial):
{code[:2000]}
"""
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            return response.json()["response"]
        except:
            return "Could not get explanation from Ollama."

    def scan_for_secrets(self) -> str:
        """Scan for exposed API keys and validate with AI."""
        results = ["### 🔐 Secret Detection Scan\n"]
        secrets_found = 0

        for root, dirs, files in os.walk(self.root_path):
            # Skip node_modules etc.
            if any(p in root for p in ['node_modules', 'venv', '.git']):
                continue

            for file in files:
                if file.endswith((".py", ".js", ".env", ".json", ".ts", ".tsx")):
                    path = os.path.join(root, file)
                    file_name = os.path.relpath(path, self.root_path)

                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                    except:
                        continue

                    for name, pattern in SECRET_PATTERNS.items():
                        for match in re.finditer(pattern, content):
                            secrets_found += 1
                            line_no = content[:match.start()].count("\n") + 1
                            lines = content.splitlines()
                            snippet = lines[line_no - 1].strip() if line_no <= len(lines) else "unknown"

                            # Mask for display
                            masked = re.sub(r'(["\'])(.*?)(["\'])', r'\1****\3', snippet)

                            results.append(f"⚠ **{name}** detected in `{file_name}` at line {line_no}")
                            results.append(f"> Masked Snippet: `{masked}`")

                            if self._is_ollama_available():
                                ai_result = self._ask_ollama_secret_validation(snippet)
                                results.append(f"\n**AI Security Audit:**\n{ai_result}\n")
                            else:
                                results.append("")

                            if secrets_found >= 10: # Cap results
                                results.append("\n*Capping scan at 10 results.*")
                                return "\n".join(results)

        if secrets_found == 0:
            results.append("✅ No obvious secrets or API keys detected.")

        return "\n".join(results)

    def _ask_ollama_secret_validation(self, snippet: str) -> str:
        """Validate potential secret with Ollama."""
        prompt = f"""
You are a security auditor.
Does this code snippet contain a real exposed secret (API key, password, token)?
Evaluate the risk.

Snippet:
{snippet}

Expected Format:
Result: (Real Secret / False Positive)
Risk: (High / Medium / Low)
Reason: (Brief explanation)
"""
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            return response.json()["response"]
        except:
            return "Could not validate with Ollama."

    def generate_mermaid_diagram(self) -> str:
        """Generate a Mermaid diagram based on detected architecture."""
        self.scan_structure()
        self.collect_summary()
        
        # If we haven't analyzed architecture yet, do it now
        if not self.ai_result:
            self.analyze_architecture()

        arch = self.architecture_name.lower()
        diagram = "```mermaid\ngraph TD\n"

        if "mvc" in arch:
            diagram += "    Client --> Controllers\n"
            diagram += "    Controllers --> Models\n"
            diagram += "    Models --> Database\n"
        elif "layered" in arch or "clean" in arch:
            diagram += "    Client --> Controllers\n"
            diagram += "    Controllers --> Services\n"
            diagram += "    Services --> Repositories\n"
            diagram += "    Repositories --> Database\n"
        elif "microservices" in arch:
            diagram += "    Client --> API_Gateway\n"
            diagram += "    API_Gateway --> Service_A\n"
            diagram += "    API_Gateway --> Service_B\n"
            diagram += "    Service_A --> DB_A\n"
            diagram += "    Service_B --> DB_B\n"
        else:
            diagram += "    Client --> Application\n"
            diagram += "    Application --> Database\n"
            
        diagram += "```"
        return f"### 📊 System Architecture Diagram\n\n{diagram}\n\n*Generated based on {self.architecture_name} architecture.*"