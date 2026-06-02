"""Tests for query engine.

Docs: test_query.py.doc.md
"""

import pytest

from sin_code_sckg.query import QueryEngine
from sin_code_sckg.nodes import FileNode, FunctionNode
from sin_code_sckg.edges import Edge, EdgeType


class TestQueryEngine:
    def test_get_neighbors(self):
        nodes = {
            "a": FileNode("a", "a.py"),
            "b": FunctionNode("b", "foo"),
        }
        edges = [Edge("a", "b", EdgeType.CONTAINS.value)]
        engine = QueryEngine(nodes, edges)
        neighbors = engine.get_neighbors("a")
        assert len(neighbors) == 1
        assert neighbors[0].id == "b"

    def test_get_neighbors_with_type(self):
        nodes = {
            "a": FileNode("a", "a.py"),
            "b": FunctionNode("b", "foo"),
            "c": FileNode("c", "c.py"),
        }
        edges = [
            Edge("a", "b", EdgeType.CONTAINS.value),
            Edge("a", "c", EdgeType.IMPORTS.value),
        ]
        engine = QueryEngine(nodes, edges)
        assert len(engine.get_neighbors("a", EdgeType.CONTAINS.value)) == 1
        assert len(engine.get_neighbors("a", EdgeType.IMPORTS.value)) == 1
        assert len(engine.get_neighbors("a", EdgeType.CALLS.value)) == 0

    def test_get_neighbors_unknown_node(self):
        engine = QueryEngine({}, [])
        assert engine.get_neighbors("x") == []

    def test_find_path_direct(self):
        nodes = {"a": FileNode("a", "a.py"), "b": FileNode("b", "b.py")}
        edges = [Edge("a", "b", EdgeType.IMPORTS.value)]
        engine = QueryEngine(nodes, edges)
        assert engine.find_path("a", "b") == ["a", "b"]

    def test_find_path_two_hops(self):
        nodes = {
            "a": FileNode("a", "a.py"),
            "b": FileNode("b", "b.py"),
            "c": FileNode("c", "c.py"),
        }
        edges = [
            Edge("a", "b", EdgeType.IMPORTS.value),
            Edge("b", "c", EdgeType.IMPORTS.value),
        ]
        engine = QueryEngine(nodes, edges)
        assert engine.find_path("a", "c") == ["a", "b", "c"]

    def test_find_path_same_node(self):
        nodes = {"a": FileNode("a", "a.py")}
        edges = []
        engine = QueryEngine(nodes, edges)
        assert engine.find_path("a", "a") == ["a"]

    def test_find_path_no_path(self):
        nodes = {"a": FileNode("a", "a.py"), "b": FileNode("b", "b.py")}
        edges = []
        engine = QueryEngine(nodes, edges)
        assert engine.find_path("a", "b") == []

    def test_find_path_missing_source(self):
        nodes = {"b": FileNode("b", "b.py")}
        edges = []
        engine = QueryEngine(nodes, edges)
        assert engine.find_path("a", "b") == []

    def test_find_path_missing_target(self):
        nodes = {"a": FileNode("a", "a.py")}
        edges = []
        engine = QueryEngine(nodes, edges)
        assert engine.find_path("a", "b") == []

    def test_find_path_cycle(self):
        nodes = {
            "a": FileNode("a", "a.py"),
            "b": FileNode("b", "b.py"),
            "c": FileNode("c", "c.py"),
        }
        edges = [
            Edge("a", "b", EdgeType.IMPORTS.value),
            Edge("b", "c", EdgeType.IMPORTS.value),
            Edge("c", "a", EdgeType.IMPORTS.value),
        ]
        engine = QueryEngine(nodes, edges)
        assert engine.find_path("a", "c") == ["a", "b", "c"]
