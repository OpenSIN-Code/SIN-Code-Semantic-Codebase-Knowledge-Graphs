# nodes.py

Node dataclasses for the knowledge graph.

## What it does

Defines all node types used in the graph: `FileNode`, `FunctionNode`,
`ClassNode`, and `ModuleNode`.

## Base fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique identifier (used in edges) |
| `type` | `str` | Node class name |
| `name` | `str` | Human-readable name |
| `file_path` | `str` | Absolute path to source file |
| `line_number` | `int` | Definition line |
| `metadata` | `dict` | Optional extra data |

## Serialization

- `to_dict()` → plain `dict` for JSON
- `from_dict(data)` → reconstruct node

## Extending

Subclass `Node` and set `type` in the constructor to add new node kinds.
