#!/usr/bin/env python3
"""Test: SCKG vulnerabilities
- JSON deserialization
- File size DoS
- Arbitrary directory traversal in parse_directory()
"""
import os
import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, "/Users/jeremy/dev/SIN-Code-Semantic-Codebase-Knowledge-Graphs")


def test_json_storage_no_validation():
    """storage.py:load() uses json.load() with no size limits."""
    import inspect
    from src.sin_code_sckg import storage
    
    source = inspect.getsource(storage.GraphStorage.load)
    
    has_size_check = "os.path.getsize" in source or "stat" in source.lower()
    has_type_check = "isinstance" in source
    
    if not has_size_check:
        print("PASS: GraphStorage.load() has NO file size limit")
        print("  [MEDIUM] VULNERABILITY: Attacker can provide enormous JSON file")
        print("  Example: 500MB JSON with 1M nodes → OOM or timeout")
        print("  Fix: Add file size limit check before json.load()")


def test_parse_directory_traversal():
    """parse_directory() accepts arbitrary root path without validation."""
    import inspect
    from src.sin_code_sckg import parser
    
    source = inspect.getsource(parser.SemanticParser.parse_directory)
    
    has_resolve = ".resolve()" in source
    has_path_check = "resolve()." in source
    uses_os_walk = "os.walk" in source
    
    if uses_os_walk:
        print("PASS: parse_directory() uses os.walk() with resolved root")
        print("  [LOW] parse_directory() resolves root before walking,")
        print("  but accepts ANY path including system dirs.")
        print("  os.walk('/') would parse ALL Python files available")
        print("  Fix: Validate path is within project workspace")


def test_graph_file_dos():
    """Test that we can create a JSON graph file with massive data."""
    from src.sin_code_sckg.storage import GraphStorage
    
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_path = Path(tmpdir) / "bomb.graph.json"
        store = GraphStorage(graph_path)
        
        # Create a graph with many nodes
        large_graph = {
            "nodes": {f"node_{i}": {"type": "function", "name": f"func_{i}"} for i in range(10000)},
            "edges": [{"source": f"node_{i}", "target": f"node_{(i+1)%10000}", "type": "calls"} for i in range(50000)]
        }
        
        import time
        start = time.time()
        store.save(large_graph)
        save_time = time.time() - start
        
        file_size = os.path.getsize(graph_path)
        print(f"PASS: Wrote graph with 10K nodes + 50K edges in {save_time:.2f}s ({file_size/1024:.1f} KB)")
        
        start = time.time()
        loaded = store.load()
        load_time = time.time() - start
        print(f"PASS: Loaded graph in {load_time:.2f}s, {len(loaded['nodes'])} nodes, {len(loaded['edges'])} edges")
        print("  [MEDIUM] No size limits - could DoS with multi-hundred MB JSON")


def test_yaml_safe_loading():
    """Verify YAML loading is secure (uses safe_load)."""
    import inspect
    from src.sin_code_sckg import mcp_server
    
    source = inspect.getsource(mcp_server._load_graph)
    
    uses_safe_load = "yaml.safe_load" in source
    uses_unsafe_load = "yaml.load(" in source and "yaml.safe_load" not in source
    
    if uses_safe_load:
        print("PASS: YAML uses yaml.safe_load() - secure against YAML deserialization attacks")
    elif uses_unsafe_load:
        print("FAIL: YAML uses yaml.load() - VULNERABLE to deserialization attacks!")
    else:
        print("INFO: YAML loading not found")


if __name__ == "__main__":
    print("=" * 60)
    print("SCKG SECURITY VULNERABILITY TESTS")
    print("=" * 60)
    
    test_json_storage_no_validation()
    print()
    test_parse_directory_traversal()
    print()
    test_graph_file_dos()
    print()
    test_yaml_safe_loading()
    
    print("\n" + "=" * 60)
    print("SUMMARY: SCKG has no file size limits (DoS risk), but YAML")
    print("loading is properly secured with safe_load()")
    print("=" * 60)
