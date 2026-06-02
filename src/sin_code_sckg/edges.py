"""Edge types for the knowledge graph.

Docs: edges.py.doc.md
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EdgeType(Enum):
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    INHERITS = "INHERITS"
    CONTAINS = "CONTAINS"


@dataclass
class Edge:
    """Represents a directed relationship between two nodes."""
    source: str
    target: str
    type: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.type,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Edge":
        return cls(
            source=data["source"],
            target=data["target"],
            type=data["type"],
            metadata=data.get("metadata", {}),
        )
