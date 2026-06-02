# query.py

Graph traversal algorithms.

## What it does

Provides `QueryEngine` with BFS-based path finding and neighbor lookup.

## API

| Method | Purpose |
|--------|---------|
| `get_neighbors(node_id, edge_type)` | Outgoing neighbors (filtered) |
| `find_path(source_id, target_id)` | Shortest path via BFS |

## Performance

- BFS is `O(V + E)` for path finding.
- Adjacency list is rebuilt on each `QueryEngine` instantiation.

## Known caveats

- `find_path` returns the first shortest path found, not all paths.
- Cycles are handled via visited set.
