"""API package for review endpoints.

Submodules:
  - `comments.py`: GET /reviews/{id}/comments
  - `diff.py`:     POST /diff/parse
  - `reviews.py`:  POST/GET /reviews, /reviews/{id}, /reviews/{id}/comments, /reviews/{id}/decisions

Mount this router under any prefix (e.g. `/api` or `/reviews/v1`) to
expose the routes. The standalone `server.py` also defines equivalent
routes for direct uvicorn use.

Docs: __init__.doc.md
"""
