# edges.py

Edge dataclass and edge type enum.

## What it does

Defines `Edge` (directed relationship) and `EdgeType` (enum of supported
relationship types).

## Edge types

| Type | Meaning |
|------|---------|
| `IMPORTS` | Module imports another module |
| `CALLS` | Function calls another function |
| `INHERITS` | Class inherits from base class |
| `CONTAINS` | Parent (file/module/class) contains child |

## Serialization

- `to_dict()` → plain `dict`
- `from_dict(data)` → reconstruct edge

## Usage

```python
from sin_code_sckg.edges import Edge, EdgeType
edge = Edge(source="a", target="b", type=EdgeType.IMPORTS.value)
```
