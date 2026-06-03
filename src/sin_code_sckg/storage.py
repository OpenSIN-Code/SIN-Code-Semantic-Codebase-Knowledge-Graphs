"""Graph persistence layer.

Docs: storage.py.doc.md
"""

import json
import os
from pathlib import Path
from typing import Any


class GraphStorage:
    """Handles JSON persistence for the knowledge graph."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def save(self, data: dict[str, Any]) -> None:
        """Save graph data to JSON."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def load(self) -> dict[str, Any]:
        """Load graph data from JSON."""
        max_size = 500 * 1024 * 1024  # 500MB
        if self.path.exists():
            if os.path.getsize(self.path) > max_size:
                raise ValueError("Graph file too large")
        else:
            return {"nodes": {}, "edges": []}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)
