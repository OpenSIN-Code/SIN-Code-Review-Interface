# `reviews.py` — Reviews API

What this file does: FastAPI endpoints for creating, listing, and retrieving reviews.

## Dependencies

- Imported by: `api/__init__.py`, `server.py`

## Endpoints

- `POST /reviews` — create a review
- `GET /reviews` — list all reviews
- `GET /reviews/{id}` — get a review with side-by-side diff

## Notes

Uses `ReviewServer` for business logic and `SemanticDiff` for rendering.
