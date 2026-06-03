"""CLI for the SCKG (Semantic Codebase Knowledge Graph) daemon.

Docs: cli.py.doc.md
"""
from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml

from .graph import KnowledgeGraph

app = typer.Typer(help="SIN-Code Semantic Knowledge Graph CLI")


# Config file search order. CWD first, then .sin/ subdir. These are
# the two locations the agent-toolbox conventions expect.
_CONFIG_PATHS = (Path("config.yaml"), Path(".sin/config.yaml"))

# Hard-coded fallback so the CLI works out of the box on a fresh clone
# without requiring a config file.
_DEFAULT_CONFIG: dict = {
    "repository": {"root": ".", "exclude": []},
    "graph": {"storage": "./.sin/knowledge.graph", "include_intent": True},
}


def _load_config() -> dict:
    """Load YAML config from the first match in `_CONFIG_PATHS`.

    Returns `_DEFAULT_CONFIG` if no file is found.
    """
    for p in _CONFIG_PATHS:
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f)
    return _DEFAULT_CONFIG


@app.command()
def build(root: str = typer.Option(None, help="Repository root")):
    """Build the knowledge graph from a repository.

    Reads `repository.root` (or the `--root` flag) and writes the resulting
    graph to `graph.storage`. This is the only mutating subcommand.
    """
    cfg = _load_config()
    repo_root = root or cfg["repository"]["root"]
    exclude = cfg["repository"].get("exclude", [])
    storage = cfg["graph"]["storage"]
    typer.echo(f"[SCKG] Building graph from {repo_root}...")
    kg = KnowledgeGraph(storage_path=storage)
    stats = kg.build_from_repo(
        repo_root, exclude=exclude, include_intents=cfg["graph"].get("include_intent", True)
    )
    typer.echo(f"[SCKG] Done. Stats: {json.dumps(stats, indent=2)}")


@app.command()
def find(name: str):
    """Find symbols by name (substring + token search)."""
    cfg = _load_config()
    kg = KnowledgeGraph(storage_path=cfg["graph"]["storage"])
    typer.echo(json.dumps(kg.find_symbol(name), indent=2))


@app.command()
def impact(fqid: str):
    """Impact analysis for a symbol (blast radius / upstream + downstream)."""
    cfg = _load_config()
    kg = KnowledgeGraph(storage_path=cfg["graph"]["storage"])
    typer.echo(json.dumps(kg.impact_analysis(fqid), indent=2))


@app.command()
def arch():
    """Show architecture overview (hubs, edge counts, hotspots)."""
    cfg = _load_config()
    kg = KnowledgeGraph(storage_path=cfg["graph"]["storage"])
    typer.echo(json.dumps(kg.explain_architecture(), indent=2))


@app.command()
def serve():
    """Run as MCP server (stdio). Blocks until the client disconnects."""
    from .mcp_server import main
    main()


if __name__ == "__main__":
    app()
