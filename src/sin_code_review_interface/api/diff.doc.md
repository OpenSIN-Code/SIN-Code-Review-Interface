# `diff.py` — Diff API

What this file does: FastAPI endpoints for generating and retrieving semantic diffs.

## Dependencies

- Imported by: `api/__init__.py`, `server.py`

## Endpoints

- `GET /reviews/{id}/diff` — get the raw diff
- `GET /reviews/{id}/side-by-side` — get the rendered side-by-side diff

## Notes

Side-by-side diff is returned as HTML for the UI.
