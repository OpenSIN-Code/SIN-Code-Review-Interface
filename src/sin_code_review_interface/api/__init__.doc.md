# `api/__init__.py` — API Package

What this file does: empty package marker for the `api/` subpackage. The actual routes live in `comments.py`, `diff.py`, and `reviews.py`; mount this router under any prefix you like (e.g. `/api`).

## Dependency map

- Imports: nothing.
- Imported by: app code that wires the API router into a parent FastAPI app.

## Submodules

| Module           | Routes                                                                        |
|------------------|-------------------------------------------------------------------------------|
| `comments.py`    | `GET /reviews/{id}/comments`                                                  |
| `diff.py`        | `POST /diff/parse`                                                            |
| `reviews.py`     | `POST/GET /reviews`, `/reviews/{id}`, `/reviews/{id}/comments`, `/reviews/{id}/decisions` |

## Important config / limits

- **The router in `api/` is for custom mounting** (e.g. under `/api/v1`). The standalone `server.py` defines equivalent routes for direct uvicorn use.
- **Routes assume `request.app.state.review_server` is set.** Wire that up before including the router.

## Caveats / footguns

- **Routes in `api/` and `server.py` are duplicates.** Mounting both will cause FastAPI to register duplicate routes. Use one or the other.
