"""MCP server for agent integration.

Docs: mcp_server.py.doc.md
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

from .graph import KnowledgeGraph


# Default storage location when no config.yaml is present. Mirrors the
# default in `cli.py` so the MCP server works out of the box.
_DEFAULT_STORAGE = "./.sin/knowledge.graph"


def _load_graph() -> KnowledgeGraph:
    """Construct a `KnowledgeGraph` from the on-disk config.

    Each MCP tool call uses a freshly-loaded graph so the agent always
    sees the latest state (the file may have been rebuilt between calls).
    """
    cfg = {"graph": {"storage": _DEFAULT_STORAGE}}
    cfg_path = Path("config.yaml")
    if cfg_path.exists():
        with open(cfg_path) as f:
            cfg = yaml.safe_load(f)
    return KnowledgeGraph(storage_path=cfg["graph"]["storage"])


def build_server():
    """Create the FastMCP instance without starting it (testable).

    The split between `build_server` and `main` allows the tools to be
    unit-tested in isolation without binding to stdio.

    Returns:
        A configured `FastMCP` instance ready to `.run()`.
    """
    # Local import: keeps `mcp` optional so non-agent users don't need it.
    from mcp.server.fastmcp import FastMCP

    mcp = FastMCP("sin-code-sckg")

    @mcp.tool()
    def find_symbol(name: str) -> str:
        """Find a symbol in the codebase by name.

        Args:
            name: Substring or token to search for (case-insensitive).

        Returns:
            JSON-encoded list of matching symbols.
        """
        return json.dumps(_load_graph().find_symbol(name), indent=2)

    @mcp.tool()
    def impact_analysis(fqid: str) -> str:
        """Return blast-radius / impact analysis for a fully-qualified symbol id.

        Args:
            fqid: Fully-qualified ID, e.g. `func:app.api:handle_request`.

        Returns:
            JSON object with upstream callers, downstream callees, and depth info.
        """
        return json.dumps(_load_graph().impact_analysis(fqid), indent=2)

    @mcp.tool()
    def architecture_overview() -> str:
        """Return high-level architecture stats and hubs (most-connected nodes)."""
        return json.dumps(_load_graph().explain_architecture(), indent=2)

    @mcp.tool()
    def downstream_deps(fqid: str) -> str:
        """Return downstream dependencies (what uses this symbol)."""
        return json.dumps(_load_graph().downstream(fqid))

    return mcp


def main():
    """Build the server and run it on stdio (blocks until disconnect)."""
    build_server().run()


if __name__ == "__main__":
    main()
