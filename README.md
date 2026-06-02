# SIN-Code Semantic Codebase Knowledge Graphs (SCKG)

> Semantic codebase knowledge graph for the SIN-Code stack. Extracts AST-based code intelligence from Python repositories and exposes a graph API for navigation, querying, and persistence.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

Part of the [SIN-Code](https://github.com/OpenSIN-Code) agent-engineering stack. Install all subsystems together via the [SIN-Code Bundle](https://github.com/OpenSIN-Code/SIN-Code-Bundle).

## Features

- **AST-based extraction** — parse Python repos into files, functions, classes, and modules
- **Graph persistence** — save and load knowledge graphs to disk
- **Query engine** — lookup nodes, traverse neighbors, and find shortest paths
- **Impact analysis** — blast-radius analysis for any symbol (what depends on this?)
- **Architecture overview** — detect hubs, orphans, and structural hotspots
- **MCP server** — expose graph tools to AI agents via the Model Context Protocol

## Installation

```bash
pip install -e .
```

Optional MCP server support:
```bash
pip install -e ".[mcp]"
```

See [INSTALL.md](./INSTALL.md) for detailed setup instructions.

## Usage

### Library

```python
from sin_code_sckg.graph import KnowledgeGraph

kg = KnowledgeGraph(storage_path="./knowledge.graph")
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

### CLI

```bash
# Build graph from current repo
sckg build

# Find a symbol
sckg find my_function

# Impact analysis
sckg impact "file:main.py"

# Architecture overview
sckg arch

# Run MCP server
sckg serve
```

## Testing

```bash
pytest
```

## MCP Server

Run the MCP server for agent integration:

```bash
# With the CLI
sckg serve

# Or directly
python -m sin_code_sckg.mcp_server
```

Tools exposed:
- `find_symbol(name)` — find a symbol in the codebase
- `impact_analysis(fqid)` — blast-radius / impact analysis
- `architecture_overview()` — high-level architecture stats and hubs
- `downstream_deps(fqid)` — downstream dependencies (what uses this symbol)

## Integration

SCKG is designed to work as part of the SIN-Code ecosystem:

- **SIN-Code Bundle** — orchestrates all subsystems from a single CLI (`sin`)
- **Intent-Based Diffing (IBD)** — consume graph data to enrich semantic diffs
- **Architectural Debt Watchdogs (ADW)** — feed graph metrics into debt scoring
- **Verification Oracle** — cross-reference graph symbols with verification results

## License

MIT — see [LICENSE](./LICENSE).
