# `decision.py` — Review Decisions

What this file does: defines the decision states for code reviews.

## Dependencies

- Imported by: `__init__.py`, `server.py`, `mcp_server.py`, tests

## Types

- `Decision` — enum: APPROVE, REQUEST_CHANGES, COMMENT, PENDING

## Usage

```python
from sin_code_review_interface import Decision
server.submit_decision(review_id, "jeremy", Decision.APPROVE)
```

## Notes

PENDING is the default status for newly created reviews.
