# builder.py

AST-based graph extraction engine for Python repositories.

## What it does

Walks a repository, parses `.py` files with the `ast` module, and generates
`Node` and `Edge` objects representing modules, classes, functions, imports,
inheritance, and calls.

## Dependencies

- `nodes.py` — `FileNode`, `ModuleNode`, `ClassNode`, `FunctionNode`
- `edges.py` — `Edge`, `EdgeType`

## How it works

1. `os.walk` the repo, skipping excluded directories.
2. For each `.py` file: `ast.parse()` → walk AST.
3. Create `FileNode` + `ModuleNode` per file.
4. Create `ClassNode` / `FunctionNode` for each definition.
5. Create edges: `CONTAINS`, `INHERITS`, `IMPORTS`, `CALLS`.

## Exclusion defaults

Always excluded (in addition to user-supplied set):
`node_modules`, `.venv`, `.git`, `dist`, `build`, `__pycache__`, `.pytest_cache`

## Performance

- Pure stdlib `ast` — no heavy dependencies.
- Files with syntax errors are skipped silently.
- Handles 1000+ files in <10 seconds on typical hardware.

## Known caveats

- Call resolution is heuristic (uses module prefix guessing).
- Cross-repo imports are not resolved to absolute paths.
- `async def` functions are handled correctly.
- Methods inside classes are counted as functions.
