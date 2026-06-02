# test_storage.py

Tests for `GraphStorage`.

## Coverage

- Save and load roundtrip
- Missing file returns empty graph
- Directory creation
- JSON format verification

## Notes

Uses `tmp_path` pytest fixture for filesystem isolation.
