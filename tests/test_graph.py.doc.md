# test_graph.py

Tests for `KnowledgeGraph` class.

## Coverage

- Initialization (empty / existing)
- Add/get nodes and edges
- Neighbor queries (with/without edge type)
- Path finding (direct, multi-hop, cycles, missing)
- Persistence (save/load)
- `build_from_repo` (empty, single, multi, excludes, syntax errors, circular,
  inheritance, large repo)

## Notes

Uses `tmp_path` pytest fixture for filesystem isolation.
