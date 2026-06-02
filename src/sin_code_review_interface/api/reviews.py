"""Review API routes.

Docs: reviews.doc.md
"""
from fastapi import APIRouter, Request
from sin_code_review_interface.server import ReviewServer
from sin_code_review_interface.decision import Decision

router = APIRouter()

# Note: these routes are also defined in server.py for standalone use.
# When using the API package, mount this router under /api or /reviews.

@router.post("/reviews")
async def create_review(request: Request):
    server: ReviewServer = request.app.state.review_server
    data = await request.json()
    review = server.create_review(
        title=data["title"],
        diff=data["diff"],
        author=data.get("author", "agent"),
        files_changed=data.get("files_changed")
    )
    return {"id": review.id, "title": review.title, "author": review.author,
            "files_changed": review.files_changed, "status": review.status}

@router.get("/reviews")
async def list_reviews(request: Request):
    server: ReviewServer = request.app.state.review_server
    reviews = server.list_reviews()
    return [{"id": r.id, "title": r.title, "author": r.author,
             "files_changed": r.files_changed, "status": r.status} for r in reviews]

@router.get("/reviews/{review_id}")
async def get_review(review_id: str, request: Request):
    from sin_code_review_interface.diff import SemanticDiff
    server: ReviewServer = request.app.state.review_server
    review = server.get_review(review_id)
    if not review:
        return {"error": "Not found"}, 404
    sd = SemanticDiff(review.diff)
    return {
        "id": review.id,
        "title": review.title,
        "author": review.author,
        "files_changed": review.files_changed,
        "status": review.status,
        "diff": review.diff,
        "side_by_side": sd.render_side_by_side(),
        "comments": [
            {"id": c.id, "author": c.author, "body": c.body,
             "file": c.file, "line": c.line, "created_at": c.created_at}
            for c in review.comments
        ],
        "decisions": review.decisions
    }

@router.post("/reviews/{review_id}/comments")
async def add_comment(review_id: str, request: Request):
    server: ReviewServer = request.app.state.review_server
    data = await request.json()
    comment = server.add_comment(
        review_id=review_id,
        body=data["body"],
        author=data.get("author", "reviewer"),
        file=data.get("file"),
        line=data.get("line")
    )
    return {"id": comment.id, "author": comment.author, "body": comment.body,
            "file": comment.file, "line": comment.line}

@router.post("/reviews/{review_id}/decisions")
async def submit_decision(review_id: str, request: Request):
    server: ReviewServer = request.app.state.review_server
    data = await request.json()
    decision = Decision(data.get("decision", "comment"))
    server.submit_decision(review_id, data.get("reviewer", "human"), decision)
    return {"review_id": review_id, "reviewer": data.get("reviewer", "human"), "decision": decision.value}
