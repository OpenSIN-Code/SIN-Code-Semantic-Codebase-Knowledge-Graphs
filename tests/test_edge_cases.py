"""Edge-case tests for KnowledgeGraph — bugs NOT covered by existing tests.

Docs: test_edge_cases.doc.md
"""

import pytest
import time
from pathlib import Path

from sin_code_sckg.graph import KnowledgeGraph
from sin_code_sckg.nodes import FileNode, FunctionNode, ClassNode, Node
from sin_code_sckg.edges import Edge, EdgeType


class TestEmptyAndSingleGraph:
    """Edge cases: empty graph, single node."""

    def test_empty_graph_operations(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "empty.graph")
        assert kg.get_neighbors("nonexistent") == []
        assert kg.find_path("a", "b") == []
        assert kg.query("anything") == []
        assert kg.to_dict() == {"nodes": {}, "edges": []}

    def test_single_node_all_operations(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "single.graph")
        kg.add_node(FileNode("only", "single.py"))
        assert kg.get_node("only") is not None
        assert kg.get_neighbors("only") == []
        assert kg.find_path("only", "only") == ["only"]
        assert kg.find_path("only", "missing") == []
        assert kg.find_path("missing", "only") == []
        results = kg.query("single")
        assert len(results) == 1
        assert results[0].id == "only"


class TestDuplicateNodesAndEdges:
    """Edge cases: duplicate IDs, duplicate edges, self-edges."""

    def test_duplicate_node_id_overwrites(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "dup.graph")
        n1 = FileNode("same_id", "first.py")
        n2 = FileNode("same_id", "second.py")
        kg.add_node(n1)
        kg.add_node(n2)
        node = kg.get_node("same_id")
        assert node is not None
        assert node.name == "second.py"  # overwritten

    def test_duplicate_edges_accumulated(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "dup_edges.graph")
        kg.add_node(FileNode("a", "a.py"))
        kg.add_node(FileNode("b", "b.py"))
        kg.add_edge(Edge("a", "b", EdgeType.CALLS.value))
        kg.add_edge(Edge("a", "b", EdgeType.CALLS.value))
        assert len(kg.edges) == 2  # edges are accumulated, not deduplicated

    def test_self_edge(self, tmp_path):
        """Self-referencing edge (node importing itself)."""
        kg = KnowledgeGraph(tmp_path / "self.graph")
        kg.add_node(FileNode("self", "self.py"))
        kg.add_edge(Edge("self", "self", EdgeType.CALLS.value))
        neighbors = kg.get_neighbors("self")
        assert len(neighbors) == 1
        assert neighbors[0].id == "self"
        path = kg.find_path("self", "self")
        assert path == ["self", "self"]


class TestInvalidEdges:
    """Edge cases: edges to missing nodes."""

    def test_edge_source_missing(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "missing_src.graph")
        kg.add_node(FileNode("target", "t.py"))
        kg.add_edge(Edge("missing_source", "target", EdgeType.IMPORTS.value))
        # get_neighbors on the existing node should still work for outbound edges
        neighbors = kg.get_neighbors("missing_source")
        assert neighbors == []  # node doesn't exist, so no neighbors

    def test_edge_target_missing(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "missing_tgt.graph")
        kg.add_node(FileNode("source", "s.py"))
        kg.add_edge(Edge("source", "missing_target", EdgeType.IMPORTS.value))
        neighbors = kg.get_neighbors("source")
        # Edge exists but target node not in graph
        # Behavior depends on implementation
        assert isinstance(neighbors, list)

    def test_edge_both_missing(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "both_missing.graph")
        kg.add_edge(Edge("ghost_a", "ghost_b", EdgeType.CALLS.value))
        assert kg.get_neighbors("ghost_a") == []


class TestCircularDependencies:
    """Edge cases: circular paths and back-edges."""

    def test_circular_two_nodes(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "circle2.graph")
        kg.add_node(FileNode("a", "a.py"))
        kg.add_node(FileNode("b", "b.py"))
        kg.add_edge(Edge("a", "b", EdgeType.CALLS.value))
        kg.add_edge(Edge("b", "a", EdgeType.CALLS.value))
        # find_path should find the shortest path
        path = kg.find_path("a", "b")
        assert path == ["a", "b"]
        # path back should also work
        path2 = kg.find_path("b", "a")
        assert path2 == ["b", "a"]

    def test_circular_three_nodes(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "circle3.graph")
        kg.add_node(FileNode("a", "a.py"))
        kg.add_node(FileNode("b", "b.py"))
        kg.add_node(FileNode("c", "c.py"))
        kg.add_edge(Edge("a", "b", EdgeType.CALLS.value))
        kg.add_edge(Edge("b", "c", EdgeType.CALLS.value))
        kg.add_edge(Edge("c", "a", EdgeType.CALLS.value))
        assert kg.find_path("a", "c") == ["a", "b", "c"]
        assert kg.find_path("c", "a") == ["c", "a"]
        assert kg.find_path("c", "b") == ["c", "a", "b"]


class TestEdgeTypes:
    """Edge cases: non-existent edge types, invalid edge types."""

    def test_filter_by_nonexistent_edge_type(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "filter.graph")
        kg.add_node(FileNode("a", "a.py"))
        kg.add_node(FileNode("b", "b.py"))
        kg.add_edge(Edge("a", "b", EdgeType.CALLS.value))
        neighbors = kg.get_neighbors("a", "NONEXISTENT_TYPE")
        assert neighbors == []

    def test_edge_with_arbitrary_string_type(self, tmp_path):
        """Edges can have arbitrary strings, not just EdgeType enum values."""
        kg = KnowledgeGraph(tmp_path / "custom.graph")
        kg.add_node(FileNode("a", "a.py"))
        kg.add_node(FileNode("b", "b.py"))
        kg.add_edge(Edge("a", "b", "MY_CUSTOM_TYPE"))
        neighbors = kg.get_neighbors("a", "MY_CUSTOM_TYPE")
        assert len(neighbors) == 1

    def test_edge_with_empty_type(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "empty_type.graph")
        kg.add_node(FileNode("a", "a.py"))
        kg.add_node(FileNode("b", "b.py"))
        kg.add_edge(Edge("a", "b", ""))
        neighbors = kg.get_neighbors("a", "")
        assert len(neighbors) == 1


class TestUnicodeNodeNames:
    """Edge cases: Unicode identifiers."""

    def test_unicode_node_name(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "unicode.graph")
        kg.add_node(FileNode("u1", "日本語ファイル.py"))
        kg.add_node(FunctionNode("fn1", "こんにちは関数"))
        node = kg.get_node("fn1")
        assert node is not None
        assert node.name == "こんにちは関数"
        results = kg.query("こんにちは")
        assert len(results) >= 1

    def test_unicode_with_emoji(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "emoji.graph")
        kg.add_node(FunctionNode("em1", "🔥handler🔥"))
        node = kg.get_node("em1")
        assert node.name == "🔥handler🔥"
        results = kg.query("handler")
        assert len(results) >= 1

    def test_right_to_left_unicode(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "rtl.graph")
        kg.add_node(FileNode("rtl", "مرحبا.py"))
        node = kg.get_node("rtl")
        assert node.name == "مرحبا.py"


class TestQueryEdgeCases:
    """Edge cases: query with empty string, negative limit, special chars."""

    def test_query_empty_string(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "empty_query.graph")
        kg.add_node(FileNode("a", "a.py"))
        results = kg.query("")
        assert results == []

    def test_query_whitespace_only(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "ws.graph")
        kg.add_node(FileNode("a", "a.py"))
        results = kg.query("   ")
        assert results == []

    def test_query_special_regex_chars(self, tmp_path):
        """Query should treat input as literal text, not regex."""
        kg = KnowledgeGraph(tmp_path / "regex.graph")
        kg.add_node(FunctionNode("test", "test_func"))
        results = kg.query("(test")
        assert isinstance(results, list)

    def test_query_with_limit_zero(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "limit0.graph")
        for i in range(5):
            kg.add_node(FunctionNode(f"f{i}", f"func_{i}"))
        results = kg.query("func", limit=0)
        assert len(results) == 0

    def test_query_with_large_limit(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "big_limit.graph")
        kg.add_node(FunctionNode("f1", "func"))
        results = kg.query("func", limit=9999)
        assert len(results) == 1

    def test_query_no_match(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "no_match.graph")
        kg.add_node(FileNode("a", "a.py"))
        results = kg.query("zzz_nonexistent_xxx")
        assert results == []


class TestNodeEdgeCases:
    """Edge cases: node with no edges, node with empty name, node serialization."""

    def test_node_with_no_edges_in_large_graph(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "isolated.graph")
        for i in range(10):
            kg.add_node(FunctionNode(f"f{i}", f"connected_{i}"))
        kg.add_node(FunctionNode("isolated", "lonely_func"))
        for i in range(9):
            kg.add_edge(Edge(f"f{i}", f"f{i+1}", EdgeType.CALLS.value))
        assert kg.get_neighbors("isolated") == []

    def test_node_empty_name(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "empty_name.graph")
        kg.add_node(FileNode("e1", ""))
        node = kg.get_node("e1")
        assert node is not None
        assert node.name == ""

    def test_node_with_very_long_name(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "long.graph")
        long_name = "x" * 1000
        kg.add_node(FunctionNode("ln", long_name))
        node = kg.get_node("ln")
        assert node.name == long_name

    def test_node_empty_id(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "empty_id.graph")
        kg.add_node(FileNode("", "empty_id.py"))
        assert kg.get_node("") is not None

    def test_node_roundtrip_with_metadata(self, tmp_path):
        kg = KnowledgeGraph(tmp_path / "meta.graph")
        node = FunctionNode("m1", "func", metadata={"key": "value", "nested": {"a": 1}})
        kg.add_node(node)
        kg.save()
        kg2 = KnowledgeGraph(tmp_path / "meta.graph")
        loaded = kg2.get_node("m1")
        assert loaded is not None
        assert loaded.metadata == {"key": "value", "nested": {"a": 1}}


class TestBuildFromRepoEdgeCases:
    """Edge cases: build_from_repo with edge-case repos."""

    def test_build_empty_file(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "empty.py").write_text("")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["files"] == 1
        assert stats["functions"] == 0

    def test_build_only_comments(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "comments.py").write_text("# This is a comment\n# Another comment\n")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["files"] == 1
        assert stats["functions"] == 0

    def test_build_with_custom_exclude(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("def foo(): pass\n")
        bad = repo / "custom_exclude"
        bad.mkdir()
        (bad / "b.py").write_text("def bad(): pass\n")
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo, exclude={"custom_exclude"})
        assert stats["files"] == 1

    def test_build_large_file_with_many_functions(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        code = "\n".join([f"def func_{i}(): pass" for i in range(500)])
        (repo / "big.py").write_text(code)
        kg = KnowledgeGraph(tmp_path / "kg.graph")
        stats = kg.build_from_repo(repo)
        assert stats["functions"] == 500


class TestSaveAndLoadEdgeCases:
    """Edge cases: save/load with special paths, corrupted data."""

    def test_save_with_special_chars_in_path(self, tmp_path):
        special_dir = tmp_path / "sub dir" / "with spaces" / "special!@#"
        path = special_dir / "kg.graph"
        kg = KnowledgeGraph(path)
        kg.add_node(FileNode("f1", "a.py"))
        kg.save()
        assert path.exists()

    def test_save_empty_graph(self, tmp_path):
        path = tmp_path / "empty_save.graph"
        kg = KnowledgeGraph(path)
        kg.save()
        assert path.exists()
        kg2 = KnowledgeGraph(path)
        assert kg2.to_dict() == {"nodes": {}, "edges": []}

    def test_multiple_saves_idempotent(self, tmp_path):
        path = tmp_path / "multi_save.graph"
        kg = KnowledgeGraph(path)
        kg.add_node(FileNode("a", "a.py"))
        kg.save()
        kg.save()
        kg.save()
        kg2 = KnowledgeGraph(path)
        assert kg2.get_node("a") is not None
        assert len(kg2.nodes) == 1
