# mcp_server.py

FastMCP server exposing the SCKG knowledge graph as MCP tools for agent use.

## What it does

Wraps the `KnowledgeGraph` API in a `FastMCP` server with four tools:
`find_symbol`, `impact_analysis`, `architecture_overview`, `downstream_deps`.
The server speaks the Model Context Protocol over stdio, so any MCP-compatible
agent (opencode, claude-code, etc.) can call the graph directly.

## Dependencies

- `graph.py` — `KnowledgeGraph` (used per-call, reloaded from storage)
- `graph.py` — `find_symbol`, `impact_analysis`, `explain_architecture`, `downstream`
- `mcp.server.fastmcp.FastMCP` — MCP server framework
- `pyyaml` — config loading

## Tools

| Tool | Returns | Description |
|------|---------|-------------|
| `find_symbol(name)` | JSON list of symbol matches | Search by symbol name |
| `impact_analysis(fqid)` | JSON blast-radius object | Upstream/downstream fanout |
| `architecture_overview()` | JSON architecture summary | Hubs, edge counts, hotspots |
| `downstream_deps(fqid)` | JSON list of dependents | Who uses this symbol |

## Architecture

`build_server()` is split from `main()` so the MCP instance can be unit-tested
without binding to stdio. Each tool call creates a fresh `KnowledgeGraph`
by loading from disk (graph is expected to be pre-built via CLI).

## Usage

```bash
sin-sckg serve            # direct invocation via CLI
# or
python -m sin_code_sckg.mcp_server
```

In opencode.json, configure the MCP server and the four tools become
available to agents.

## Known caveats

- The graph must be pre-built with `sin-sckg build` before `serve` returns
  useful data — `build_server()` does not auto-build.
- Each tool call reloads the graph from disk (no in-memory caching across calls).
- `fqid` is the format `kind:module.path:Name` (e.g. `func:app.api:handle_request`).
