"""Tree-sitter-based multilingual semantic parser with git-intent extraction.

Docs: parser.py.doc.md
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


# Default number of recent commits to inspect when extracting intents.
# 50 is a sweet spot for ~10s of analysis time on a typical repo.
_DEFAULT_INTENT_DEPTH = 50


@dataclass
class Symbol:
    """A parsed symbol (function / class / method) with body and call info.

    `body` holds the raw source text between `line_start` and `line_end`.
    For Python, `decorators` and `docstring` are populated; for JS/TS they
    are left empty (tree-sitter parses those with different node names).
    """
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
        """Fully qualified identifier (`<file>:<kind>:<name>`)."""
        return f"{self.file}:{self.kind}:{self.name}"


@dataclass
class Intent:
    """A git-commit-derived intent used for change-type classification.

    `inferred_type` is one of `refactor` / `feature` / `fix` / `docs` /
    `other`, derived from the commit message prefix (Conventional Commits
    style).
    """
    commit_hash: str
    author: str
    timestamp: int
    message: str
    files_changed: list[str]
    inferred_type: str  # refactor, feature, fix, docs


def _build_parser(language):
    """Construct a tree-sitter `Parser` for the given language.

    Robust against the API shift between tree-sitter 0.22 and 0.23+:
    newer versions take the language in the constructor; older versions
    need `set_language()` after construction. We try both.

    Args:
        language: A `tree_sitter.Language` instance.

    Returns:
        A configured `Parser` ready to call `.parse(source_bytes)`.
    """
    from tree_sitter import Parser
    try:
        # tree-sitter >= 0.22: Parser(language)
        return Parser(language)
    except TypeError:
        # Older API: Parser() + set_language
        p = Parser()
        p.set_language(language)
        return p


class SemanticParser:
    """Parses source files and git history into semantic `Symbol`/`Intent` objects.

    The parser is language-pluggable: pass a list of `tree_sitter_*` language
    names to `__init__`. Each language must have its grammar package installed;
    missing packages degrade silently (a `[WARN]` line is printed).
    """

    def __init__(self, languages: list[str] | None = None):
        """Initialize the parser for the requested languages.

        Args:
            languages: List of language names (`python`, `javascript`,
                `typescript`). Defaults to all three.
        """
        self.languages = languages or ["python", "javascript", "typescript"]
        self._parsers: dict = {}
        self._langs: dict = {}
        self._init_languages()

    def _init_languages(self) -> None:
        """Load grammars for each language. Missing packages are warned and skipped."""
        from tree_sitter import Language
        for lang in self.languages:
            try:
                # Convention: each grammar package exposes a `language()` factory.
                pkg = __import__(f"tree_sitter_{lang}", fromlist=["language"])
                # TypeScript's grammar package splits TS/TSX into two factories.
                if lang == "typescript":
                    raw = pkg.language_typescript()
                else:
                    raw = pkg.language()
                self._langs[lang] = Language(raw)
                self._parsers[lang] = _build_parser(self._langs[lang])
            except Exception as e:  # pragma: no cover - depends on env
                print(f"[WARN] Could not load {lang}: {e}")

    @property
    def available(self) -> bool:
        """True if at least one language loaded successfully."""
        return bool(self._parsers)

    def _lang_for_file(self, filepath: str) -> str | None:
        """Map a file path to its parser language (or None if unsupported)."""
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
        """Parse a single file and return its `Symbol`s.

        Returns an empty list if the file's language has no loaded parser
        or if parsing fails. Errors are printed as `[WARN]` and swallowed.
        """
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

    def _walk(self, node, source, filepath, lang_name, symbols) -> None:
        """Recursive AST visitor that collects `Symbol`s.

        Dispatches to language-specific extractors based on `node.type`.
        `decorated_definition` parents are inspected to recover Python
        decorators (tree-sitter separates them from the function node).
        """
        kind = node.type
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
                decorators = []
                parent = node.parent
                if parent is not None and parent.type == "decorated_definition":
                    for c in parent.children:
                        if c.type == "decorator":
                            decorators.append(c.text.decode("utf-8"))
                doc = self._python_docstring(body_node)
                calls = self._extract_calls(body_node) if body_node else []
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
        elif lang_name in ("javascript", "typescript"):
            if kind in (
                "function_declaration",
                "arrow_function",
                "method_definition",
                "class_declaration",
            ):
                sym_kind = "class" if kind == "class_declaration" else "function"
                name_node = next(
                    (c for c in node.children if c.type in ("identifier", "property_identifier")),
                    None,
                )
                name = name_node.text.decode("utf-8") if name_node else "<anon>"
                body = node.text.decode("utf-8")
                calls = self._extract_calls(node)
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

    @staticmethod
    def _python_docstring(body_node) -> str | None:
        """Extract the leading docstring string node from a function/class body.

        Uses AST node-type checks (`expression_statement > string`) rather
        than text heuristics, so f-strings or non-docstring leading strings
        are correctly ignored.
        """
        if body_node is None:
            return None
        for stmt in body_node.children:
            if stmt.type == "expression_statement":
                inner = stmt.children[0] if stmt.children else None
                if inner is not None and inner.type == "string":
                    return inner.text.decode("utf-8")
                return None
        return None

    def _extract_calls(self, node) -> list[str]:
        """Walk a subtree and collect the called function names.

        Returns a de-duplicated list (preserves no order). Handles both
        Python `call` and JS/TS `call_expression` node types.
        """
        calls = []
        stack = [node]
        while stack:
            n = stack.pop()
            if n.type == "call" or n.type == "call_expression":
                fn = next(
                    (c for c in n.children if c.type in ("identifier", "attribute", "member_expression")),
                    None,
                )
                if fn:
                    calls.append(fn.text.decode("utf-8"))
            stack.extend(n.children)
        return list(set(calls))

    def parse_directory(self, root: str, exclude: list[str]) -> Iterator[Symbol]:
        """Yield `Symbol`s from every parseable file under `root`.

        Args:
            root: Directory to walk. Must resolve to a path under the
                user's home directory (security boundary).
            exclude: Directory names (and relative path prefixes) to skip.

        Yields:
            `Symbol` records in walk order.

        Raises:
            ValueError: If `root` resolves to a path outside the home
                directory. This is a deliberate sandbox to prevent the
                parser from being tricked into reading arbitrary paths.
        """
        root_path = Path(root).resolve()
        # Enforce workspace boundary: refuse to walk outside $HOME.
        # This is a defense against path-traversal-via-config accidents.
        workspace = os.path.expanduser("~")
        if not str(root_path).startswith(workspace):
            raise ValueError(f"Path outside workspace: {root}")
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Skip excluded AND hidden directories in one pass.
            dirnames[:] = [
                d for d in dirnames
                if d not in exclude and not d.startswith(".")
            ]
            for fname in filenames:
                full = os.path.join(dirpath, fname)
                rel = os.path.relpath(full, root_path)
                # Match the relative path either as a prefix or as a
                # path component, so `exclude=["vendor"]` skips
                # `vendor/lib/foo.py` and `src/vendor/lib/foo.py`.
                if any(rel.startswith(e) or f"/{e}/" in rel for e in exclude):
                    continue
                yield from self.parse_file(full)

    @staticmethod
    def parse_intents(repo_path: str, depth: int = _DEFAULT_INTENT_DEPTH) -> list[Intent]:
        """Walk recent git commits and produce `Intent` records.

        Args:
            repo_path: Path to (or inside) a git repo. Searched upward.
            depth: How many of the most recent commits to inspect.

        Returns:
            List of `Intent` records. Empty if `gitpython` is not installed
            or the path is not in a git repo.
        """
        try:
            import git
        except ImportError:
            return []
        try:
            repo = git.Repo(repo_path, search_parent_directories=True)
        except Exception:
            return []
        intents: list[Intent] = []
        for commit in list(repo.iter_commits())[:depth]:
            # First line of the commit message drives the heuristic.
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
            try:
                # Diff against the parent commit; a_path = post-image path.
                # Swallow errors for the first commit (no parent) and merge commits.
                files_changed = [d.a_path for d in commit.diff(f"{commit.hexsha}~1")]
            except Exception:
                files_changed = []
            intents.append(
                Intent(
                    commit_hash=commit.hexsha,
                    author=str(commit.author),
                    timestamp=commit.committed_date,
                    message=commit.message,
                    files_changed=files_changed,
                    inferred_type=t,
                )
            )
        return intents
