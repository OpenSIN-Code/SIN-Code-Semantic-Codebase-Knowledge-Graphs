"""Tests for storage layer.

Docs: test_storage.py.doc.md
"""

import pytest
from pathlib import Path

from sin_code_sckg.storage import GraphStorage


class TestGraphStorage:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "data.graph"
        storage = GraphStorage(path)
        data = {"nodes": {"n1": {"id": "n1", "type": "FileNode", "name": "a.py"}}, "edges": []}
        storage.save(data)
        loaded = storage.load()
        assert loaded == data

    def test_load_missing_file(self, tmp_path):
        path = tmp_path / "missing.graph"
        storage = GraphStorage(path)
        loaded = storage.load()
        assert loaded == {"nodes": {}, "edges": []}

    def test_save_creates_directories(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "data.graph"
        storage = GraphStorage(path)
        storage.save({"nodes": {}, "edges": []})
        assert path.exists()

    def test_save_json_format(self, tmp_path):
        path = tmp_path / "data.json"
        storage = GraphStorage(path)
        data = {"nodes": {}, "edges": [{"source": "a", "target": "b", "type": "IMPORTS"}]}
        storage.save(data)
        text = path.read_text()
        assert "IMPORTS" in text
