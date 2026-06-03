"""Main KnowledgeGraph API.

Docs: graph.py.doc.md
"""

import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .builder import GraphBuilder
from .nodes import Node, FileNode, FunctionNode, ClassNode, ModuleNode
from .edges import Edge
from .query import QueryEngine
from .storage import GraphStorage


# Scoring weights for `KnowledgeGraph._query_score`. Higher = stronger match.
# Tuned empirically; tweak together with `query()` callers, not in isolation.
_SCORE_EXACT = 10.0   # full lowercase equality on node name
_SCORE_SUBSTR = 5.0   # substring of query in node name
_SCORE_FILE = 1.0     # substring of query in file_path

# Minimum length of a sub-component token to keep (filters 0/1-char noise
# from splitting names like "foo_bar" -> "foo", "bar").
_MIN_TOKEN_LEN = 2


class KnowledgeGraph:
    """In-memory knowledge graph with persistence and traversal.

    Combines node storage, an inverted text index for search, a query
    engine for graph traversal, and JSON persistence. One instance is
    safe to reuse for many reads but the persistence layer rewrites the
    whole file on each `save()`.
    """

    def __init__(self, storage_path: str | Path):
        """Load existing graph from disk or create an empty one.

        Args:
            storage_path: Path to the `.graph` / `.json` file. Missing
                files are treated as empty graphs.
        """
        self.storage_path = Path(storage_path)
        self.storage = GraphStorage(self.storage_path)
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self._inverted_index: dict[str, set[str]] = defaultdict(set)
        self._load()

    def _load(self) -> None:
        """Load persisted state if present and rebuild the inverted index."""
        data = self.storage.load()
        for node_data in data.get("nodes", {}).values():
            node = self._node_from_dict(node_data)
            if node:
                self.nodes[node.id] = node
                self._index_node(node)
        for edge_data in data.get("edges", []):
            self.edges.append(Edge.from_dict(edge_data))

    def _node_from_dict(self, data: dict) -> Node | None:
        """Reconstruct a node from its serialized dict.

        Returns None for unknown node types or any other parse error
        (a partial graph from an older version is still loadable).
        """
        type_map = {
            "FileNode": FileNode,
            "FunctionNode": FunctionNode,
            "ClassNode": ClassNode,
            "ModuleNode": ModuleNode,
        }
        cls = type_map.get(data.get("type"), Node)
        try:
            return cls.from_dict(data)
        except Exception:
            return None

    def _tokenize(self, text: str) -> set[str]:
        """Extract lowercase word tokens from text.

        Generates both full word tokens and sub-components split by
        underscores / path separators so that "helper" matches "helper_0".
        Also captures Unicode/CJK runs so that こんにちは is searchable.
        """
        lower = text.lower()
        tokens: set[str] = set()
        # Full word tokens (includes underscores, e.g. helper_0)
        for token in re.findall(r"\b[a-z_][a-z0-9_]*\b", lower):
            tokens.add(token)
            # Also index sub-components split by underscore
            for part in token.split("_"):
                if len(part) >= _MIN_TOKEN_LEN:
                    tokens.add(part)
        # Path / dot components (e.g. module_0.py -> module_0, py, module, 0)
        for token in re.findall(r"[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*", lower):
            for part in re.split(r"[_.]", token):
                if len(part) >= _MIN_TOKEN_LEN:
                    tokens.add(part.lower())
        # Unicode / CJK runs (e.g. こんにちは, 日本語, مرحبا)
        # Also add length-2+ prefixes so "こんにちは" matches "こんにちは関数"
        for token in re.findall(r'[^\x00-\x7F\s_.\-]+', lower):
            for i in range(_MIN_TOKEN_LEN, len(token) + 1):
                tokens.add(token[:i])
        return tokens

    def _index_node(self, node: Node) -> None:
        """Add a node to the inverted index using its name + file_path."""
        tokens = self._tokenize(node.name + " " + node.file_path)
        for token in tokens:
            self._inverted_index[token].add(node.id)

    def _query_score(self, node: Node, query_lower: str) -> float:
        """Score relevance of a node against a query string.

        Higher is better. Prefers exact name matches over file path matches.
        """
        name_lower = node.name.lower()
        file_lower = node.file_path.lower()
        score = 0.0
        # Exact match bonus
        if query_lower == name_lower:
            score += _SCORE_EXACT
        elif query_lower in name_lower:
            score += _SCORE_SUBSTR
        if query_lower in file_lower:
            score += _SCORE_FILE
        return score

    def add_node(self, node: Node) -> None:
        """Add or overwrite a node in the graph and update the inverted index."""
        self.nodes[node.id] = node
        self._index_node(node)

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph (no dedup)."""
        self.edges.append(edge)

    def get_node(self, id: str) -> Node | None:
        """Retrieve a node by its ID, or None if missing."""
        return self.nodes.get(id)

    def get_neighbors(self, node_id: str, edge_type: str | None = None) -> list[Node]:
        """Return neighbors of a node via outgoing edges.

        Args:
            node_id: Source node ID.
            edge_type: Optional filter; only edges of this type are followed.
        """
        engine = QueryEngine(self.nodes, self.edges)
        return engine.get_neighbors(node_id, edge_type)

    def find_path(self, source_id: str, target_id: str) -> list[str]:
        """Find shortest path between two node IDs (BFS)."""
        engine = QueryEngine(self.nodes, self.edges)
        return engine.find_path(source_id, target_id)

    def build_from_repo(self, repo: str | Path, exclude: set[str] | None = None) -> dict[str, Any]:
        """Build graph from a code repository and persist.

        Args:
            repo: Repository root path.
            exclude: Optional set of directory names to skip during walk.

        Returns:
            Stats dict like: `{"files": 42, "functions": 318, "classes": 27, "edges": 412}`.
        """
        builder = GraphBuilder(exclude=exclude)
        nodes, edges, stats = builder.build(repo)
        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self.add_edge(edge)
        # Persist immediately so a crash mid-build leaves a partial graph on disk
        # rather than an empty one in memory.
        self.save()
        return stats

    def to_dict(self) -> dict[str, Any]:
        """Serialize the full graph to a JSON-friendly dict."""
        return {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
        }

    def query(self, text: str, limit: int = 10) -> list[Node]:
        """Search nodes by name or file path using an inverted index.

        Case-insensitive AND search across the query tokens. Results are
        ranked by `_query_score` and capped at `limit`.

        Args:
            text: Free-form query (e.g. "handle request").
            limit: Maximum number of results to return.

        Returns:
            List of matching `Node`s, ordered by descending relevance.
        """
        tokens = self._tokenize(text)
        if not tokens:
            return []

        candidate_ids = None
        for token in tokens:
            if token in self._inverted_index:
                if candidate_ids is None:
                    candidate_ids = self._inverted_index[token].copy()
                else:
                    # AND across tokens: a node must contain every token.
                    candidate_ids &= self._inverted_index[token]
            else:
                # Missing any token means no result (AND semantics).
                return []

        if not candidate_ids:
            return []

        query_lower = text.lower()
        # Use heapq.nlargest for O(m log limit) instead of O(m log m) sort.
        # Lazy import keeps the module top-level import graph lean.
        import heapq
        results = []
        for node_id in candidate_ids:
            node = self.nodes[node_id]
            score = self._query_score(node, query_lower)
            results.append((score, node))

        top = heapq.nlargest(limit, results, key=lambda x: x[0])
        return [r[1] for r in top]

    def save(self) -> None:
        """Persist the graph to `storage_path` (overwrites the file)."""
        self.storage.save(self.to_dict())
