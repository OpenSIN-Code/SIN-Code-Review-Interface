# ReviewServer and FastAPI app

## What this file does
Provides the `ReviewServer` class (programmatic API) and a FastAPI application factory.

## Dependencies
- `fastapi` — HTTP framework
- `jinja2` — HTML templating
- `diff.py` — SemanticDiff for parsing and rendering diffs
- `storage.py` — Persistence layer (SQLite or JSON)

## Important config values
- Default storage path: `reviews.db` (SQLite)
- Switch to JSON by passing `*.json` path

## Usage
```python
from sin_code_review_interface.server import ReviewServer, get_app
server = ReviewServer("reviews.db")
review = server.create_review(title="feat: auth", diff="...", author="agent")
app = get_app("reviews.db")
```

## FastAPI routes
- `POST /reviews` — create
- `GET /reviews` — list
- `GET /reviews/{id}` — details + side-by-side diff
- `POST /reviews/{id}/comments` — add comment
- `POST /reviews/{id}/decisions` — submit decision
- `GET /reviews/{id}/ui` — HTML review page

## Known caveats
- No auth middleware; add in production.
- Templates directory is relative to `src/`.
