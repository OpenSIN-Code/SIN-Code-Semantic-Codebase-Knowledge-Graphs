# graph.py

Main `KnowledgeGraph` API for the SIN-Code semantic codebase knowledge graph.

## What it does

Provides the primary entry point for building, querying, and persisting a
knowledge graph extracted from Python source repositories.

## Dependencies

- `builder.py` — `GraphBuilder` for AST extraction
- `nodes.py` — node dataclasses
- `edges.py` — edge dataclass
- `query.py` — `QueryEngine` for traversal
- `storage.py` — `GraphStorage` for JSON persistence

## Public API

| Method | Purpose |
|--------|---------|
| `__init__(storage_path)` | Load existing graph or create empty |
| `build_from_repo(repo, exclude)` | Parse repo with AST, populate graph |
| `add_node(node)` / `add_edge(edge)` | Manual graph construction |
| `get_node(id)` | Lookup node by ID |
| `get_neighbors(node_id, edge_type)` | Outgoing neighbors (filtered by type) |
| `find_path(source, target)` | BFS shortest path |
| `to_dict()` / `save()` | Serialization and persistence |

## Usage example

```python
kg = KnowledgeGraph("knowledge.graph")
stats = kg.build_from_repo("~/dev/myproject")
print(stats)
```

## Known caveats

- `save()` overwrites the storage file completely (no incremental append).
- `find_path` uses BFS and returns the first shortest path found.
