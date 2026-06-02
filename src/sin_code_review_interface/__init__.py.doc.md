# `__init__.py` — SIN-Code Review Interface

What this file does: package-level exports for `sin_code_review_interface`.

## Dependencies

- Imported by: external consumers, tests, CLI, MCP server
- Imports: `server`, `decision`, `diff`, `comment`

## Exports

- `ReviewServer` — programmatic review server
- `get_app` — FastAPI app factory
- `Decision` — review decision enum (APPROVE, REQUEST_CHANGES, COMMENT, PENDING)
- `SemanticDiff` — diff parser and renderer
- `Comment` — comment data model
- `Thread` — threaded discussion model

## Usage

```python
from sin_code_review_interface import ReviewServer, Decision
server = ReviewServer("reviews.db")
```

## Notes

`get_app()` is the entry point for ASGI servers (uvicorn, gunicorn).
