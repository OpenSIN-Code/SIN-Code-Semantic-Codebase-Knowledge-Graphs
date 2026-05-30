"""Tree-sitter basierter semantischer Parser für mehrere Sprachen."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from tree_sitter import Language, Parser, Node


@dataclass
class Symbol:
    name: str
    kind: str  # function, class, method, variable
    file: str
    line_start: int
    line_end: int
    body: str
    imports: list[str] = field(default_factory=list)
    calls: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str | None = None

    @property
    def fqid(self) -> str:
        """Fully qualified identifier."""
        return f"{self.file}:{self.kind}:{self.name}"


@dataclass
class Intent:
    commit_hash: str
    author: str
    timestamp: int
    message: str
    files_changed: list[str]
    inferred_type: str  # refactor, feature, fix, docs


class SemanticParser:
    """Parst Code und Git-History in semantische Objekte."""

    def __init__(self, languages: list[str] | None = None):
        self.languages = languages or ["python", "javascript", "typescript"]
        self._parsers: dict[str, Parser] = {}
        self._langs: dict[str, Language] = {}
        self._init_languages()

    def _init_languages(self) -> None:
        for lang in self.languages:
            try:
                pkg = __import__(f"tree_sitter_{lang}", fromlist=["language"])
                self._langs[lang] = Language(pkg.language())
                p = Parser(self._langs[lang])
                self._parsers[lang] = p
            except Exception as e:
                print(f"[WARN] Could not load {lang}: {e}")

    def _lang_for_file(self, filepath: str) -> str | None:
        ext = Path(filepath).suffix.lower()
        mapping = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
        }
        return mapping.get(ext)

    def parse_file(self, filepath: str) -> list[Symbol]:
        lang_name = self._lang_for_file(filepath)
        if not lang_name or lang_name not in self._parsers:
            return []
        try:
            with open(filepath, "rb") as f:
                source = f.read()
            tree = self._parsers[lang_name].parse(source)
        except Exception as e:
            print(f"[WARN] Failed to parse {filepath}: {e}")
            return []

        symbols: list[Symbol] = []
        self._walk(tree.root_node, source, filepath, lang_name, symbols)
        return symbols

    def _walk(
        self,
        node: Node,
        source: bytes,
        filepath: str,
        lang_name: str,
        symbols: list[Symbol],
    ) -> None:
        kind = node.type
        # Python
        if lang_name == "python":
            if kind in ("function_definition", "class_definition"):
                sym_kind = "function" if kind == "function_definition" else "class"
                name_node = next(
                    (c for c in node.children if c.type == "identifier"), None
                )
                name = name_node.text.decode("utf-8") if name_node else "<anon>"
                body_node = next(
                    (c for c in node.children if c.type == "block"), None
                )
                body = body_node.text.decode("utf-8") if body_node else ""
                # Decorators
                decorators = []
                for c in node.children:
                    if c.type == "decorated" or c.type == "decorator":
                        decorators.append(c.text.decode("utf-8"))
                # Docstring
                doc = None
                if body_node:
                    stmts = [
                        n for n in body_node.children
                        if n.type == "expression_statement"
                    ]
                    if stmts:
                        first = stmts[0]
                        if "string" in first.text.decode("utf-8").strip()[:3]:
                            doc = first.text.decode("utf-8")
                # Calls inside body
                calls = self._extract_calls(body_node, source)
                symbols.append(
                    Symbol(
                        name=name,
                        kind=sym_kind,
                        file=filepath,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        body=body,
                        calls=calls,
                        decorators=decorators,
                        docstring=doc,
                    )
                )
        # JS/TS
        elif lang_name in ("javascript", "typescript"):
            if kind in (
                "function_declaration",
                "arrow_function",
                "method_definition",
                "class_declaration",
            ):
                sym_kind = "class" if kind == "class_declaration" else "function"
                name_node = next(
                    (c for c in node.children if c.type == "identifier"), None
                )
                name = name_node.text.decode("utf-8") if name_node else "<anon>"
                body = node.text.decode("utf-8")
                calls = self._extract_calls(node, source)
                symbols.append(
                    Symbol(
                        name=name,
                        kind=sym_kind,
                        file=filepath,
                        line_start=node.start_point[0] + 1,
                        line_end=node.end_point[0] + 1,
                        body=body,
                        calls=calls,
                    )
                )
        for child in node.children:
            self._walk(child, source, filepath, lang_name, symbols)

    def _extract_calls(self, node: Node, source: bytes) -> list[str]:
        calls = []
        stack = [node]
        while stack:
            n = stack.pop()
            if n.type == "call":
                fn = next(
                    (c for c in n.children if c.type in ("identifier", "attribute")),
                    None,
                )
                if fn:
                    calls.append(fn.text.decode("utf-8"))
            stack.extend(n.children)
        return list(set(calls))

    def parse_directory(self, root: str, exclude: list[str]) -> Iterator[Symbol]:
        root_path = Path(root).resolve()
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [
                d for d in dirnames
                if d not in exclude and not d.startswith(".")
            ]
            for fname in filenames:
                full = os.path.join(dirpath, fname)
                rel = os.path.relpath(full, root_path)
                if any(rel.startswith(e) or f"/{e}/" in rel for e in exclude):
                    continue
                yield from self.parse_file(full)

    @staticmethod
    def parse_intents(repo_path: str, depth: int = 50) -> list[Intent]:
        """Parst Git-Commits zu Intent-Objekten."""
        try:
            import git
        except ImportError:
            return []
        try:
            repo = git.Repo(repo_path)
        except Exception:
            return []
        intents: list[Intent] = []
        for commit in list(repo.iter_commits())[:depth]:
            msg = commit.message.split("\n")[0].lower()
            if msg.startswith(("refactor", "ref")):
                t = "refactor"
            elif msg.startswith(("feat", "add")):
                t = "feature"
            elif msg.startswith(("fix", "bug")):
                t = "fix"
            elif msg.startswith(("doc", "readme")):
                t = "docs"
            else:
                t = "other"
            intents.append(
                Intent(
                    commit_hash=commit.hexsha,
                    author=str(commit.author),
                    timestamp=commit.committed_date,
                    message=commit.message,
                    files_changed=[d.a_path for d in commit.diff("HEAD~1")],
                    inferred_type=t,
                )
            )
        return intents
