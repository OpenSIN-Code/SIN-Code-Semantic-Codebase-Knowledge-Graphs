"""Node types for the knowledge graph.

Docs: nodes.py.doc.md
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """Base class for all graph nodes.

    Subclasses set `type` to a discriminator string so the storage layer
    can round-trip the right class on `from_dict`. All construction goes
    through keyword args to keep call sites readable.
    """
    id: str
    type: str
    name: str
    file_path: str = ""
    line_number: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to a JSON-friendly dict.

        Order matches the on-disk format used by `GraphStorage`.
        """
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        """Reconstruct a node from its dict form.

        Top-level keys are reserved; everything else is merged into
        `metadata` to allow forward-compat with new fields.
        """
        meta = data.get("metadata", {})
        return cls(
            id=data["id"],
            name=data["name"],
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            **meta,
        )


@dataclass
class FileNode(Node):
    """Represents a source file in the repository (one per `.py` file)."""
    def __init__(self, id: str, name: str, file_path: str = "", line_number: int = 0, **extra):
        # `extra` is the bucket for future per-file fields (e.g. hash, size).
        meta = extra.pop("metadata", None)
        super().__init__(id=id, type="FileNode", name=name, file_path=file_path,
                         line_number=line_number, metadata=meta if meta is not None else extra)


@dataclass
class FunctionNode(Node):
    """Represents a function or method definition (including `async def`)."""
    def __init__(self, id: str, name: str, file_path: str = "", line_number: int = 0, **extra):
        meta = extra.pop("metadata", None)
        super().__init__(id=id, type="FunctionNode", name=name, file_path=file_path,
                         line_number=line_number, metadata=meta if meta is not None else extra)


@dataclass
class ClassNode(Node):
    """Represents a class definition (its methods are separate `FunctionNode`s)."""
    def __init__(self, id: str, name: str, file_path: str = "", line_number: int = 0, **extra):
        meta = extra.pop("metadata", None)
        super().__init__(id=id, type="ClassNode", name=name, file_path=file_path,
                         line_number=line_number, metadata=meta if meta is not None else extra)


@dataclass
class ModuleNode(Node):
    """Represents a Python module (typically a file mapped to a dotted module name)."""
    def __init__(self, id: str, name: str, file_path: str = "", line_number: int = 0, **extra):
        meta = extra.pop("metadata", None)
        super().__init__(id=id, type="ModuleNode", name=name, file_path=file_path,
                         line_number=line_number, metadata=meta if meta is not None else extra)
