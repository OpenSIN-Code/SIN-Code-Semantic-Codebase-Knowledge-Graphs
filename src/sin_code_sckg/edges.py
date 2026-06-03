"""Edge types for the knowledge graph.

Docs: edges.py.doc.md
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EdgeType(Enum):
    """Closed enum of relationship kinds recognized by the graph.

    The string values are stored on disk; do NOT rename them in place —
    add a new member and migrate old data instead.
    """
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    INHERITS = "INHERITS"
    CONTAINS = "CONTAINS"


@dataclass
class Edge:
    """Represents a directed relationship between two nodes.

    `source` and `target` are node IDs (see `nodes.Node.id`). `type` is
    one of the `EdgeType` enum values, serialized as its string form.
    """
    source: str
    target: str
    type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to a JSON-friendly dict."""
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Edge":
        """Reconstruct an `Edge` from its dict form.

        Raises `KeyError` if `source`, `target`, or `type` is missing.
        """
        return cls(
            source=data["source"],
            target=data["target"],
            type=data["type"],
            metadata=data.get("metadata", {}),
        )
