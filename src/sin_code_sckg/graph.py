"""NetworkX-basierter Knowledge Graph mit temporalen Kanten."""
from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

import networkx as nx

from .parser import SemanticParser, Symbol, Intent


class KnowledgeGraph:
    """Persistenter semantischer Knowledge Graph."""

    def __init__(self, storage_path: str | None = None):
        self.graph = nx.MultiDiGraph()
        self.storage_path = storage_path
        if storage_path and os.path.exists(storage_path):
            self.load(storage_path)

    def build_from_repo(
        self,
        repo_root: str,
        exclude: list[str] | None = None,
        include_intents: bool = True,
        intent_depth: int = 50,
    ) -> dict:
        exclude = exclude or []
        parser = SemanticParser()
        stats = {"symbols": 0, "edges": 0, "intents": 0}

        # 1. Symbole parsen und als Nodes einfügen
        symbols_by_fqid: dict[str, Symbol] = {}
        for sym in parser.parse_directory(repo_root, exclude):
            self.graph.add_node(
                sym.fqid,
                name=sym.name,
                kind=sym.kind,
                file=sym.file,
                line_start=sym.line_start,
                line_end=sym.line_end,
                docstring=sym.docstring,
            )
            symbols_by_fqid[sym.fqid] = sym
            stats["symbols"] += 1

        # 2. Namens-Index für Call-Resolution
        name_index: dict[str, list[str]] = {}
        for fqid, sym in symbols_by_fqid.items():
            name_index.setdefault(sym.name, []).append(fqid)

        # 3. Call-Edges
        for fqid, sym in symbols_by_fqid.items():
            for call in sym.calls:
                targets = name_index.get(call, [])
                for t in targets:
                    if t != fqid:
                        self.graph.add_edge(fqid, t, kind="calls")
                        stats["edges"] += 1

        # 4. File-Containment-Edges
        for fqid, sym in symbols_by_fqid.items():
            self.graph.add_edge(sym.file, fqid, kind="contains")

        # 5. Git-Intents
        if include_intents:
            intents = parser.parse_intents(repo_root, intent_depth)
            for intent in intents:
                inode = f"intent:{intent.commit_hash}"
                self.graph.add_node(
                    inode,
                    kind="intent",
                    author=intent.author,
                    timestamp=intent.timestamp,
                    message=intent.message,
                    inferred_type=intent.inferred_type,
                )
                for f in intent.files_changed:
                    if self.graph.has_node(f):
                        self.graph.add_edge(inode, f, kind="touches")
                stats["intents"] += 1

        if self.storage_path:
            self.save(self.storage_path)
        return stats

    # ---------- Querying ----------
    def find_symbol(self, name: str) -> list[dict]:
        results = []
        for node, data in self.graph.nodes(data=True):
            if data.get("name") == name:
                results.append({"id": node, **data})
        return results

    def upstream(self, fqid: str, depth: int = 3) -> list[str]:
        """Was hängt von diesem Symbol ab?"""
        if not self.graph.has_node(fqid):
            return []
        try:
            return list(
                nx.ancestors(self.graph.reverse(), fqid)
            )
        except Exception:
            return []

    def downstream(self, fqid: str, depth: int = 3) -> list[str]:
        """Was nutzt dieses Symbol?"""
        if not self.graph.has_node(fqid):
            return []
        try:
            return list(nx.descendants(self.graph, fqid))
        except Exception:
            return []

    def impact_analysis(self, fqid: str) -> dict:
        """SOTA-Feature: Blast-Radius-Analyse."""
        if not self.graph.has_node(fqid):
            return {"error": "Symbol not found"}
        down = self.downstream(fqid)
        up = self.upstream(fqid)
        files_affected = {
            self.graph.nodes[n].get("file")
            for n in down
            if self.graph.nodes[n].get("file")
        }
        return {
            "symbol": fqid,
            "upstream_count": len(up),
            "downstream_count": len(down),
            "files_affected": list(files_affected),
            "risk_score": min(1.0, len(down) / 50.0),
        }

    def explain_architecture(self, top_k: int = 10) -> dict:
        """Top-Hubs und kritische Pfade."""
        if len(self.graph) == 0:
            return {}
        try:
            deg = sorted(
                self.graph.out_degree(),
                key=lambda x: x[1],
                reverse=True,
            )[:top_k]
            return {
                "total_nodes": len(self.graph),
                "total_edges": self.graph.number_of_edges(),
                "hubs": [
                    {
                        "id": n,
                        "out_degree": d,
                        "kind": self.graph.nodes[n].get("kind"),
                        "name": self.graph.nodes[n].get("name"),
                    }
                    for n, d in deg
                ],
            }
        except Exception as e:
            return {"error": str(e)}

    # ---------- Persistence ----------
    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        data = nx.node_link_data(self.graph)
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, path: str) -> None:
        with open(path) as f:
            data = json.load(f)
        self.graph = nx.node_link_graph(data)
