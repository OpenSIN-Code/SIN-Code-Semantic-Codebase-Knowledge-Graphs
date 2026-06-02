#!/usr/bin/env python3
"""SCKG Pilot Evaluation Framework.

Measures:
- Time saved: How much faster is graph-based vs file-based search?
- Accuracy: How relevant are the graph results?
- Maintenance cost: How long to build/update the graph?
"""

import time
import json
from pathlib import Path
from sin_code_sckg.graph import KnowledgeGraph


def measure_build_time(repo_path: str) -> dict:
    """Measure how long it takes to build the graph."""
    start = time.time()
    kg = KnowledgeGraph(storage_path="/tmp/pilot.graph")
    stats = kg.build_from_repo(repo_path)
    duration = time.time() - start
    
    return {
        "repo": repo_path,
        "files": stats.get("files", 0),
        "functions": stats.get("functions", 0),
        "build_time_seconds": duration,
        "files_per_second": stats.get("files", 0) / max(duration, 0.001)
    }


def measure_query_time(kg: KnowledgeGraph, query: str) -> dict:
    """Measure how long a query takes."""
    start = time.time()
    results = kg.query(query)  # or whatever query method exists
    duration = time.time() - start
    
    return {
        "query": query,
        "time_seconds": duration,
        "results_count": len(results)
    }


def compare_with_grep(repo_path: str, query: str) -> dict:
    """Compare graph query vs grep search."""
    import subprocess
    
    # Graph query
    kg = KnowledgeGraph(storage_path="/tmp/pilot.graph")
    kg.build_from_repo(repo_path)
    
    start = time.time()
    graph_results = kg.query(query)
    graph_time = time.time() - start
    
    # Grep search
    start = time.time()
    grep_results = subprocess.run(
        ["grep", "-r", query, repo_path],
        capture_output=True, text=True
    )
    grep_time = time.time() - start
    
    return {
        "query": query,
        "graph_time": graph_time,
        "grep_time": grep_time,
        "speedup": grep_time / max(graph_time, 0.001),
        "graph_results": len(graph_results),
        "grep_results": len(grep_results.stdout.split("\n"))
    }


def run_pilot(repo_path: str = ".") -> dict:
    """Run full pilot evaluation."""
    print(f"SCKG Pilot Evaluation: {repo_path}")
    print("=" * 50)
    
    # Build time
    build = measure_build_time(repo_path)
    print(f"Build time: {build['build_time_seconds']:.2f}s for {build['files']} files")
    
    # Query benchmarks
    queries = [
        "auth",
        "database",
        "API",
        "test"
    ]
    
    query_results = []
    for query in queries:
        result = measure_query_time(KnowledgeGraph(storage_path="/tmp/pilot.graph"), query)
        query_results.append(result)
        print(f"Query '{query}': {result['time_seconds']:.4f}s, {result['results_count']} results")
    
    # Comparison
    if build['files'] > 0:
        compare = compare_with_grep(repo_path, "func")
        print(f"\nGraph vs Grep speedup: {compare['speedup']:.2f}x")
    
    return {
        "build": build,
        "queries": query_results,
        "comparison": compare if build['files'] > 0 else None
    }


if __name__ == "__main__":
    import sys
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    results = run_pilot(repo)
    
    # Save results
    output = Path("sckg-pilot-results.json")
    output.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to {output}")
