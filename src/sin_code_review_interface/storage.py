"""Storage backends for reviews.

Three pieces:
  - `ReviewData`: in-memory representation of a review.
  - `Storage`:     abstract interface (create / get / list / add_comment / add_decision).
  - `SQLiteStorage` / `JSONStorage`: two concrete implementations.

The server picks the backend by file extension (`.json` → JSON,
otherwise SQLite).

Docs: storage.doc.md
"""
import json
import logging
import sqlite3
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from .comment import Comment
from .decision import Decision


# ── Data model ─────────────────────────────────────────────────────────
class ReviewData:
    """In-memory representation of a review.

    Comments and decisions are loaded eagerly when the review is read
    from storage; they're mutable lists/dicts on this object.
    """
    def __init__(self, review_id: str, title: str, diff: str, author: str,
                 files_changed: List[str], status: str = Decision.PENDING):
        self.id = review_id
        self.title = title
        self.diff = diff
        self.author = author
        self.files_changed = files_changed
        self.status = status
        self.comments: List[Comment] = []
        self.decisions: Dict[str, str] = {}
        self.created_at = None


# ── Abstract interface ─────────────────────────────────────────────────
class Storage:
    """Abstract storage interface.

    Subclasses must implement all five methods. The interface is
    deliberately narrow — anything more complex (transactions, indexes)
    belongs in a subclass.
    """
    def create(self, review: ReviewData) -> None:
        """Persist a new review."""
        raise NotImplementedError

    def get(self, review_id: str) -> Optional[ReviewData]:
        """Fetch a review by ID; return `None` if not found."""
        raise NotImplementedError

    def list(self) -> List[ReviewData]:
        """List all reviews (no pagination)."""
        raise NotImplementedError

    def add_comment(self, review_id: str, comment: Comment) -> None:
        """Append a comment to an existing review."""
        raise NotImplementedError

    def add_decision(self, review_id: str, reviewer: str, decision: str) -> None:
        """Record a reviewer's decision; updates the review's status too."""
        raise NotImplementedError


# ── SQLite backend ─────────────────────────────────────────────────────
class SQLiteStorage(Storage):
    """SQLite-backed persistent storage (default for production)."""
    def __init__(self, path: str = "reviews.db"):
        self.path = path
        self._init_db()

    def _init_db(self) -> None:
        """Create the three tables if they don't already exist.

        Schema:
          - reviews:    one row per review (id is the primary key).
          - comments:   many rows per review, joined by review_id.
          - decisions:  one row per (review_id, reviewer) pair; the
                        composite primary key means a reviewer can change
                        their decision by submitting again.
        """
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                diff TEXT NOT NULL,
                author TEXT NOT NULL,
                files_changed TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                review_id TEXT NOT NULL,
                author TEXT NOT NULL,
                body TEXT NOT NULL,
                file TEXT,
                line INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                review_id TEXT NOT NULL,
                reviewer TEXT NOT NULL,
                decision TEXT NOT NULL,
                PRIMARY KEY (review_id, reviewer)
            )
        """)
        conn.commit()
        conn.close()

    def create(self, review: ReviewData) -> None:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        # `files_changed` is a list — JSON-encoded into a TEXT column.
        cursor.execute(
            "INSERT INTO reviews (id, title, diff, author, files_changed, status) VALUES (?, ?, ?, ?, ?, ?)",
            (review.id, review.title, review.diff, review.author,
             json.dumps(review.files_changed), review.status)
        )
        conn.commit()
        conn.close()

    def get(self, review_id: str) -> Optional[ReviewData]:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, diff, author, files_changed, status FROM reviews WHERE id=?", (review_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        review = ReviewData(
            review_id=row[0],
            title=row[1],
            diff=row[2],
            author=row[3],
            files_changed=json.loads(row[4]),
            status=row[5]
        )
        # Load comments and decisions in the same connection so we see a
        # consistent snapshot (SQLite default isolation is serializable
        # within a connection).
        cursor.execute("SELECT id, review_id, author, body, file, line, created_at FROM comments WHERE review_id=?", (review_id,))
        for crow in cursor.fetchall():
            review.comments.append(Comment(
                id=crow[0], review_id=crow[1], author=crow[2],
                body=crow[3], file=crow[4], line=crow[5],
                created_at=crow[6]
            ))
        cursor.execute("SELECT reviewer, decision FROM decisions WHERE review_id=?", (review_id,))
        for drow in cursor.fetchall():
            review.decisions[drow[0]] = drow[1]
        conn.close()
        return review

    def list(self) -> List[ReviewData]:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, diff, author, files_changed, status FROM reviews")
        rows = cursor.fetchall()
        reviews = []
        for row in rows:
            reviews.append(ReviewData(
                review_id=row[0],
                title=row[1],
                diff=row[2],
                author=row[3],
                files_changed=json.loads(row[4]),
                status=row[5]
            ))
        conn.close()
        return reviews

    def add_comment(self, review_id: str, comment: Comment) -> None:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO comments (id, review_id, author, body, file, line) VALUES (?, ?, ?, ?, ?, ?)",
            (comment.id, review_id, comment.author, comment.body, comment.file, comment.line)
        )
        conn.commit()
        conn.close()

    def add_decision(self, review_id: str, reviewer: str, decision: str) -> None:
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        # `INSERT OR REPLACE` because a reviewer can change their mind —
        # the (review_id, reviewer) composite primary key handles upsert.
        cursor.execute(
            "INSERT OR REPLACE INTO decisions (review_id, reviewer, decision) VALUES (?, ?, ?)",
            (review_id, reviewer, decision)
        )
        # Also bump the review's overall status to the latest decision.
        cursor.execute("UPDATE reviews SET status=? WHERE id=?", (decision, review_id))
        conn.commit()
        conn.close()


# ── JSON backend ───────────────────────────────────────────────────────
class JSONStorage(Storage):
    """JSON-file-backed storage. Convenient for tests and small deployments.

    NOT suitable for concurrent access — every method reads-modify-writes
    the whole file. Use SQLite for production.
    """
    def __init__(self, path: str = "reviews.json"):
        self.path = Path(path)
        self._data: Dict[str, dict] = {}
        if self.path.exists():
            text = self.path.read_text()
            if text.strip():
                try:
                    self._data = json.loads(text)
                except json.JSONDecodeError as e:
                    # Corrupted file — log and start fresh rather than crash.
                    # The user can restore from backup if they have one.
                    logging.warning("Corrupted JSON in %s: %s", self.path, e)
                    self._data = {}

    def _save(self) -> None:
        """Persist the in-memory dict to disk (pretty-printed)."""
        self.path.write_text(json.dumps(self._data, indent=2))

    def create(self, review: ReviewData) -> None:
        self._data[review.id] = {
            "id": review.id,
            "title": review.title,
            "diff": review.diff,
            "author": review.author,
            "files_changed": review.files_changed,
            "status": review.status,
            "comments": [],
            "decisions": {}
        }
        self._save()

    def get(self, review_id: str) -> Optional[ReviewData]:
        raw = self._data.get(review_id)
        if not raw:
            return None
        review = ReviewData(
            review_id=raw["id"],
            title=raw["title"],
            diff=raw["diff"],
            author=raw["author"],
            files_changed=raw["files_changed"],
            status=raw["status"]
        )
        # `**c` works because Comment's field names match the JSON keys.
        review.comments = [Comment(**c) for c in raw.get("comments", [])]
        review.decisions = raw.get("decisions", {})
        return review

    def list(self) -> List[ReviewData]:
        # `self.get(rid)` filters out None defensively (e.g. corrupt rows).
        return [self.get(rid) for rid in self._data if self.get(rid) is not None]

    def add_comment(self, review_id: str, comment: Comment) -> None:
        # Silently ignore comments on unknown reviews — caller (the server)
        # is supposed to validate the review_id first.
        if review_id not in self._data:
            return
        self._data[review_id]["comments"].append({
            "id": comment.id,
            "review_id": comment.review_id,
            "author": comment.author,
            "body": comment.body,
            "file": comment.file,
            "line": comment.line,
            "created_at": comment.created_at
        })
        self._save()

    def add_decision(self, review_id: str, reviewer: str, decision: str) -> None:
        if review_id not in self._data:
            return
        # Two writes: the per-reviewer decision AND the rollup status.
        self._data[review_id]["decisions"][reviewer] = decision
        self._data[review_id]["status"] = decision
        self._save()
