"""Main KnowledgeGraph API.

Docs: graph.py.doc.md
"""

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
        self._load()

    def _load(self) -> None:
        """Load persisted state if present."""
        data = self.storage.load()
        for node_data in data.get("nodes", {}).values():
            node = self._node_from_dict(node_data)
            if node:
                self.nodes[node.id] = node
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

    def add_node(self, node: Node) -> None:
        """Add or overwrite a node in the graph."""
        self.nodes[node.id] = node

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

    def query(self, text: str) -> list[Node]:
        """Search nodes by name or file path (case-insensitive)."""
        text_lower = text.lower()
        results = []
        for node in self.nodes.values():
            if text_lower in node.name.lower() or text_lower in node.file_path.lower():
                results.append(node)
        return results

    def save(self) -> None:
        """Persist the graph to storage_path."""
        self.storage.save(self.to_dict())
