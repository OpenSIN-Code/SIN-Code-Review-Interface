# `comment.py` — Review Comments

What this file does: the data model for review comments and threads. Two dataclasses — `Comment` (a single comment with author, body, file/line anchor, timestamp) and `Thread` (a list of comments grouped by file/line).

## Dependency map

- Imports: stdlib `dataclasses`, `datetime`, `typing`.
- Imported by: `.server` (add_comment), `.storage` (review persistence), `.api/comments` (list endpoint).

## Public API

| Symbol     | Purpose                                                                |
|------------|------------------------------------------------------------------------|
| `Comment`  | A single comment: id, review_id, author, body, file?, line, created_at |
| `Thread`   | A thread: file, line, list of comments. The UI builds these dynamically. |

## Important config / limits

- **`Comment.body` is capped at 64 KB** by the server (`ReviewServer.add_comment`). Larger bodies raise `ValueError` before storage.
- **`Comment.created_at` is auto-generated** to `datetime.now(timezone.utc).isoformat()` on construction. Override by passing a value explicitly.
- **`Comment.file` is `Optional[str]`, `Comment.line` defaults to `0`.** A comment with `file=None` is a "general" comment on the whole review; otherwise it's anchored to `file:line`.
- **`Thread.comments` is mutable.** The UI may append to it as new comments come in.

## Design decisions

- **Why a `Thread` dataclass if the UI groups dynamically?** The dataclass is a convenient carrier for API responses; the UI can ignore it and group itself.
- **Why `timezone.utc` and not local time?** UTC ISO-8601 is sortable and unambiguous. Local time would require a tz suffix and confuse downstream consumers.
- **Why is `line` an `int` and not a `LineRange`?** Most comments anchor on a single line. A range would complicate the storage and the UI for a rare case.

## Usage example

```python
from sin_code_review_interface import Comment

c = Comment(
    id="c-uuid",
    review_id="r-uuid",
    author="reviewer",
    body="LGTM with one nit",
    file="src/auth.py",
    line=42,
)
```

## Caveats / footguns

- **`Comment.id` and `Comment.review_id` are NOT auto-generated** by the dataclass — the server (`ReviewServer.add_comment`) does that. Constructing a `Comment` directly requires both.
- **Mutating `Thread.comments` does not auto-save.** The server's `add_comment` is the only way to persist a comment.
- **`created_at` is a string, not a `datetime`.** Parse with `datetime.fromisoformat(c.created_at)` if you need to do date math.
