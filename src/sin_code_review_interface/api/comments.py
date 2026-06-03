"""Comment API routes.

Exposes `GET /reviews/{review_id}/comments` for listing the comments on
a review. The full create flow lives in `server.py` and `reviews.py` —
this module is for the read-only list endpoint.

Docs: comments.doc.md
"""
from fastapi import APIRouter, Request

# Module-level router. Mount this under any prefix; the comment author
# and body are NOT HTML-escaped here (server.py does that for UI
# responses; if you render these directly, escape before display).
router = APIRouter()

@router.get("/reviews/{review_id}/comments")
async def list_comments(review_id: str, request: Request):
    """List all comments for a review.

    Args:
        review_id: Target review UUID.
        request: FastAPI Request (used to access the app-level
                 `review_server` via `request.app.state`).

    Returns:
        List of comment dicts, or `({"error": "Not found"}, 404)`.
    """
    server = request.app.state.review_server
    review = server.get_review(review_id)
    if not review:
        # 404 with a structured body — the frontend can show a useful error.
        return {"error": "Not found"}, 404
    return [
        {"id": c.id, "author": c.author, "body": c.body,
         "file": c.file, "line": c.line, "created_at": c.created_at}
        for c in review.comments
    ]
