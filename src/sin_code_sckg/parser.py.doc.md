# parser.py

Tree-sitter-based multilingual semantic parser plus git-intent extractor.

## What it does

Parses Python, JavaScript, and TypeScript source files into `Symbol` records
(functions, classes, methods) using `tree-sitter` grammars. Optionally walks
the git history of a repo to produce `Intent` records (refactor / feature /
fix / docs) from commit messages.

## Dependencies

- `tree_sitter` — parser runtime
- `tree_sitter_python`, `tree_sitter_javascript`, `tree_sitter_typescript` — grammars
- `gitpython` (optional) — used by `parse_intents`; absence is non-fatal

## Public API

| Symbol | Purpose |
|--------|---------|
| `Symbol` | Dataclass holding parsed symbol info (name, kind, file, lines, body, calls, decorators, docstring) |
| `Intent` | Dataclass holding a commit-derived intent (hash, author, message, files, inferred type) |
| `SemanticParser` | Main parser class; `parse_file`, `parse_directory`, `parse_intents` |
| `SemanticParser.available` | True if at least one language loaded successfully |

## Language support

| Language | Extensions |
|----------|------------|
| Python | `.py` |
| JavaScript | `.js`, `.jsx` |
| TypeScript | `.ts`, `.tsx` |

A `Symbol` produced by Python parsing carries extra fields (decorators,
docstring) that JS/TS parsing leaves empty.

## Usage

```python
from sin_code_sckg.parser import SemanticParser
parser = SemanticParser()
for sym in parser.parse_directory("~/dev/myproject", exclude=["tests", "build"]):
    print(sym.fqid, sym.kind, sym.line_start, sym.line_end)
```

## Known caveats

- The tree-sitter API shifted between 0.22 and 0.23+ — `_build_parser` handles
  both `Parser(language)` and `Parser() + set_language(language)` constructors.
- Missing tree-sitter language packages degrade silently (printed as `[WARN]`).
- `parse_directory` enforces that the root lives under `$HOME`; paths outside
  raise `ValueError` to avoid path-traversal accidents.
- `parse_intents` infers intent from commit-message prefixes — non-conventional
  messages fall into the `other` bucket.
