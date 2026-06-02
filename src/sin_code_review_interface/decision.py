"""Decision states for code reviews.

Docs: decision.doc.md
"""
from enum import Enum


class Decision(str, Enum):
    """Review decision states."""
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    COMMENT = "comment"
    PENDING = "pending"
