"""Tests for KnowledgeGraph.

Docs: test_graph.py.doc.md
"""

import pytest
from pathlib import Path

from sin_code_sckg.graph import KnowledgeGraph
from sin_code_sckg.nodes import FileNode, FunctionNode, ClassNode
from sin_code_sckg.edges import Edge, EdgeType


class TestKnowledgeGraphInit:
    def test_creates_empty_graph_when_storage_missing(self, tmp_path):
        path = tmp_path / "missing.graph"
        kg = KnowledgeGraph(storage_path=path)
        assert kg.get_node("nope") is None
        assert kg.to_dict() == {"nodes": {}, "edges": []}

    def test_loads_existing_graph(self, tmp_path):
        path = tmp_path / "existing.graph"
        kg = KnowledgeGraph(path)
        kg.add_node(FileNode("f1", "a.py"))
        kg.add_edge(Edge("f1", "f2", EdgeType.CONTAINS.value))
        kg.save()

        kg2 = KnowledgeGraph(path)
        assert kg2.get_node("f1") is not None
        assert len(kg2.edges) == 1


class TestKnowledgeGraphAddAndGet:
    def test_add_node(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        node = FileNode("f1", "a.py")
        kg.add_node(node)
        assert kg.get_node("f1") == node

    def test_add_edge(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_edge(Edge("a", "b", EdgeType.IMPORTS.value))
        assert len(kg.edges) == 1

    def test_get_node_missing(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        assert kg.get_node("missing") is None


class TestKnowledgeGraphNeighbors:
    def test_get_neighbors(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("f1", "a.py"))
        kg.add_node(FunctionNode("fn1", "foo"))
        kg.add_edge(Edge("f1", "fn1", EdgeType.CONTAINS.value))
        neighbors = kg.get_neighbors("f1")
        assert len(neighbors) == 1
        assert neighbors[0].id == "fn1"

    def test_get_neighbors_with_edge_type(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("f1", "a.py"))
        kg.add_node(FunctionNode("fn1", "foo"))
        kg.add_node(ClassNode("c1", "Bar"))
        kg.add_edge(Edge("f1", "fn1", EdgeType.CONTAINS.value))
        kg.add_edge(Edge("f1", "c1", EdgeType.IMPORTS.value))
        assert len(kg.get_neighbors("f1", EdgeType.CONTAINS.value)) == 1
        assert len(kg.get_neighbors("f1", EdgeType.IMPORTS.value)) == 1

    def test_get_neighbors_no_match(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("f1", "a.py"))
        assert kg.get_neighbors("f1", EdgeType.CALLS.value) == []

    def test_get_neighbors_unknown_node(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        assert kg.get_neighbors("unknown") == []


class TestKnowledgeGraphPath:
    def test_find_path_direct(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("a", "a.py"))
        kg.add_node(FileNode("b", "b.py"))
        kg.add_edge(Edge("a", "b", EdgeType.IMPORTS.value))
        assert kg.find_path("a", "b") == ["a", "b"]

    def test_find_path_two_hops(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("a", "a.py"))
        kg.add_node(FileNode("b", "b.py"))
        kg.add_node(FileNode("c", "c.py"))
        kg.add_edge(Edge("a", "b", EdgeType.IMPORTS.value))
        kg.add_edge(Edge("b", "c", EdgeType.IMPORTS.value))
        assert kg.find_path("a", "c") == ["a", "b", "c"]

    def test_find_path_same_node(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("a", "a.py"))
        assert kg.find_path("a", "a") == ["a"]

    def test_find_path_no_path(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("a", "a.py"))
        kg.add_node(FileNode("b", "b.py"))
        assert kg.find_path("a", "b") == []

    def test_find_path_missing_source(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("b", "b.py"))
        assert kg.find_path("a", "b") == []

    def test_find_path_missing_target(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("a", "a.py"))
        assert kg.find_path("a", "b") == []


class TestKnowledgeGraphToDict:
    def test_roundtrip(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        kg.add_node(FileNode("f1", "a.py"))
        kg.add_edge(Edge("f1", "f2", EdgeType.CONTAINS.value))
        d = kg.to_dict()
        assert "nodes" in d
        assert "edges" in d
        assert d["nodes"]["f1"]["name"] == "a.py"
        assert d["edges"][0]["type"] == "CONTAINS"


class TestKnowledgeGraphSave:
    def test_save_creates_file(self, tmp_path):
        path = tmp_path / "kg.graph"
        kg = KnowledgeGraph(path)
        kg.add_node(FileNode("f1", "a.py"))
        kg.save()
        assert path.exists()

    def test_save_in_nested_dir(self, tmp_path):
        path = tmp_path / "deep" / "nested" / "kg.graph"
        kg = KnowledgeGraph(path)
        kg.add_node(FileNode("f1", "a.py"))
        kg.save()
        assert path.exists()


class TestKnowledgeGraphBuildFromRepo:
    def test_empty_repo(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats == {"files": 0, "functions": 0, "classes": 0, "edges": 0}

    def test_single_file(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("def foo(): pass\n")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["files"] == 1
        assert stats["functions"] == 1
        assert stats["classes"] == 0
        assert stats["edges"] > 0
        assert kg.get_node(f"file:a.py") is not None

    def test_multi_file(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("def foo(): pass\n")
        (repo / "b.py").write_text("class Bar: pass\n")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["files"] == 2
        assert stats["functions"] == 1
        assert stats["classes"] == 1

    def test_excludes_directories(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "main.py").write_text("def main(): pass\n")
        bad = repo / "node_modules"
        bad.mkdir()
        (bad / "bad.py").write_text("def bad(): pass\n")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["files"] == 1

    def test_skips_syntax_errors(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "good.py").write_text("def foo(): pass\n")
        (repo / "bad.py").write_text("def foo(:\n")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["files"] == 1

    def test_circular_imports(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("import b\n")
        (repo / "b.py").write_text("import a\n")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["files"] == 2

    def test_class_inheritance(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("class Base: pass\nclass Child(Base): pass\n")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["classes"] == 2

    def test_large_repo(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        for i in range(100):
            (repo / f"file_{i}.py").write_text(f"def func_{i}(): pass\nclass Class_{i}: pass\n")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["files"] == 100
        assert stats["functions"] == 100
        assert stats["classes"] == 100

    def test_persistence_after_build(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("def foo(): pass\n")
        path = tmp_path / "kg.graph"
        kg = KnowledgeGraph(path)
        kg.build_from_repo(repo)
        kg2 = KnowledgeGraph(path)
        assert kg2.get_node(f"file:a.py") is not None
