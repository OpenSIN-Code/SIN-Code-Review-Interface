# `__init__.py` — Public Package API

What this file does: re-exports the public symbols of `sin_code_review_interface` so users can do `from sin_code_review_interface import ReviewServer, Decision, ...`.

## Dependency map

- Imports: `.server` (ReviewServer, get_app), `.decision` (Decision), `.diff` (SemanticDiff), `.comment` (Comment, Thread)
- Imported by: external user code, the CLI, the MCP wrapper

## Public API

```python
from sin_code_review_interface import (
    ReviewServer,   # programmatic review CRUD (no HTTP)
    get_app,        # FastAPI app factory
    Decision,       # enum: APPROVE / REQUEST_CHANGES / COMMENT / PENDING
    SemanticDiff,   # unified diff parser + side-by-side renderer
    Comment,        # single comment dataclass
    Thread,         # comment group on a file:line (rarely used; UI groups dynamically)
)
```

## Caveats / footguns

- `get_app()` is the entry point for ASGI servers (uvicorn, gunicorn). It creates a fresh `ReviewServer` with its own storage connection — don't share one across multiple `get_app()` calls.
- The package has no `__version__`. Consumers who need it should pin to a git ref or read `pyproject.toml`.
- `Thread` is re-exported but rarely instantiated directly — the UI builds threads on the fly by grouping comments by `(file, line)`.
