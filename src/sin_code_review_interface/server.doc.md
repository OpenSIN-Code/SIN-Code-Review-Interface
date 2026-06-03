# `server.py` — Review Server (FastAPI + Programmatic)

What this file does: two layers in one file. `ReviewServer` is the programmatic CRUD layer (no HTTP). `get_app()` is the FastAPI app factory that wires `ReviewServer` to a JSON API and HTML UI. Storage is auto-selected from the path: `.json` → `JSONStorage`, otherwise `SQLiteStorage`.

## Dependency map

- Imports: `fastapi`, `fastapi.responses`, `fastapi.templating`, `html` (stdlib), `uuid` (stdlib), plus internal: `.comment.Comment`, `.decision.Decision`, `.diff.SemanticDiff`, `.storage.{JSONStorage,ReviewData,SQLiteStorage,Storage}`.
- Imported by: `__init__.py` (re-exports), `cli.py` (uvicorn target), `mcp_server.py` (storage).

## Public API

| Symbol                                                | Purpose                                                              |
|-------------------------------------------------------|----------------------------------------------------------------------|
| `ReviewServer(storage_path="reviews.db")`             | Construct. `.json` → JSONStorage, else SQLiteStorage.                |
| `.create_review(title, diff, author, files_changed?)` | Create a review. `files_changed` is inferred from the diff if omitted. |
| `.get_review(review_id)`                              | Fetch by ID; `None` if not found.                                    |
| `.list_reviews()`                                     | List all reviews (no pagination).                                    |
| `.add_comment(review_id, body, author?, file?, line?)` | Add a comment. 64 KB body cap.                                       |
| `.submit_decision(review_id, reviewer, decision)`     | Submit a decision. Coerces string to `Decision`.                      |
| `.get_comments_for_review(review_id)`                 | List comments (or `[]` if review missing).                            |
| `get_app(storage_path="reviews.db")`                  | FastAPI app factory.                                                  |

## Important config / limits

- **Storage is chosen by file extension**: `.json` → JSONStorage, else SQLite.
- **Comment body limit: 64 KB** (matches GitHub PR comments).
- **`/reviews/{id}` endpoint HTML-escapes** author and body to prevent stored XSS — review content can come from untrusted agents.
- **`/reviews/{id}/ui` returns a 404 page** (not JSON) when the review is missing.
- **Decision accepts both `Decision` and `string`.** MCP clients pass strings; the server coerces internally.

## Design decisions

- **Why the factory pattern (`get_app`) instead of a module-level `app`?** Tests can instantiate a fresh app with isolated storage. A module-level `app` would share state across tests.
- **Why HTML-escape on the GET endpoint but not on create?** `html.escape` is a read-side concern — escaping on create would double-escape when the UI re-renders. Escape once, at the boundary closest to the renderer.
- **Why no auth middleware?** The interface is intended for trusted internal networks. Add a reverse proxy (e.g. nginx with basic auth) if you need to expose it.
- **Why `Optional[int] = 0` for `line`?** A default of `0` is a sentinel for "no specific line". The UI hides line numbers when `line == 0` to avoid rendering `"line: 0"`.

## Usage example

```python
# Programmatic
from sin_code_review_interface import ReviewServer
server = ReviewServer("reviews.db")
r = server.create_review(title="t", diff="...", author="agent")
server.add_comment(r.id, "LGTM")

# ASGI
from sin_code_review_interface import get_app
app = get_app("reviews.db")
# uvicorn my_module:app
```

## Caveats / footguns

- **`ReviewServer.__init__` opens the SQLite database immediately.** Creating thousands of `ReviewServer` instances (e.g. per-request) will leak file handles. Use the module-level singleton pattern in `__init__.py` for production.
- **No CSRF protection on POST endpoints.** Add a CSRF middleware or use SameSite=Strict cookies if you expose this on the public web.
- **The 64 KB comment cap is in CHARACTERS, not bytes.** Multi-byte characters (e.g. emoji) may push the actual byte count higher.
