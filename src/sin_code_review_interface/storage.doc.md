# `storage.py` — Storage Backends

What this file does: the persistence layer for reviews. Three pieces — `ReviewData` (in-memory model), `Storage` (abstract interface), and two concrete backends: `SQLiteStorage` (default) and `JSONStorage` (testing / single-process).

## Dependency map

- Imports: stdlib (`json`, `logging`, `sqlite3`, `pathlib`, `typing`).
- Imported by: `.server` (storage selection), `mcp_server` (storage selection).

## Public API

| Symbol                                          | Purpose                                                              |
|-------------------------------------------------|----------------------------------------------------------------------|
| `ReviewData`                                    | In-memory model: id, title, diff, author, files_changed, status, comments, decisions. |
| `Storage` (ABC)                                 | Abstract: `create / get / list / add_comment / add_decision`.        |
| `SQLiteStorage(path="reviews.db")`              | Default backend. Three tables: `reviews`, `comments`, `decisions`.   |
| `JSONStorage(path="reviews.json")`              | Testing / single-process backend. One JSON file, full read-modify-write per op. |

## Important config / limits

- **Storage is selected by file extension in `ReviewServer.__init__`**: `.json` → JSONStorage, else SQLite.
- **JSONStorage is NOT concurrency-safe** — every method reads-modify-writes the whole file. Use SQLite for production.
- **SQLiteStorage is single-process safe** but does not enable WAL mode. For multi-writer workloads, run `PRAGMA journal_mode=WAL` once on the DB.
- **Decisions have a composite primary key `(review_id, reviewer)`** in SQLite — a reviewer changing their mind does an `INSERT OR REPLACE`.
- **`add_decision` updates the review's overall `status`** to the latest decision value. Status is therefore "the most recent decision" rather than an aggregate.
- **JSONStorage silently ignores** `add_comment` / `add_decision` for unknown `review_id`. The server is expected to validate the review_id first.

## Design decisions

- **Why two backends?** SQLite is the default (ACID, fast, single-file); JSON is the escape hatch for tests, sandboxes, and environments where SQLite isn't available.
- **Why `INSERT OR REPLACE` for decisions?** A reviewer can change their mind. The composite primary key means re-submitting overwrites; no separate "update" path needed.
- **Why a corrupted JSON file starts fresh instead of raising?** Losing a corrupted file is better than refusing to start. A warning is logged so the operator can restore from backup.
- **Why not use an ORM?** Storage is small enough that hand-written SQL is clearer than an ORM mapping. The schema is 3 tables; an ORM would add more friction than it removes.

## Usage example

```python
from sin_code_review_interface.storage import SQLiteStorage, ReviewData, JSONStorage

# SQLite
db = SQLiteStorage("reviews.db")
review = ReviewData(review_id="r1", title="t", diff="...", author="me", files_changed=[])
db.create(review)

# JSON (testing)
jd = JSONStorage("reviews.json")
jd.create(review)
```

## Caveats / footguns

- **JSONStorage `add_comment` returns silently** on unknown review_id. Check the review exists first if you care about getting an error.
- **SQLiteStorage opens a new connection per method call.** Cheap for SQLite, but at very high QPS you may want a connection pool.
- **`ReviewData.created_at` is `None` until the storage backend sets it** (the SQLite backend uses `DEFAULT CURRENT_TIMESTAMP`, but the value isn't loaded back into the dataclass).
- **No migrations.** Schema changes require a `DROP TABLE` or a manual ALTER. Acceptable for a single-table schema; would need Alembic if it grew.
