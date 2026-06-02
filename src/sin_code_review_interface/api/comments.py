"""Comment API routes.

Docs: api/comments.doc.md
"""
from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/reviews/{review_id}/comments")
async def list_comments(review_id: str, request: Request):
    server = request.app.state.review_server
    review = server.get_review(review_id)
    if not review:
        return {"error": "Not found"}, 404
    return [
        {"id": c.id, "author": c.author, "body": c.body,
         "file": c.file, "line": c.line, "created_at": c.created_at}
        for c in review.comments
    ]
