# `decision.py` — Review Decision States

What this file does: defines the `Decision` enum — the four states a review can be in (PENDING, APPROVE, REQUEST_CHANGES, COMMENT). Values are lowercase strings so they JSON-serialize cleanly.

## Dependency map

- Imports: stdlib `enum` only.
- Imported by: `.storage` (default status), `.server` (decision endpoint), `.api/reviews` (decision endpoint), `mcp_server` (decision dispatch).

## Public API

| Value              | String           | When it's set                                              |
|--------------------|------------------|------------------------------------------------------------|
| `Decision.APPROVE` | `"approve"`      | Reviewer explicitly approves.                              |
| `Decision.REQUEST_CHANGES` | `"request_changes"` | Reviewer requests changes before merge.              |
| `Decision.COMMENT` | `"comment"`      | Reviewer leaves a comment without approval/rejection.      |
| `Decision.PENDING` | `"pending"`      | Default state for a new review.                            |

## Design decisions

- **Why `(str, Enum)` mixin?** Values JSON-serialize as their string form. Without it, FastAPI would emit `"Decision.APPROVE"` or refuse to encode at all.
- **Why does this match GitHub's PR review model?** Familiar vocabulary. Reviewers coming from GitHub know what `request_changes` means without reading docs.
- **Why is `PENDING` a `Decision` and not a separate field?** Symmetry — `ReviewData.status` is a string, and `Decision.PENDING.value` is `"pending"`. One type, no special cases.

## Usage example

```python
from sin_code_review_interface import Decision

d = Decision("approve")
print(d.value)            # "approve"
print(d == "approve")     # True (because Decision subclasses str)
print(list(Decision))     # [<Decision.APPROVE: 'approve'>, ...]
```

## Caveats / footguns

- **The string values are part of the public API** (they cross MCP and HTTP wire formats). Renaming a value is a breaking change.
- **`Decision("foo")` raises `ValueError`.** Catch it in API endpoints if you want to return a 400 instead of a 500.
- **The server's `submit_decision` accepts both `Decision` and `str`.** Pass a string from MCP/HTTP and the server coerces internally.
