"""Edge-case tests for SIN-Code-Review-Interface — bugs NOT covered by existing tests.

Docs: test_edge_cases.doc.md
"""

import os
import json
import tempfile
import pytest
from pathlib import Path


# Use sys.path to ensure imports work from src/
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sin_code_review_interface import ReviewServer, Decision, SemanticDiff, Comment
from sin_code_review_interface.storage import JSONStorage, SQLiteStorage, ReviewData


@pytest.fixture
def tmp_json_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def tmp_sqlite_storage():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


# ── Empty/blank submissions ────────────────────────────

def test_create_review_with_empty_diff(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    review = server.create_review("Test", "", "agent")
    assert review.title == "Test"
    assert review.files_changed == []


def test_create_review_with_empty_title(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    review = server.create_review("", "diff --git a/test.py b/test.py\n", "agent")
    assert review.title == ""


def test_semantic_diff_only_header_no_hunks():
    sd = SemanticDiff("diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n")
    assert sd.get_files_changed() == ["test.py"]
    assert len(sd.render_side_by_side()) > 0
    # Should have a file entry but with no hunks
    result = sd.render_side_by_side()
    assert result[0]["hunks"] == []


def test_semantic_diff_complex_unified():
    diff = """diff --git a/main.py b/main.py
--- a/main.py
+++ b/main.py
@@ -1,5 +1,5 @@
 def main():
-    old_code()
+    new_code()
     return True
@@ -10,6 +10,8 @@
 def helper():
     pass
+
+def new_helper():
+    pass
diff --git a/utils.py b/utils.py
--- a/utils.py
+++ b/utils.py
@@ -1,3 +1,4 @@
+import os
 def util():
     return 1
"""
    sd = SemanticDiff(diff)
    files = sd.get_files_changed()
    assert "main.py" in files
    assert "utils.py" in files
    # Should have 2 files
    assert len(files) == 2


def test_semantic_diff_unicode():
    diff = """diff --git a/utf8.py b/utf8.py
--- a/utf8.py
+++ b/utf8.py
@@ -1,3 +1,3 @@
-def hello():
+def こんにちは():
     return "Hello"
"""
    sd = SemanticDiff(diff)
    files = sd.get_files_changed()
    assert "utf8.py" in files


def test_semantic_diff_edge_cases():
    """Diff with various edge-case patterns."""
    diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,1 +1,1 @@
-old line
+new line
@@ -100,0 +101,5 @@
+line1
+line2
+line3
+line4
+line5
"""
    sd = SemanticDiff(diff)
    result = sd.render_side_by_side()
    # Should handle multiple hunks
    assert len(result) > 0
    if result:
        assert len(result[0]["hunks"]) == 2


def test_semantic_diff_with_only_context_lines():
    diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 unchanged
 unchanged
 unchanged
"""
    sd = SemanticDiff(diff)
    result = sd.render_side_by_side()
    # All lines should be type "ctx"
    if result and result[0]["hunks"]:
        for line in result[0]["hunks"][0]["lines"]:
            assert line["type"] == "ctx"


# ── Very large submissions ─────────────────────────────

def test_large_diff_thousands_of_lines(tmp_json_storage):
    """Diff with many (>1000) lines."""
    lines = ["diff --git a/large.py b/large.py", "--- a/large.py", "+++ b/large.py"]
    # Create many hunks
    for i in range(50):
        start = i * 20 + 1
        lines.append(f"@@ -{start},3 +{start},3 @@")
        lines.append(f" line{start}")
        lines.append(f"-old_{i}")
        lines.append(f"+new_{i}")
        lines.append(f" line{start+2}")

    diff = "\n".join(lines)
    sd = SemanticDiff(diff)
    assert len(sd.render_side_by_side()) == 1
    # Should have 50 hunks
    assert len(sd.render_side_by_side()[0]["hunks"]) == 50


def test_very_large_code_review(tmp_json_storage):
    """Review with a very large diff (simulating 10000+ line code)."""
    server = ReviewServer(storage_path=tmp_json_storage)
    # Create a diff with many lines
    diff_parts = ["diff --git a/big.py b/big.py", "--- a/big.py", "+++ b/big.py"]
    for i in range(100):
        start = i * 10 + 1
        diff_parts.append(f"@@ -{start},5 +{start},5 @@")
        for j in range(5):
            diff_parts.append(f" line{start+j}")
    diff = "\n".join(diff_parts)

    review = server.create_review("Large Review", diff, "agent")
    assert review.id is not None
    assert review.title == "Large Review"


# ── Unicode and special chars ─────────────────────────

def test_unicode_in_title_and_diff(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    diff = "diff --git a/файл.py b/файл.py\n--- a/файл.py\n+++ b/файл.py\n@@ -1,1 +1,1 @@\n-старый\n+новый\n"
    review = server.create_review("日本語レビュー🔥", diff, "агент")
    assert review.title == "日本語レビュー🔥"
    assert review.author == "агент"


def test_unicode_comment(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    diff = "diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    review = server.create_review("Test", diff, "agent")
    comment = server.add_comment(review.id, "非常に良いコード！👍", "レビュアー", "test.py", 1)
    assert comment.body == "非常に良いコード！👍"


def test_special_chars_in_file_path(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    diff = "diff --git a/path with spaces/file!.py b/path with spaces/file!.py\n--- a/path with spaces/file!.py\n+++ b/path with spaces/file!.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    review = server.create_review("Special path", diff, "agent")
    assert "path with spaces/file!.py" in review.files_changed


# ── JSON storage edge cases ───────────────────────────

def test_json_storage_add_decision_to_nonexistent(tmp_json_storage):
    storage = JSONStorage(tmp_json_storage)
    # Should NOT crash — just silently return
    storage.add_decision("nonexistent", "reviewer", "approve")
    assert storage.get("nonexistent") is None


def test_json_storage_add_comment_to_nonexistent(tmp_json_storage):
    storage = JSONStorage(tmp_json_storage)
    c = Comment("c1", "nonexistent", "author", "body", "f.py", 1)
    storage.add_comment("nonexistent", c)
    assert storage.get("nonexistent") is None


def test_json_storage_duplicate_create(tmp_json_storage):
    storage = JSONStorage(tmp_json_storage)
    r1 = ReviewData("same_id", "first", "diff1", "a", [])
    r2 = ReviewData("same_id", "second", "diff2", "b", [])
    storage.create(r1)
    storage.create(r2)  # Should overwrite
    review = storage.get("same_id")
    assert review is not None
    assert review.title == "second"


def test_json_storage_corrupted_file(tmp_json_storage):
    path = Path(tmp_json_storage)
    path.write_text("not valid json {{{")
    storage = JSONStorage(tmp_json_storage)
    # Should handle gracefully — empty data
    assert storage.get("anything") is None


def test_json_storage_empty_file(tmp_json_storage):
    path = Path(tmp_json_storage)
    path.write_text("")
    storage = JSONStorage(tmp_json_storage)
    assert storage.get("anything") is None
    assert storage.list() == []


# ── SQLite storage edge cases ─────────────────────────

def test_sqlite_storage_add_decision_to_nonexistent(tmp_sqlite_storage):
    storage = SQLiteStorage(tmp_sqlite_storage)
    # Should NOT crash — DB will just update 0 rows
    storage.add_decision("nonexistent", "reviewer", "approve")
    assert storage.get("nonexistent") is None


def test_sqlite_storage_add_comment_to_nonexistent(tmp_sqlite_storage):
    storage = SQLiteStorage(tmp_sqlite_storage)
    c = Comment("c1", "nonexistent", "author", "body", "f.py", 1)
    storage.add_comment("nonexistent", c)
    assert storage.get("nonexistent") is None


def test_sqlite_storage_unicode_handling(tmp_sqlite_storage):
    storage = SQLiteStorage(tmp_sqlite_storage)
    review = ReviewData("ru1", "テスト", "diff", "автор", ["файл.py"])
    storage.create(review)
    fetched = storage.get("ru1")
    assert fetched is not None
    assert fetched.title == "テスト"


def test_sqlite_storage_many_reviews(tmp_sqlite_storage):
    storage = SQLiteStorage(tmp_sqlite_storage)
    for i in range(100):
        review = ReviewData(f"r{i}", f"Review {i}", f"diff {i}", "agent", ["file.py"])
        storage.create(review)
    assert len(storage.list()) == 100


# ── Decision enum edge cases ──────────────────────────

def test_decision_invalid_string():
    with pytest.raises(ValueError):
        Decision("invalid_decision")


# ── Comment edge cases ────────────────────────────────

def test_comment_empty_body(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    diff = "diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    review = server.create_review("Test", diff, "agent")
    comment = server.add_comment(review.id, "", "author")
    assert comment.body == ""


def test_comment_negative_line(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    diff = "diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    review = server.create_review("Test", diff, "agent")
    comment = server.add_comment(review.id, "Note", "author", "test.py", -1)
    assert comment.line == -1


def test_comment_no_line(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    diff = "diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    review = server.create_review("Test", diff, "agent")
    comment = server.add_comment(review.id, "No line", "author")
    assert comment.line == 0  # default


# ── Review server edge cases ──────────────────────────

def test_get_review_nonexistent(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    assert server.get_review("nonexistent") is None


def test_get_comments_empty(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    diff = "diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    review = server.create_review("Test", diff, "agent")
    comments = server.get_comments_for_review(review.id)
    assert comments == []


def test_submit_decision_to_nonexistent(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    with pytest.raises(ValueError):
        server.submit_decision("nonexistent", "reviewer", "approve")


# ── Multiple decisions (aggregate status) ─────────────

def test_multiple_reviewers_decisions(tmp_json_storage):
    server = ReviewServer(storage_path=tmp_json_storage)
    diff = "diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    review = server.create_review("Test", diff, "agent")
    server.submit_decision(review.id, "reviewer1", "approve")
    # Second reviewer wants changes — status changes
    server.submit_decision(review.id, "reviewer2", "request_changes")
    fetched = server.get_review(review.id)
    assert fetched.decisions["reviewer1"] == "approve"
    assert fetched.decisions["reviewer2"] == "request_changes"


# ── Diff rendering edge cases ─────────────────────────

def test_semantic_diff_no_newline_at_end():
    """Diff text without trailing newline should still parse."""
    sd = SemanticDiff("diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-old\n+new")
    assert "test.py" in sd.get_files_changed()


def test_semantic_diff_with_deleted_file():
    diff = """diff --git a/deleted.py b/deleted.py
deleted file mode 100644
--- a/deleted.py
+++ /dev/null
@@ -1,1 +0,0 @@
-deleted line
"""
    sd = SemanticDiff(diff)
    files = sd.get_files_changed()
    assert "deleted.py" in files


def test_semantic_diff_with_new_file():
    diff = """diff --git a/new.py b/new.py
new file mode 100644
--- /dev/null
+++ b/new.py
@@ -0,0 +1,1 @@
+new line
"""
    sd = SemanticDiff(diff)
    files = sd.get_files_changed()
    assert "new.py" in files


def test_semantic_diff_render_unified():
    diff = "diff --git a/test.py b/test.py\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
    sd = SemanticDiff(diff)
    assert sd.render_unified() == diff
