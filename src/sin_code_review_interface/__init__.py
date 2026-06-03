"""SIN Code Review Interface — human-centered review of agent-generated code.

Re-exports the public API: `ReviewServer`, `get_app`, `Decision`, `SemanticDiff`,
`Comment`, `Thread`. See `server.doc.md` for the high-level architecture.

Docs: __init__.doc.md
"""
from .server import ReviewServer, get_app
from .decision import Decision
from .diff import SemanticDiff
from .comment import Comment, Thread

__all__ = [
    "ReviewServer",
    "get_app",
    "Decision",
    "SemanticDiff",
    "Comment",
    "Thread",
]
