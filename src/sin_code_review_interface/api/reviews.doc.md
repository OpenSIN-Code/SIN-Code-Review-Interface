# `api/reviews.py` — Review API Routes

What this file does: the complete review CRUD surface — create, list, get, add-comment, submit-decision. Equivalent routes also exist in `server.py` for standalone uvicorn use; this module is for users who want to mount the API under a custom prefix.

## Dependency map

- Imports: `fastapi.APIRouter`, `fastapi.Request`, internal `ReviewServer` and `Decision`.
- Imported by: app code that mounts the API router.

## Public API

| Method | Route                                       | Body / Returns                                                    |
|--------|---------------------------------------------|-------------------------------------------------------------------|
| POST   | `/reviews`                                  | `{"title","diff","author"?,"files_changed"?}` → review summary    |
| GET    | `/reviews`                                  | → list of review summaries                                       |
| GET    | `/reviews/{review_id}`                      | → review with parsed side-by-side diff, comments, decisions       |
| POST   | `/reviews/{review_id}/comments`             | `{"body","author"?,"file"?,"line"?}` → comment                    |
| POST   | `/reviews/{review_id}/decisions`            | `{"decision","reviewer"?}` → decision record                      |

## Important config / limits

- **All routes assume `request.app.state.review_server`** is set. Wire that up in your app factory.
- **No auth, no rate limiting.** Add a reverse proxy or middleware.
- **Comment body cap: 64 KB** (enforced in the server, not here).
- **GET `/reviews/{id}` does NOT HTML-escape** author/body — escape on the client if you render in a browser.
- **No pagination** on the list endpoint.

## Design decisions

- **Why duplicate the routes in `server.py` and `api/reviews.py`?** Two consumption patterns: standalone (`uvicorn server:app`) and embedded (`include_router(router, prefix="/api")`). Keeping both lets users pick without forcing one style.
- **Why use `request.app.state.review_server` instead of a global?** `app.state` is the FastAPI-blessed way to share per-app resources; it's cleaner than a module-level singleton and supports multiple apps in the same process.

## Usage

```python
from fastapi import FastAPI
from sin_code_review_interface.api.reviews import router
from sin_code_review_interface import ReviewServer

app = FastAPI()
app.state.review_server = ReviewServer("reviews.db")
app.include_router(router, prefix="/api")
```

## Caveats / footguns

- **The `decision` field on POST /decisions** must be a string matching one of `Decision`'s values (`"approve"`, `"request_changes"`, `"comment"`). Invalid values raise `ValueError` from `Decision(...)` and produce a 500 unless you wrap it.
- **Submitting a decision for an unknown review_id** is a no-op on `JSONStorage` and a no-op on `SQLiteStorage` too (the server's `submit_decision` raises `ValueError`, which the route doesn't catch). Add error handling if you want 404s.
- **Mount this router AND the `server.py` routes will cause duplicate route registration.** Pick one.
