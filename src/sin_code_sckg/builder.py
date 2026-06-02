"""Build knowledge graph from a Python repository using AST.

Docs: builder.py.doc.md
"""

import ast
import os
from pathlib import Path
from typing import Set

from .nodes import FileNode, FunctionNode, ClassNode, ModuleNode
from .edges import Edge, EdgeType


class GraphBuilder:
    """Extracts nodes and edges from a Python repository."""

    def __init__(self, exclude: set[str] | None = None):
        self.exclude = exclude or set()
        self.exclude.update({"node_modules", ".venv", ".git", "dist", "build", "__pycache__", ".pytest_cache"})
        self.stats = {"files": 0, "functions": 0, "classes": 0, "edges": 0}
        self.nodes = []
        self.edges = []

    def build(self, repo: str | Path) -> tuple[list, list, dict]:
        """Walk repo and extract all nodes and edges.

        Returns (nodes, edges, stats).
        """
        repo_path = Path(repo).resolve()
        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude]
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    self._process_file(file_path, repo_path)
        self.stats["edges"] = len(self.edges)
        return self.nodes, self.edges, self.stats

    def _process_file(self, file_path: Path, repo_path: Path) -> None:
        """Parse a single Python file and extract nodes/edges."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return

        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError:
            return
        except Exception:
            return

        rel_path = file_path.relative_to(repo_path).as_posix()
        module_name = rel_path.replace("/", ".").replace("\\", ".").replace(".py", "")

        # Create FileNode and ModuleNode
        file_id = f"file:{rel_path}"
        module_id = f"module:{module_name}"

        file_node = FileNode(id=file_id, name=file_path.name, file_path=str(file_path))
        module_node = ModuleNode(id=module_id, name=module_name, file_path=str(file_path))
        self.nodes.append(file_node)
        self.nodes.append(module_node)
        self.stats["files"] += 1

        # Edge: file CONTAINS module
        self.edges.append(Edge(source=file_id, target=module_id, type=EdgeType.CONTAINS.value))

        self._extract_from_ast(tree, file_path, rel_path, module_id, source)

    def _extract_from_ast(self, tree: ast.AST, file_path: Path, rel_path: str, module_id: str, source: str) -> None:
        """Walk AST and extract classes, functions, imports, calls, inheritance."""
        processed_methods: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_id = f"class:{module_id}:{node.name}"
                class_node = ClassNode(
                    id=class_id,
                    name=node.name,
                    file_path=str(file_path),
                    line_number=node.lineno,
                )
                self.nodes.append(class_node)
                self.stats["classes"] += 1
                self.edges.append(Edge(source=module_id, target=class_id, type=EdgeType.CONTAINS.value))

                # Inheritance
                for base in node.bases:
                    base_name = self._get_name(base)
                    if base_name:
                        base_id = self._resolve_name(base_name, module_id)
                        self.edges.append(Edge(source=class_id, target=base_id, type=EdgeType.INHERITS.value))

                # Methods inside class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        processed_methods.add(id(item))
                        func_id = f"func:{class_id}:{item.name}"
                        func_node = FunctionNode(
                            id=func_id,
                            name=item.name,
                            file_path=str(file_path),
                            line_number=item.lineno,
                            metadata={"class": node.name},
                        )
                        self.nodes.append(func_node)
                        self.stats["functions"] += 1
                        self.edges.append(Edge(source=class_id, target=func_id, type=EdgeType.CONTAINS.value))
                        self._extract_calls(item, func_id, module_id)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Top-level functions only (skip methods, handled above)
                if id(node) in processed_methods:
                    continue
                func_id = f"func:{module_id}:{node.name}"
                func_node = FunctionNode(
                    id=func_id,
                    name=node.name,
                    file_path=str(file_path),
                    line_number=node.lineno,
                )
                self.nodes.append(func_node)
                self.stats["functions"] += 1
                self.edges.append(Edge(source=module_id, target=func_id, type=EdgeType.CONTAINS.value))
                self._extract_calls(node, func_id, module_id)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    import_id = f"module:{alias.name}"
                    self.edges.append(Edge(source=module_id, target=import_id, type=EdgeType.IMPORTS.value))

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    import_id = f"module:{module}.{alias.name}"
                    self.edges.append(Edge(source=module_id, target=import_id, type=EdgeType.IMPORTS.value))

    def _extract_calls(self, node: ast.FunctionDef | ast.AsyncFunctionDef, func_id: str, module_id: str) -> None:
        """Extract function calls from a function body."""
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_name(child.func)
                if call_name:
                    target_id = self._resolve_name(call_name, module_id)
                    self.edges.append(Edge(source=func_id, target=target_id, type=EdgeType.CALLS.value))

    def _get_name(self, node: ast.AST) -> str | None:
        """Extract dotted name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            value = self._get_name(node.value)
            if value:
                return f"{value}.{node.attr}"
            return node.attr
        return None

    def _resolve_name(self, name: str, module_id: str) -> str:
        """Best-effort resolution of a name to a node ID."""
        # If name contains a dot, treat as module-qualified
        if "." in name:
            parts = name.split(".")
            # Heuristic: if first part is a known module, treat as module:...
            return f"module:{name}"
        # Otherwise assume local to current module
        return f"func:{module_id}:{name}"
