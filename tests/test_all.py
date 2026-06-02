import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sin_code_review_interface import ReviewServer, Decision, SemanticDiff, Comment, get_app
from sin_code_review_interface.storage import JSONStorage, SQLiteStorage, ReviewData
from sin_code_review_interface.mcp_server import MCPReviewServer

# ── Fixtures ──────────────────────────────────

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

@pytest.fixture
def sample_diff():
    return """diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,5 +1,5 @@
 def login():
-    password = "plain"
+    password = hash_password("plain")
     return password
@@ -10,3 +10,4 @@
 def logout():
     session.clear()
+    audit_log("logout")
"""

# ── Storage tests ─────────────────────────────

def test_json_storage_create(tmp_json_storage):
    storage = JSONStorage(tmp_json_storage)
    review = ReviewData("r1", "title", "diff", "agent", ["a.py"])
    storage.create(review)
    assert storage.get("r1") is not None

def test_json_storage_get_missing(tmp_json_storage):
    storage = JSONStorage(tmp_json_storage)
    assert storage.get("missing") is None

def test_json_storage_list(tmp_json_storage):
    storage = JSONStorage(tmp_json_storage)
    storage.create(ReviewData("r1", "t1", "d", "a", ["f1"]))
    storage.create(ReviewData("r2", "t2", "d", "a", ["f2"]))
    assert len(storage.list()) == 2

def test_json_storage_add_comment(tmp_json_storage):
    storage = JSONStorage(tmp_json_storage)
    storage.create(ReviewData("r1", "t", "d", "a", ["f"]))
    c = Comment("c1", "r1", "reviewer", "body", "f", 1)
    storage.add_comment("r1", c)
    review = storage.get("r1")
    assert len(review.comments) == 1

def test_json_storage_add_decision(tmp_json_storage):
    storage = JSONStorage(tmp_json_storage)
    storage.create(ReviewData("r1", "t", "d", "a", ["f"]))
    storage.add_decision("r1", "jeremy", "approve")
    review = storage.get("r1")
    assert review.decisions["jeremy"] == "approve"
    assert review.status == "approve"

def test_sqlite_storage_create(tmp_sqlite_storage):
    storage = SQLiteStorage(tmp_sqlite_storage)
    review = ReviewData("r1", "title", "diff", "agent", ["a.py"])
    storage.create(review)
    assert storage.get("r1") is not None

def test_sqlite_storage_get_missing(tmp_sqlite_storage):
    storage = SQLiteStorage(tmp_sqlite_storage)
    assert storage.get("missing") is None

def test_sqlite_storage_add_comment(tmp_sqlite_storage):
    storage = SQLiteStorage(tmp_sqlite_storage)
    storage.create(ReviewData("r1", "t", "d", "a", ["f"]))
    c = Comment("c1", "r1", "reviewer", "body", "f", 1)
    storage.add_comment("r1", c)
    review = storage.get("r1")
    assert len(review.comments) == 1

def test_sqlite_storage_add_decision(tmp_sqlite_storage):
    storage = SQLiteStorage(tmp_sqlite_storage)
    storage.create(ReviewData("r1", "t", "d", "a", ["f"]))
    storage.add_decision("r1", "jeremy", "approve")
    review = storage.get("r1")
    assert review.decisions["jeremy"] == "approve"

# ── Decision enum tests ───────────────────────

def test_decision_values():
    assert Decision.APPROVE == "approve"
    assert Decision.REQUEST_CHANGES == "request_changes"
    assert Decision.COMMENT == "comment"
    assert Decision.PENDING == "pending"

def test_decision_from_string():
    assert Decision("approve") == Decision.APPROVE
    assert Decision("request_changes") == Decision.REQUEST_CHANGES

# ── Diff tests ────────────────────────────────

def test_semantic_diff_parse_files(sample_diff):
    sd = SemanticDiff(sample_diff)
    files = sd.get_files_changed()
    assert "auth.py" in files

def test_semantic_diff_render_side_by_side(sample_diff):
    sd = SemanticDiff(sample_diff)
    result = sd.render_side_by_side()
    assert len(result) > 0
    assert "hunks" in result[0]

def test_semantic_diff_empty():
    sd = SemanticDiff("")
    assert sd.get_files_changed() == []

# ── ReviewServer tests ────────────────────────

def test_create_review(tmp_json_storage, sample_diff):
    server = ReviewServer(storage_path=tmp_json_storage)
    review = server.create_review("Implement auth", sample_diff, "agent")
    assert review.title == "Implement auth"
    assert review.author == "agent"
    assert "auth.py" in review.files_changed

def test_get_review(tmp_json_storage, sample_diff):
    server = ReviewServer(storage_path=tmp_json_storage)
    review = server.create_review("Implement auth", sample_diff, "agent")
    fetched = server.get_review(review.id)
    assert fetched is not None
    assert fetched.id == review.id

def test_list_reviews(tmp_json_storage, sample_diff):
    server = ReviewServer(storage_path=tmp_json_storage)
    server.create_review("R1", sample_diff, "agent")
    server.create_review("R2", sample_diff, "agent")
    assert len(server.list_reviews()) == 2

def test_add_comment(tmp_json_storage, sample_diff):
    server = ReviewServer(storage_path=tmp_json_storage)
    review = server.create_review("Implement auth", sample_diff, "agent")
    comment = server.add_comment(review.id, "Use bcrypt", "jeremy", "auth.py", 42)
    assert comment.body == "Use bcrypt"
    assert comment.file == "auth.py"
    assert comment.line == 42

def test_submit_decision(tmp_json_storage, sample_diff):
    server = ReviewServer(storage_path=tmp_json_storage)
    review = server.create_review("Implement auth", sample_diff, "agent")
    server.submit_decision(review.id, "jeremy", Decision.APPROVE)
    fetched = server.get_review(review.id)
    assert fetched.decisions["jeremy"] == "approve"
    assert fetched.status == "approve"

def test_get_comments(tmp_json_storage, sample_diff):
    server = ReviewServer(storage_path=tmp_json_storage)
    review = server.create_review("Implement auth", sample_diff, "agent")
    server.add_comment(review.id, "Note 1", "a")
    server.add_comment(review.id, "Note 2", "b")
    assert len(server.get_comments_for_review(review.id)) == 2

# ── API endpoint tests ──────────────────────────

@pytest.fixture
def client(tmp_json_storage):
    from fastapi.testclient import TestClient
    app = get_app(tmp_json_storage)
    return TestClient(app)

def test_api_create_review(client, sample_diff):
    res = client.post("/reviews", json={"title": "Test", "diff": sample_diff, "author": "agent"})
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Test"
    assert "id" in data

def test_api_list_reviews(client, sample_diff):
    client.post("/reviews", json={"title": "T1", "diff": sample_diff, "author": "a"})
    client.post("/reviews", json={"title": "T2", "diff": sample_diff, "author": "b"})
    res = client.get("/reviews")
    assert res.status_code == 200
    assert len(res.json()) == 2

def test_api_get_review(client, sample_diff):
    r = client.post("/reviews", json={"title": "T", "diff": sample_diff, "author": "a"})
    rid = r.json()["id"]
    res = client.get(f"/reviews/{rid}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == rid
    assert "side_by_side" in data

def test_api_add_comment(client, sample_diff):
    r = client.post("/reviews", json={"title": "T", "diff": sample_diff, "author": "a"})
    rid = r.json()["id"]
    res = client.post(f"/reviews/{rid}/comments", json={"body": "Note", "author": "human", "file": "a.py", "line": 1})
    assert res.status_code == 200
    assert res.json()["body"] == "Note"

def test_api_submit_decision(client, sample_diff):
    r = client.post("/reviews", json={"title": "T", "diff": sample_diff, "author": "a"})
    rid = r.json()["id"]
    res = client.post(f"/reviews/{rid}/decisions", json={"reviewer": "human", "decision": "approve"})
    assert res.status_code == 200
    assert res.json()["decision"] == "approve"

def test_api_get_review_not_found(client):
    res = client.get("/reviews/invalid-id")
    assert res.status_code == 404

def test_api_web_ui(client, sample_diff):
    r = client.post("/reviews", json={"title": "T", "diff": sample_diff, "author": "a"})
    rid = r.json()["id"]
    res = client.get(f"/reviews/{rid}/ui")
    assert res.status_code == 200
    assert "<html" in res.text

# ── MCP server tests ────────────────────────────

def test_mcp_create_review(tmp_json_storage, sample_diff):
    mcp = MCPReviewServer(tmp_json_storage)
    result = mcp.create_review("Title", sample_diff, "agent")
    assert "id" in result
    assert result["status"] == "pending"

def test_mcp_add_comment(tmp_json_storage, sample_diff):
    mcp = MCPReviewServer(tmp_json_storage)
    r = mcp.create_review("T", sample_diff, "agent")
    result = mcp.add_comment(r["id"], "Note", "human", "f.py", 1)
    assert result["body"] == "Note"
    assert result["line"] == 1

def test_mcp_list_pending(tmp_json_storage, sample_diff):
    mcp = MCPReviewServer(tmp_json_storage)
    mcp.create_review("T", sample_diff, "agent")
    pending = mcp.list_pending_reviews()
    assert len(pending) == 1

def test_mcp_submit_decision(tmp_json_storage, sample_diff):
    mcp = MCPReviewServer(tmp_json_storage)
    r = mcp.create_review("T", sample_diff, "agent")
    result = mcp.submit_decision(r["id"], "human", "approve")
    assert result["decision"] == "approve"

def test_mcp_get_tools(tmp_json_storage):
    mcp = MCPReviewServer(tmp_json_storage)
    tools = mcp.get_tools()
    names = [t["name"] for t in tools]
    assert "create_review" in names
    assert "add_comment" in names
    assert "list_pending_reviews" in names
    assert "submit_decision" in names

def test_mcp_invoke_tool(tmp_json_storage, sample_diff):
    mcp = MCPReviewServer(tmp_json_storage)
    result = mcp.invoke_tool("create_review", {"title": "T", "diff": sample_diff, "author": "agent"})
    assert "id" in result

def test_mcp_invoke_tool_unknown(tmp_json_storage):
    mcp = MCPReviewServer(tmp_json_storage)
    with pytest.raises(ValueError):
        mcp.invoke_tool("unknown_tool", {})

# ── README / integration sanity ─────────────────

def test_package_imports():
    from sin_code_review_interface import ReviewServer, Decision, SemanticDiff, Comment, Thread
    assert ReviewServer is not None
    assert Decision is not None
