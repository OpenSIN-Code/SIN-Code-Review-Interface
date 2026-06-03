# `api/diff.py` — Diff API Routes

What this file does: exposes `POST /diff/parse` to parse a unified diff into structured side-by-side data. The frontend uses this to render diffs without needing its own parser.

## Dependency map

- Imports: `fastapi.APIRouter`, `fastapi.Request`, `sin_code_review_interface.diff.SemanticDiff`.
- Imported by: app code that mounts the API router.

## Public API

| Route                  | Request                              | Returns                                                                 |
|------------------------|--------------------------------------|-------------------------------------------------------------------------|
| `POST /diff/parse`     | `{"diff": "<unified diff text>"}`    | `{"files_changed": [...], "side_by_side": [...]}`                       |

## Important config / limits

- **Parses standard `git diff` format.** Non-standard diffs may not parse cleanly.
- **No diff-size limit** at this layer; if you expose this on a public endpoint, add a body-size middleware.

## Design decisions

- **Why a dedicated parse endpoint instead of returning the diff in the review response?** The frontend can parse diffs lazily (on click), avoiding the cost of parsing for reviews the user doesn't open.
- **Why no caching?** Diff parsing is microseconds-fast for typical sizes; a cache would add eviction complexity for no measurable win.

## Usage

```python
from fastapi import FastAPI
from sin_code_review_interface.api.diff import router

app = FastAPI()
app.include_router(router, prefix="/api")
```

## Caveats / footguns

- **Empty diff returns empty arrays.** `{"files_changed": [], "side_by_side": []}`. Make sure the frontend handles this.
- **No diff validation.** Garbage in → garbage out. The parser is forgiving; the response is what it is.
