# `api/comments.py` — Comment API Routes

What this file does: exposes `GET /reviews/{review_id}/comments` to list the comments on a review. The full create flow lives in `server.py` and `reviews.py` — this module is for the read-only list endpoint.

## Dependency map

- Imports: `fastapi.APIRouter`, `fastapi.Request`.
- Imported by: app code that mounts the API router.

## Public API

| Route                                   | Returns                                            |
|-----------------------------------------|----------------------------------------------------|
| `GET /reviews/{review_id}/comments`     | `[{id, author, body, file, line, created_at}, ...]` or `({"error": "Not found"}, 404)` |

## Important config / limits

- **No `author` / `body` HTML-escaping here.** If you render this output directly in a browser, escape before display. (The `/reviews/{id}` endpoint in `server.py` does escape.)
- **Returns the raw list** (not wrapped in `{"comments": [...]}`). Match the consumer's expectation.
- **No pagination.** A review with thousands of comments returns all of them in one response.

## Design decisions

- **Why a separate module for one route?** Future-proofing — the comment thread will grow (edit, delete, react, etc.) and deserves its own file.
- **Why access the server via `request.app.state.review_server`?** Dependency injection without a Depends() function. Wire the server into `app.state` once, in your factory, and every route can find it.

## Usage

```python
from fastapi import FastAPI
from sin_code_review_interface.api.comments import router
from sin_code_review_interface import ReviewServer

app = FastAPI()
app.state.review_server = ReviewServer("reviews.db")
app.include_router(router, prefix="/api")
```

## Caveats / footguns

- **HTML injection risk.** The `author` and `body` fields come from untrusted agent output. If you render this JSON in a browser, escape before display.
- **The route is mounted at `/reviews/...` (no prefix in this file).** Add a prefix when including the router if you want `/api/reviews/...`.
