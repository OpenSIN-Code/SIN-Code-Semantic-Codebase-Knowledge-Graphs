"""CLI für den SCKG Daemon."""
from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml

from .graph import KnowledgeGraph

app = typer.Typer(help="SIN-Code Semantic Knowledge Graph CLI")


def _load_config() -> dict:
    for p in (Path("config.yaml"), Path(".sin/config.yaml")):
        if p.exists():
            with open(p) as f:
                return yaml.safe_load(f)
    return {"repository": {"root": ".", "exclude": []}, "graph": {"storage": "./.sin/knowledge.graph"}}


@app.command()
def build(
    root: str = typer.Option(None, help="Repository root"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
):
    """Build the knowledge graph from a repository."""
    cfg = _load_config()
    repo_root = root or cfg["repository"]["root"]
    exclude = cfg["repository"]["exclude"]
    storage = cfg["graph"]["storage"]

    typer.echo(f"[SCKG] Building graph from {repo_root}...")
    kg = KnowledgeGraph(storage_path=storage)
    stats = kg.build_from_repo(
        repo_root, exclude=exclude, include_intents=cfg["graph"].get("include_intent", True)
    )
    typer.echo(f"[SCKG] Done. Stats: {json.dumps(stats, indent=2)}")


@app.command()
def find(name: str):
    """Find symbols by name."""
    cfg = _load_config()
    kg = KnowledgeGraph(storage_path=cfg["graph"]["storage"])
    results = kg.find_symbol(name)
    typer.echo(json.dumps(results, indent=2))


@app.command()
def impact(fqid: str):
    """Impact analysis for a symbol (SOTA blast radius)."""
    cfg = _load_config()
    kg = KnowledgeGraph(storage_path=cfg["graph"]["storage"])
    typer.echo(json.dumps(kg.impact_analysis(fqid), indent=2))


@app.command()
def arch():
    """Show architecture overview (hubs, edges)."""
    cfg = _load_config()
    kg = KnowledgeGraph(storage_path=cfg["graph"]["storage"])
    typer.echo(json.dumps(kg.explain_architecture(), indent=2))


@app.command()
def serve(port: int = typer.Option(8765, help="MCP server port")):
    """Run as MCP server."""
    from .mcp_server import run_server
    run_server(port=port)


if __name__ == "__main__":
    app()
