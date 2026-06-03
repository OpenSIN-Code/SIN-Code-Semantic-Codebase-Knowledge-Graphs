"""Graph traversal algorithms.

Docs: query.py.doc.md
"""

from collections import deque
from typing import Optional


class QueryEngine:
    """Provides traversal queries over the knowledge graph.

    PERFORMANCE FIX: Uses pre-built indexes for O(1) lookups:
    - _adjacency: node_id -> list of edges (for graph traversal)
    - _adjacency_by_type: node_id -> edge_type -> list of edges
    - _neighbor_index: node_id -> set of neighbor_ids (for fast neighbor checks)
    - _edge_index: edge_type -> list of edges (for fast edge filtering)

    These indexes are built once during __init__ and make queries
    on 10000+ nodes run in milliseconds instead of seconds.
    """

    def __init__(self, nodes: dict, edges: list):
        self.nodes = nodes
        self.edges = edges
        self._adjacency: dict[str, list] = {}
        self._adjacency_by_type: dict[str, dict[str, list]] = {}
        self._neighbor_index: dict[str, set[str]] = {}
        self._edge_index: dict[str, list] = {}
        self._build_indexes()

    def _build_indexes(self) -> None:
        """Build all lookup indexes for O(1) query performance.

        This is the key performance optimization: instead of scanning
        all edges for every query, we pre-build indexes that allow
        direct lookups.
        """
        # Initialize adjacency for all nodes
        for node_id in self.nodes:
            self._adjacency[node_id] = []
            self._adjacency_by_type[node_id] = {}
            self._neighbor_index[node_id] = set()

        # Build indexes in a single pass
        for edge in self.edges:
            source = edge.source
            target = edge.target
            edge_type = edge.type

            # Skip orphan edges whose source or target don't exist in nodes
            if source not in self.nodes or target not in self.nodes:
                continue

            # Adjacency list (outgoing edges only)
            self._adjacency.setdefault(source, []).append(edge)

            # Adjacency by type (outgoing edges only)
            adj_types = self._adjacency_by_type.setdefault(source, {})
            if edge_type not in adj_types:
                adj_types[edge_type] = []
            adj_types[edge_type].append(edge)

            # Neighbor index (outgoing neighbors only for directed graphs)
            # For directed graphs like import relationships, we only follow
            # the direction of the edge (source -> target).
            self._neighbor_index.setdefault(source, set()).add(target)

            # Edge index by type
            if edge_type not in self._edge_index:
                self._edge_index[edge_type] = []
            self._edge_index[edge_type].append(edge)

    def get_neighbors(self, node_id: str, edge_type: str | None = None) -> list:
        """Return neighbor nodes reachable from node_id via outgoing edges.

        If edge_type is provided, only edges of that type are considered.
        PERFORMANCE: O(1) lookup using pre-built indexes.
        """
        if node_id not in self._adjacency:
            return []

        # Use type-specific index if edge_type is provided
        if edge_type is not None:
            edges = self._adjacency_by_type.get(node_id, {}).get(edge_type, [])
        else:
            edges = self._adjacency.get(node_id, [])

        # Pre-filter valid targets to avoid repeated dict lookups
        nodes = self.nodes
        return [nodes[edge.target] for edge in edges if edge.target in nodes]

    def find_path(self, source_id: str, target_id: str) -> list[str]:
        """Find shortest path from source to target using BFS.

        Returns list of node IDs including source and target.
        Empty list if no path exists.
        PERFORMANCE: Uses neighbor index for O(1) neighbor checks.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return []
        if source_id == target_id:
            # If a self-edge exists, return 1-hop path; otherwise just the node
            if source_id in self._neighbor_index.get(source_id, set()):
                return [source_id, target_id]
            return [source_id]

        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        neighbor_index = self._neighbor_index

        while queue:
            current, path = queue.popleft()
            # O(1) neighbor lookup using pre-built index
            for neighbor in neighbor_index.get(current, set()):
                if neighbor not in visited:
                    if neighbor == target_id:
                        return path + [neighbor]
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return []
