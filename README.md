# SIN-Code-Semantic-Codebase-Knowledge-Graphs (SCKG)

Semantic codebase knowledge graph for the SIN-Code stack. Extracts AST-based
code intelligence from Python repositories and exposes a graph API for
navigation, querying, and persistence.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from sin_code_sckg.graph import KnowledgeGraph

kg = KnowledgeGraph(storage_path="/path/to/knowledge.graph")
stats = kg.build_from_repo(
    "/path/to/repo",
    exclude={"node_modules", ".venv", ".git", "dist", "build"}
)
print(stats)
# {'files': 42, 'functions': 318, 'classes': 27, 'edges': 412}

# Query the graph
node = kg.get_node("file:main.py")
neighbors = kg.get_neighbors("file:main.py", edge_type="IMPORTS")
path = kg.find_path("file:main.py", "class:module:utils:Helper")
```

## API

- `KnowledgeGraph(storage_path)` — load or create a graph
- `build_from_repo(repo, exclude)` — parse a Python repo
- `add_node(node)` / `add_edge(edge)` — manual construction
- `get_node(id)` — lookup by ID
- `get_neighbors(node_id, edge_type)` — outgoing neighbors
- `find_path(source, target)` — BFS shortest path
- `save()` / `to_dict()` — persistence

## Development

```bash
pytest
```

## License

MIT
