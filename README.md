# SIN-Code Semantic Codebase Knowledge Graphs (SCKG)

State-of-the-Art Replacement for vector-database RAG in AI coding agents.

## Features
- Tree-sitter based AST parsing (Python, JS, TS)
- Git-history intent extraction
- NetworkX-based dependency graph with temporal edges
- Blast-radius impact analysis
- MCP-Server for agent integration
- CLI for human exploration

## Install
```bash
pip install -e .
```

## Usage
```bash
sckg build                  # build graph from current repo
sckg find <name>            # find symbol
sckg impact <fqid>          # blast radius
sckg arch                   # architecture overview
sckg serve                  # start MCP server
```

## MCP Integration
Add to your OpenCode/Codex MCP config:
```yaml
mcpServers:
  sckg:
    command: sckg
    args: [serve]
```
