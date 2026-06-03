"""Decision states for code reviews.

`Decision` is a `(str, Enum)` mixin — values are lowercase strings so they
JSON-serialize cleanly through the API and MCP. The four values match
GitHub's PR review model (approve / request changes / comment) plus a
PENDING initial state.

Docs: decision.doc.md
"""
from enum import Enum


# ── Decision enum ──────────────────────────────────────────────────────
class Decision(str, Enum):
    """Review decision states.

    Values:
      - `APPROVE`:         reviewer approves; status moves to "approve".
      - `REQUEST_CHANGES`: reviewer requests changes; status moves to "request_changes".
      - `COMMENT`:         reviewer leaves a comment without approval/rejection.
      - `PENDING`:         default state for a newly-created review.
    """

    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    COMMENT = "comment"
    PENDING = "pending"
