"""Storage backends for reviews.

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


class ReviewData:
    """In-memory representation of a review."""
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


class Storage:
    """Abstract storage interface."""
    def create(self, review: ReviewData) -> None:
        raise NotImplementedError

    def get(self, review_id: str) -> Optional[ReviewData]:
        raise NotImplementedError

    def list(self) -> List[ReviewData]:
        raise NotImplementedError

    def add_comment(self, review_id: str, comment: Comment) -> None:
        raise NotImplementedError

    def add_decision(self, review_id: str, reviewer: str, decision: str) -> None:
        raise NotImplementedError


class SQLiteStorage(Storage):
    """SQLite-backed persistent storage."""
    def __init__(self, path: str = "reviews.db"):
        self.path = path
        self._init_db()

    def _init_db(self) -> None:
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
        cursor.execute(
            "INSERT OR REPLACE INTO decisions (review_id, reviewer, decision) VALUES (?, ?, ?)",
            (review_id, reviewer, decision)
        )
        cursor.execute("UPDATE reviews SET status=? WHERE id=?", (decision, review_id))
        conn.commit()
        conn.close()


class JSONStorage(Storage):
    """JSON-file-backed storage for testing."""
    def __init__(self, path: str = "reviews.json"):
        self.path = Path(path)
        self._data: Dict[str, dict] = {}
        if self.path.exists():
            text = self.path.read_text()
            if text.strip():
                try:
                    self._data = json.loads(text)
                except json.JSONDecodeError as e:
                    logging.warning("Corrupted JSON in %s: %s", self.path, e)
                    self._data = {}

    def _save(self) -> None:
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
        review.comments = [Comment(**c) for c in raw.get("comments", [])]
        review.decisions = raw.get("decisions", {})
        return review

    def list(self) -> List[ReviewData]:
        return [self.get(rid) for rid in self._data if self.get(rid) is not None]

    def add_comment(self, review_id: str, comment: Comment) -> None:
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
        self._data[review_id]["decisions"][reviewer] = decision
        self._data[review_id]["status"] = decision
        self._save()
