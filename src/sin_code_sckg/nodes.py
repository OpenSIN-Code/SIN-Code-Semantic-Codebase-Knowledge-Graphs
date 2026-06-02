"""Node types for the knowledge graph.

Docs: nodes.py.doc.md
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Node:
    """Base class for all graph nodes."""
    id: str
    type: str
    name: str
    file_path: str = ""
    line_number: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
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
        return cls(
            id=data["id"],
            type=data["type"],
            name=data["name"],
            file_path=data.get("file_path", ""),
            line_number=data.get("line_number", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FileNode(Node):
    """Represents a source file in the repository."""
    def __init__(self, id: str, name: str, file_path: str = "", line_number: int = 0, **metadata):
        super().__init__(id=id, type="FileNode", name=name, file_path=file_path, line_number=line_number, metadata=metadata)


@dataclass
class FunctionNode(Node):
    """Represents a function or method definition."""
    def __init__(self, id: str, name: str, file_path: str = "", line_number: int = 0, **metadata):
        super().__init__(id=id, type="FunctionNode", name=name, file_path=file_path, line_number=line_number, metadata=metadata)


@dataclass
class ClassNode(Node):
    """Represents a class definition."""
    def __init__(self, id: str, name: str, file_path: str = "", line_number: int = 0, **metadata):
        super().__init__(id=id, type="ClassNode", name=name, file_path=file_path, line_number=line_number, metadata=metadata)


@dataclass
class ModuleNode(Node):
    """Represents a Python module (typically a file mapped to module name)."""
    def __init__(self, id: str, name: str, file_path: str = "", line_number: int = 0, **metadata):
        super().__init__(id=id, type="ModuleNode", name=name, file_path=file_path, line_number=line_number, metadata=metadata)
