# test_query.py

Tests for `QueryEngine`.

## Coverage

- Neighbor lookup (all, filtered by type)
- Unknown node returns empty list
- Path finding (direct, two hops, same node, no path, missing nodes)
- Cycle handling

## Notes

Uses `tmp_path` pytest fixture for filesystem isolation.
