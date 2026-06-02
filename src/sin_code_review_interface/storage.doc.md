# `storage.py` — Review Storage

What this file does: persistence layer for reviews, comments, and decisions. Supports SQLite and JSON backends.

## Dependencies

- Imported by: `server.py`, tests

## Backends

- `SQLiteStorage` — file-based SQLite (default for `.db` paths)
- `JSONStorage` — simple JSON file (default for `.json` paths)

## Usage

```python
from sin_code_review_interface.storage import SQLiteStorage, JSONStorage
storage = SQLiteStorage("reviews.db")
```

## Notes

Choose the backend by file extension when creating `ReviewServer`. SQLite is recommended for production use.
