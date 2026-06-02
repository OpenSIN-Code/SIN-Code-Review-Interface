# `comment.py` — Review Comments

What this file does: defines the data models for review comments and threads.

## Dependencies

- Imported by: `server.py`, `storage.py`, tests

## Types

- `Comment` — a single comment with id, author, body, file, line, created_at
- `Thread` — a threaded discussion attached to a review

## Usage

```python
from sin_code_review_interface import Comment
comment = Comment(id="uuid", review_id="rid", author="bot", body="LGTM")
```

## Notes

Comments are stored as part of the review record in SQLite/JSON storage.
