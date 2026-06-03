"""Graph persistence layer.

Docs: storage.py.doc.md
"""

import json
import os
from pathlib import Path
from typing import Any


# Cap on graph file size. 500MB protects against accidentally loading a
# runaway serialized graph (e.g. if a future change introduces a cycle).
# At ~1KB/node, that supports ~500k nodes which is well past any practical use.
_MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


class GraphStorage:
    """Handles JSON persistence for the knowledge graph.

    Write/append is not supported: every `save` rewrites the file in full.
    This is intentionally simple — the graph is small enough that a full
    rewrite on every checkpoint is cheaper than maintaining an append log.
    """

    def __init__(self, path: str | Path):
        """Store the target path; does not touch the filesystem yet.

        Args:
            path: Destination `.graph` or `.json` file. Parent directories
                are created on `save`, not on construction.
        """
        self.path = Path(path)

    def save(self, data: dict[str, Any]) -> None:
        """Save graph data to JSON.

        Creates parent directories as needed. The `default=str` makes
        non-JSON-native types (e.g. `datetime`) serialize as their `str`
        representation rather than crashing.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def load(self) -> dict[str, Any]:
        """Load graph data from JSON.

        Returns:
            The deserialized graph dict, or an empty `{"nodes": {}, "edges": []}`
            skeleton if the file does not exist.

        Raises:
            ValueError: If the file exists but is larger than `_MAX_FILE_SIZE`.
                This is a guard against pathological files.
        """
        if self.path.exists():
            if os.path.getsize(self.path) > _MAX_FILE_SIZE:
                raise ValueError("Graph file too large")
        else:
            return {"nodes": {}, "edges": []}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)
