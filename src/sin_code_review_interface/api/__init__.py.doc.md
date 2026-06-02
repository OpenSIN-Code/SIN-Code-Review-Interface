# `__init__.py` — API Package

What this file does: package-level exports for REST API endpoints.

## Dependencies

- Imported by: `server.py`

## Exports

- `reviews_router` — FastAPI router for review endpoints
- `comments_router` — FastAPI router for comment endpoints
- `diff_router` — FastAPI router for diff endpoints

## Notes

Routers are mounted by `get_app()` in `server.py`.
