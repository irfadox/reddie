"""Static analysis engine for LLM application codebases."""

import ast
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class StaticAnalyzer:
    """Analyzes a codebase statically to extract system prompts, tool definitions, and variables."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {self.repo_path}")

    def analyze(self) -> Dict[str, Any]:
        """Runs full static analysis on the target repository."""
        system_prompts: Dict[str, str] = {}
        tool_definitions: List[Dict[str, Any]] = []
        discovered_files: List[str] = []
        endpoints: List[Dict[str, Any]] = []

        for root, dirs, files in os.walk(self.repo_path):
            # Exclude hidden directories, caches, and virtualenvs
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("venv", ".venv", "__pycache__", "node_modules", "dist", "build")]

            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                discovered_files.append(rel_path)
                full_path = Path(root) / file

                if file.endswith(".py"):
                    try:
                        prompts, tools, routes = self._analyze_python_file(full_path, rel_path)
                        system_prompts.update(prompts)
                        tool_definitions.extend(tools)
                        endpoints.extend(routes)
                    except Exception as e:
                        # Continue gracefully on syntax errors
                        continue
                elif file.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs")):
                    try:
                        prompts, routes = self._analyze_js_file(full_path, rel_path)
                        system_prompts.update(prompts)
                        endpoints.extend(routes)
                    except Exception as e:
                        continue
                elif file.endswith((".txt", ".json", ".yaml", ".yml", ".md")):
                    prompts = self._analyze_text_file(full_path, rel_path)
                    system_prompts.update(prompts)

        return {
            "system_prompts": system_prompts,
            "tool_definitions": tool_definitions,
            "discovered_files": discovered_files,
            "endpoint_metadata": {
                "inferred_endpoints": endpoints,
                "total_files": len(discovered_files),
            },
        }

    def _analyze_python_file(self, full_path: Path, rel_path: str) -> Tuple[Dict[str, str], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parses a Python file using AST and regex for prompts, tools, and endpoints."""
        prompts: Dict[str, str] = {}
        tools: List[Dict[str, Any]] = []
        routes: List[Dict[str, Any]] = []

        content = full_path.read_text(encoding="utf-8", errors="ignore")
        
        try:
            tree = ast.parse(content, filename=str(full_path))
        except SyntaxError:
            # Fallback to regex if syntax error
            prompts.update(self._extract_prompts_regex(content, rel_path))
            return prompts, tools, routes

        # 1. AST walk for assignments, docstrings, decorators
        for node in ast.walk(tree):
            # Check variable assignments: e.g. SYSTEM_PROMPT = "..." or prompt = "..."
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    name = ""
                    if isinstance(target, ast.Name):
                        name = target.id
                    elif isinstance(target, ast.Attribute):
                        name = target.attr

                    if name and any(k in name.lower() for k in ["prompt", "system", "instruction", "persona", "template"]):
                        val = self._extract_ast_string_value(node.value)
                        if val and len(val.strip()) > 10:
                            key = f"{rel_path}:{name}"
                            prompts[key] = val.strip()

            # Check LangChain, CrewAI, LlamaIndex, OpenAI/Anthropic instantiations
            elif isinstance(node, ast.Call):
                func_name = self._get_call_func_name(node)
                if func_name in ("SystemMessage", "SystemMessagePromptTemplate", "PromptTemplate", "ChatPromptTemplate"):
                    for arg in node.args:
                        val = self._extract_ast_string_value(arg)
                        if val and len(val.strip()) > 10:
                            key = f"{rel_path}:{func_name}_{node.lineno}"
                            prompts[key] = val.strip()
                    for kw in node.keywords:
                        if kw.arg in ("content", "template"):
                            val = self._extract_ast_string_value(kw.value)
                            if val and len(val.strip()) > 10:
                                key = f"{rel_path}:{func_name}_{kw.arg}_{node.lineno}"
                                prompts[key] = val.strip()

                # Check CrewAI Agent(role=..., goal=..., backstory=...)
                elif func_name in ("Agent", "CrewAgent", "WorkerAgent"):
                    crew_parts = []
                    for kw in node.keywords:
                        if kw.arg in ("role", "goal", "backstory"):
                            val = self._extract_ast_string_value(kw.value)
                            if val:
                                crew_parts.append(f"{kw.arg.capitalize()}: {val}")
                    if crew_parts:
                        prompts[f"{rel_path}:CrewAI_Agent_{node.lineno}"] = "\n".join(crew_parts)

                # Check general system_prompt / system kwargs in LLM calls
                else:
                    for kw in node.keywords:
                        if kw.arg in ("system_prompt", "system", "instructions", "prompt_template"):
                            val = self._extract_ast_string_value(kw.value)
                            if val and len(val.strip()) > 10:
                                prompts[f"{rel_path}:{kw.arg}_{node.lineno}"] = val.strip()

            # Check Function definitions for @tool decorator
            elif isinstance(node, ast.FunctionDef):
                is_tool = False
                for dec in node.decorator_list:
                    dec_name = self._get_decorator_name(dec)
                    if dec_name in ("tool", "langchain.tools.tool", "ai_tool"):
                        is_tool = True
                        break

                if is_tool:
                    doc = ast.get_docstring(node) or ""
                    args_list = [a.arg for a in node.args.args if a.arg != "self"]
                    tools.append({
                        "file": rel_path,
                        "function_name": node.name,
                        "line_number": node.lineno,
                        "docstring": doc,
                        "arguments": args_list,
                    })

                # Check for FastAPI / Flask routes
                for dec in node.decorator_list:
                    dec_name = self._get_decorator_name(dec)
                    if any(r in dec_name.lower() for r in ["get", "post", "put", "delete", "route", "api"]):
                        routes.append({
                            "file": rel_path,
                            "function": node.name,
                            "line": node.lineno,
                            "decorator": dec_name,
                        })

        # Also apply regex to catch multi-line raw prompts that might be in helper dicts
        prompts.update(self._extract_prompts_regex(content, rel_path))
        return prompts, tools, routes

    def _analyze_js_file(self, full_path: Path, rel_path: str) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """Analyzes JavaScript and TypeScript files for system prompts and API endpoints."""
        prompts: Dict[str, str] = {}
        routes: List[Dict[str, Any]] = []

        content = full_path.read_text(encoding="utf-8", errors="ignore")

        # 1. Capture systemPrompt / prompt assignments in JS objects or variables
        patterns = [
            (r'([a-zA-Z_0-9]*systemPrompt[a-zA-Z_0-9]*)\s*:\s*[`"\']([\s\S]*?)[`"\']', 1, 2),
            (r'([a-zA-Z_0-9]*prompt[a-zA-Z_0-9]*)\s*:\s*[`"\']([\s\S]*?)[`"\']', 1, 2),
            (r'const\s+([a-zA-Z_0-9]*system[a-zA-Z_0-9]*)\s*=\s*[`"\']([\s\S]*?)[`"\']', 1, 2),
            (r'const\s+([a-zA-Z_0-9]*prompt[a-zA-Z_0-9]*)\s*=\s*[`"\']([\s\S]*?)[`"\']', 1, 2),
            (r'role:\s*["\']system["\'],\s*content:\s*[`"\']([\s\S]*?)[`"\']', None, 1),
        ]

        for pat in patterns:
            for match in re.finditer(pat[0], content, re.IGNORECASE):
                val = match.group(pat[2]).strip()
                if len(val) > 10:
                    var_name = match.group(pat[1]) if pat[1] is not None else "system_message"
                    key = f"{rel_path}:{var_name}"
                    prompts[key] = val

        # 2. Extract fetch / axios API endpoints
        endpoint_patterns = [
            r'fetch\(["\'](https?://[^"\']+)["\']',
            r'axios\.(?:get|post|put)\(["\'](https?://[^"\']+)["\']',
        ]
        for ep_pat in endpoint_patterns:
            for match in re.finditer(ep_pat, content):
                routes.append({
                    "file": rel_path,
                    "url": match.group(1),
                })

        return prompts, routes

    def _extract_text_file(self, full_path: Path, rel_path: str) -> Dict[str, str]:
        """Extracts prompts from raw text, yaml, or json files if relevant."""
        prompts: Dict[str, str] = {}
        content = full_path.read_text(encoding="utf-8", errors="ignore").strip()
        if not content:
            return prompts

        lower_path = rel_path.lower()
        if any(k in lower_path for k in ["prompt", "system", "agent", "persona", "instruction"]):
            prompts[rel_path] = content
        return prompts

    def _analyze_text_file(self, full_path: Path, rel_path: str) -> Dict[str, str]:
        return self._extract_text_file(full_path, rel_path)

    def _extract_ast_string_value(self, node: ast.AST) -> Optional[str]:
        """Extracts string or joined f-string value from AST."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.JoinedStr):
            parts = []
            for val in node.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    parts.append(val.value)
                elif isinstance(val, ast.FormattedValue):
                    parts.append(f"{{{ast.unparse(val.value)}}}")
            return "".join(parts)
        return None

    def _get_call_func_name(self, call_node: ast.Call) -> str:
        """Extracts function name from a Call AST node."""
        if isinstance(call_node.func, ast.Name):
            return call_node.func.id
        elif isinstance(call_node.func, ast.Attribute):
            return call_node.func.attr
        return ""

    def _get_decorator_name(self, dec_node: ast.AST) -> str:
        """Extracts name from decorator AST node."""
        if isinstance(dec_node, ast.Name):
            return dec_node.id
        elif isinstance(dec_node, ast.Attribute):
            return f"{self._get_decorator_name(dec_node.value)}.{dec_node.attr}" if isinstance(dec_node.value, (ast.Name, ast.Attribute)) else dec_node.attr
        elif isinstance(dec_node, ast.Call):
            return self._get_decorator_name(dec_node.func)
        return ""

    def _extract_prompts_regex(self, content: str, rel_path: str) -> Dict[str, str]:
        """Regex fallback to capture prompt constants and templates."""
        prompts: Dict[str, str] = {}
        patterns = [
            (r'([A-Z_]*SYSTEM[A-Z_]*PROMPT[A-Z_]*)\s*=\s*["\']{3}([\s\S]*?)["\']{3}', 2),
            (r'([A-Z_]*PROMPT[A-Z_]*)\s*=\s*["\']{3}([\s\S]*?)["\']{3}', 2),
            (r'([a-zA-Z_0-9]*system_prompt[a-zA-Z_0-9]*)\s*=\s*["\']{3}([\s\S]*?)["\']{3}', 2),
            (r'([a-zA-Z_0-9]*system_message[a-zA-Z_0-9]*)\s*=\s*["\']{3}([\s\S]*?)["\']{3}', 2),
        ]

        for pattern, group_idx in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                key = f"{rel_path}:{match.group(1)}"
                val = match.group(group_idx).strip()
                if len(val) > 10:
                    prompts[key] = val

        return prompts

    def extract_placeholders(self, prompt_text: str) -> List[str]:
        """Extracts variable placeholders like {user_input}, {context} from a prompt."""
        return re.findall(r"\{([a-zA-Z0-9_]+)\}", prompt_text)
