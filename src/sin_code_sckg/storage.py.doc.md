# storage.py

JSON persistence layer.

## What it does

Saves and loads the knowledge graph as JSON. Creates missing directories
automatically.

## API

| Method | Purpose |
|--------|---------|
| `save(data)` | Write JSON to disk |
| `load()` | Read JSON from disk; returns empty graph if missing |

## File format

```json
{
  "nodes": {"id": {...}},
  "edges": [{"source": "...", "target": "...", "type": "..."}]
}
```

## Notes

- `.graph` or `.json` extension both work.
- Uses `utf-8` encoding.
- Missing files return empty graph (no crash).
