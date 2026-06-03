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


class KnowledgeGraph:
    """In-memory knowledge graph with persistence and traversal."""

    def __init__(self, storage_path: str | Path):
        """Load existing graph or create empty one."""
        self.storage_path = Path(storage_path)
        self.storage = GraphStorage(self.storage_path)
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self._inverted_index: dict[str, set[str]] = defaultdict(set)
        self._load()

    def _load(self) -> None:
        """Load persisted state if present and rebuild inverted index."""
        data = self.storage.load()
        for node_data in data.get("nodes", {}).values():
            node = self._node_from_dict(node_data)
            if node:
                self.nodes[node.id] = node
                self._index_node(node)
        for edge_data in data.get("edges", []):
            self.edges.append(Edge.from_dict(edge_data))

    def _node_from_dict(self, data: dict) -> Node | None:
        """Reconstruct a node from its serialized dict."""
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
        """
        lower = text.lower()
        tokens: set[str] = set()
        # Full word tokens (includes underscores, e.g. helper_0)
        for token in re.findall(r"\b[a-z_][a-z0-9_]*\b", lower):
            tokens.add(token)
            # Also index sub-components split by underscore
            for part in token.split("_"):
                if len(part) >= 2:
                    tokens.add(part)
        # Path / dot components (e.g. module_0.py -> module_0, py, module, 0)
        for token in re.findall(r"[a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)*", lower):
            for part in re.split(r"[_.]", token):
                if len(part) >= 2:
                    tokens.add(part.lower())
        return tokens

    def _index_node(self, node: Node) -> None:
        """Add a node to the inverted index."""
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
            score += 10.0
        elif query_lower in name_lower:
            score += 5.0
        if query_lower in file_lower:
            score += 1.0
        return score

    def add_node(self, node: Node) -> None:
        """Add or overwrite a node in the graph and update the inverted index."""
        self.nodes[node.id] = node
        self._index_node(node)

    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)

    def get_node(self, id: str) -> Node | None:
        """Retrieve a node by its ID."""
        return self.nodes.get(id)

    def get_neighbors(self, node_id: str, edge_type: str | None = None) -> list[Node]:
        """Return neighbors of a node via outgoing edges."""
        engine = QueryEngine(self.nodes, self.edges)
        return engine.get_neighbors(node_id, edge_type)

    def find_path(self, source_id: str, target_id: str) -> list[str]:
        """Find shortest path between two node IDs."""
        engine = QueryEngine(self.nodes, self.edges)
        return engine.find_path(source_id, target_id)

    def build_from_repo(self, repo: str | Path, exclude: set[str] | None = None) -> dict[str, Any]:
        """Build graph from a code repository.

        Returns stats dict like: {"files": 42, "functions": 318, "classes": 27, "edges": 412}
        """
        builder = GraphBuilder(exclude=exclude)
        nodes, edges, stats = builder.build(repo)
        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self.add_edge(edge)
        self.save()
        return stats

    def to_dict(self) -> dict[str, Any]:
        """Serialize the graph to a dictionary."""
        return {
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "edges": [edge.to_dict() for edge in self.edges],
        }

    def query(self, text: str, limit: int = 10) -> list[Node]:
        """Search nodes by name or file path using an inverted index (case-insensitive).

        Uses AND semantics across query tokens. Results are ranked by relevance.
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
                    candidate_ids &= self._inverted_index[token]
            else:
                return []

        if not candidate_ids:
            return []

        query_lower = text.lower()
        # Use heapq.nlargest for O(m log limit) instead of O(m log m) sort
        import heapq
        results = []
        for node_id in candidate_ids:
            node = self.nodes[node_id]
            score = self._query_score(node, query_lower)
            results.append((score, node))

        top = heapq.nlargest(limit, results, key=lambda x: x[0])
        return [r[1] for r in top]

    def save(self) -> None:
        """Persist the graph to storage_path."""
        self.storage.save(self.to_dict())
