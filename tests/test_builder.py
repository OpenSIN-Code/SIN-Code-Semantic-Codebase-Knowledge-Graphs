"""Tests for GraphBuilder.

Docs: test_builder.py.doc.md
"""

import pytest
from pathlib import Path

from sin_code_sckg.builder import GraphBuilder


class TestGraphBuilder:
    def test_empty_repo(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["files"] == 0
        assert stats["functions"] == 0
        assert stats["classes"] == 0
        assert stats["edges"] == 0

    def test_single_file(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("def foo(): pass\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["files"] == 1
        assert stats["functions"] == 1
        assert stats["classes"] == 0

    def test_multi_file(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("def foo(): pass\n")
        (repo / "b.py").write_text("class Bar: pass\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
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
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["files"] == 1

    def test_skips_syntax_errors(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "good.py").write_text("def foo(): pass\n")
        (repo / "bad.py").write_text("def foo(:\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["files"] == 1

    def test_circular_imports(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("import b\n")
        (repo / "b.py").write_text("import a\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["files"] == 2

    def test_class_inheritance(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("class Base: pass\nclass Child(Base): pass\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["classes"] == 2

    def test_large_repo(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        for i in range(100):
            (repo / f"file_{i}.py").write_text(f"def func_{i}(): pass\nclass Class_{i}: pass\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["files"] == 100
        assert stats["functions"] == 100
        assert stats["classes"] == 100

    def test_methods_counted(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("class Bar:\n    def method(self): pass\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["functions"] == 1
        assert stats["classes"] == 1

    def test_async_functions(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("async def foo(): pass\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["functions"] == 1

    def test_imports(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("import os\nfrom pathlib import Path\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["files"] == 1
        assert any(e.type == "IMPORTS" for e in edges)

    def test_calls(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "a.py").write_text("def foo(): pass\ndef bar(): foo()\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert any(e.type == "CALLS" for e in edges)

    def test_custom_exclude(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "main.py").write_text("def main(): pass\n")
        custom = repo / "custom_skip"
        custom.mkdir()
        (custom / "skip.py").write_text("def skip(): pass\n")
        builder = GraphBuilder(exclude={"custom_skip"})
        nodes, edges, stats = builder.build(repo)
        assert stats["files"] == 1

    def test_nested_modules(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        pkg = repo / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("def init(): pass\n")
        builder = GraphBuilder()
        nodes, edges, stats = builder.build(repo)
        assert stats["files"] == 1
        assert any("module:pkg.__init__" in n.id for n in nodes)
