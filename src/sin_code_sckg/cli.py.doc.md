# cli.py

Typer-based CLI for the SCKG (Semantic Codebase Knowledge Graph) tool.

## What it does

Provides user-facing commands to build a knowledge graph from a repository,
query symbols, run impact analysis, and start the MCP server. Wraps
`KnowledgeGraph` and `mcp_server` behind a `typer.Typer` app.

## Dependencies

- `graph.py` — `KnowledgeGraph` (build / find / impact / arch operations)
- `mcp_server.py` — `main()` (launched via `serve` subcommand)
- `typer` — CLI framework
- `pyyaml` — config file loading

## Config loading

`_load_config()` searches for `config.yaml` in CWD first, then `.sin/config.yaml`.
If neither exists, sensible defaults are used:

```yaml
repository:
  root: .
  exclude: []
graph:
  storage: ./.sin/knowledge.graph
  include_intent: true
```

## Subcommands

| Command | Args | Description |
|---------|------|-------------|
| `build` | `--root PATH` | Build knowledge graph from a repo |
| `find` | `NAME` | Find symbols by name |
| `impact` | `FQID` | Blast-radius analysis for a symbol |
| `arch` | — | Show architecture hubs and edges |
| `serve` | — | Run as MCP server (stdio) |

## Usage

```bash
sin-sckg build --root ~/dev/myproject
sin-sckg find MyClass
sin-sckg impact "module:myproj.core:MyClass"
sin-sckg arch
sin-sckg serve
```

## Known caveats

- Config loading uses CWD — invoke from project root.
- All commands reload the graph from storage; `build` is the only mutator.
- `serve` blocks the process (FastMCP stdio transport).
