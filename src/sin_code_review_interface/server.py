"""Review server with FastAPI and ReviewServer.

Docs: server.py.doc.md
"""
import html
import uuid
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .comment import Comment
from .decision import Decision
from .diff import SemanticDiff
from .storage import JSONStorage, ReviewData, SQLiteStorage, Storage


class ReviewServer:
    """Programmatic review server."""

    def __init__(self, storage_path: str = "reviews.db"):
        if storage_path.endswith(".json"):
            self.storage: Storage = JSONStorage(storage_path)
        else:
            self.storage = SQLiteStorage(storage_path)

    def create_review(self, title: str, diff: str, author: str,
                      files_changed: Optional[List[str]] = None) -> ReviewData:
        """Create a new review from diff text."""
        review_id = str(uuid.uuid4())
        if files_changed is None:
            sd = SemanticDiff(diff)
            files_changed = sd.get_files_changed()
        review = ReviewData(
            review_id=review_id,
            title=title,
            diff=diff,
            author=author,
            files_changed=files_changed
        )
        self.storage.create(review)
        return review

    def get_review(self, review_id: str) -> Optional[ReviewData]:
        """Get a review by ID."""
        return self.storage.get(review_id)

    def list_reviews(self) -> List[ReviewData]:
        """List all reviews."""
        return self.storage.list()

    def add_comment(self, review_id: str, body: str, author: str = "reviewer",
                    file: Optional[str] = None, line: Optional[int] = 0) -> Comment:
        """Add a comment to a review."""
        if len(body) > 65536:  # 64KB limit
            raise ValueError("Comment body exceeds 64KB limit")
        comment = Comment(
            id=str(uuid.uuid4()),
            review_id=review_id,
            author=author,
            body=body,
            file=file,
            line=line
        )
        self.storage.add_comment(review_id, comment)
        return comment

    def submit_decision(self, review_id: str, reviewer: str,
                        decision: Decision) -> None:
        """Submit a review decision."""
        if isinstance(decision, str):
            decision = Decision(decision)
        if not self.storage.get(review_id):
            raise ValueError(f"Review not found: {review_id}")
        self.storage.add_decision(review_id, reviewer, decision.value)

    def get_comments_for_review(self, review_id: str) -> List[Comment]:
        """Get all comments for a review."""
        review = self.storage.get(review_id)
        if review:
            return review.comments
        return []


# FastAPI app factory

def get_app(storage_path: str = "reviews.db") -> FastAPI:
    """Create and configure the FastAPI application."""
    server = ReviewServer(storage_path=storage_path)
    app = FastAPI(title="SIN Code Review Interface")
    templates = Jinja2Templates(directory="src/sin_code_review_interface/templates")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        reviews = server.list_reviews()
        return templates.TemplateResponse(request, "base.html", {"reviews": reviews})

    @app.post("/reviews")
    async def create_review_endpoint(request: Request):
        data = await request.json()
        review = server.create_review(
            title=data["title"],
            diff=data["diff"],
            author=data.get("author", "agent"),
            files_changed=data.get("files_changed")
        )
        return {"id": review.id, "title": review.title, "author": review.author,
                "files_changed": review.files_changed, "status": review.status}

    @app.get("/reviews")
    async def list_reviews_endpoint():
        reviews = server.list_reviews()
        return [{"id": r.id, "title": r.title, "author": r.author,
                 "files_changed": r.files_changed, "status": r.status} for r in reviews]

    @app.get("/reviews/{review_id}")
    async def get_review_endpoint(review_id: str):
        review = server.get_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Not found")
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
                {"id": c.id, "author": html.escape(c.author), "body": html.escape(c.body),
                 "file": c.file, "line": c.line, "created_at": c.created_at}
                for c in review.comments
            ],
            "decisions": review.decisions
        }

    @app.post("/reviews/{review_id}/comments")
    async def add_comment_endpoint(review_id: str, request: Request):
        data = await request.json()
        comment = server.add_comment(
            review_id=review_id,
            body=data["body"],
            author=data.get("author", "reviewer"),
            file=data.get("file"),
            line=data.get("line")
        )
        return {"id": comment.id, "author": html.escape(comment.author), "body": html.escape(comment.body),
                "file": comment.file, "line": comment.line}

    @app.post("/reviews/{review_id}/decisions")
    async def submit_decision_endpoint(review_id: str, request: Request):
        data = await request.json()
        decision = Decision(data.get("decision", "comment"))
        server.submit_decision(review_id, data.get("reviewer", "human"), decision)
        return {"review_id": review_id, "reviewer": data.get("reviewer", "human"), "decision": decision.value}

    @app.get("/reviews/{review_id}/ui", response_class=HTMLResponse)
    async def review_ui(request: Request, review_id: str):
        review = server.get_review(review_id)
        if not review:
            return HTMLResponse("<h1>Review not found</h1>", status_code=404)
        sd = SemanticDiff(review.diff)
        return templates.TemplateResponse(request, "review.html", {
            "review": review,
            "side_by_side": sd.render_side_by_side()
        })

    return app
