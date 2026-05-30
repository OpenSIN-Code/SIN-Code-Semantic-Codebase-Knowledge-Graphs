"""MCP-Server für Agent-Integration."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    FastMCP = None

from .graph import KnowledgeGraph


def _load_graph() -> KnowledgeGraph:
    cfg_path = Path("config.yaml")
    cfg = {"graph": {"storage": "./.sin/knowledge.graph"}}
    if cfg_path.exists():
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f)
    return KnowledgeGraph(storage_path=cfg["graph"]["storage"])


def main():
    if FastMCP is None:
        raise RuntimeError("mcp package not installed")
    mcp = FastMCP("sin-code-sckg")

    @mcp.tool()
    def find_symbol(name: str) -> str:
        """Find a symbol in the codebase by name."""
        kg = _load_graph()
        return json.dumps(kg.find_symbol(name), indent=2)

    @mcp.tool()
    def impact_analysis(fqid: str) -> str:
        """Return blast-radius / impact analysis for a fully-qualified symbol id."""
        kg = _load_graph()
        return json.dumps(kg.impact_analysis(fqid), indent=2)

    @mcp.tool()
    def architecture_overview() -> str:
        """Return high-level architecture stats and hubs."""
        kg = _load_graph()
        return json.dumps(kg.explain_architecture(), indent=2)

    @mcp.tool()
    def downstream_deps(fqid: str) -> str:
        """Return downstream dependencies (what uses this symbol)."""
        kg = _load_graph()
        return json.dumps(kg.downstream(fqid))

    mcp.run()


def run_server(port: int = 8765):
    main()


if __name__ == "__main__":
    main()
