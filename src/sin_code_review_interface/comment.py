"""Comment and Thread models for code reviews.

Docs: comment.doc.md
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class Comment:
    """A single comment on a review."""
    id: str
    review_id: str
    author: str
    body: str
    file: Optional[str] = None
    line: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Thread:
    """A thread of comments on a specific file/line."""
    file: Optional[str]
    line: Optional[int]
    comments: List[Comment] = field(default_factory=list)
