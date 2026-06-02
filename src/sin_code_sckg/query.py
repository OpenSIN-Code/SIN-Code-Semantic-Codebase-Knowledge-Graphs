"""Graph traversal algorithms.

Docs: query.py.doc.md
"""

from collections import deque
from typing import Optional


class QueryEngine:
    """Provides traversal queries over the knowledge graph."""

    def __init__(self, nodes: dict, edges: list):
        self.nodes = nodes
        self.edges = edges
        self._adjacency: dict[str, list] | None = None
        self._build_adjacency()

    def _build_adjacency(self) -> None:
        """Build adjacency list from edges."""
        self._adjacency = {}
        for node_id in self.nodes:
            self._adjacency[node_id] = []
        for edge in self.edges:
            self._adjacency.setdefault(edge.source, []).append(edge)

    def get_neighbors(self, node_id: str, edge_type: str | None = None) -> list:
        """Return neighbor nodes reachable from node_id via outgoing edges.

        If edge_type is provided, only edges of that type are considered.
        """
        if node_id not in self._adjacency:
            return []
        neighbors = []
        for edge in self._adjacency[node_id]:
            if edge_type is None or edge.type == edge_type:
                if edge.target in self.nodes:
                    neighbors.append(self.nodes[edge.target])
        return neighbors

    def find_path(self, source_id: str, target_id: str) -> list[str]:
        """Find shortest path from source to target using BFS.

        Returns list of node IDs including source and target.
        Empty list if no path exists.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []
        if source_id == target_id:
            return [source_id]

        queue = deque([(source_id, [source_id])])
        visited = {source_id}

        while queue:
            current, path = queue.popleft()
            for edge in self._adjacency.get(current, []):
                neighbor = edge.target
                if neighbor not in visited:
                    if neighbor == target_id:
                        return path + [neighbor]
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return []
