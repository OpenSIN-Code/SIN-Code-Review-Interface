from fastapi.testclient import TestClient
from sin_code_review_interface.server import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_root_serves_html():
    r = client.get("/")
    assert r.status_code == 200
    assert "SIN-Code Semantic Review" in r.text
