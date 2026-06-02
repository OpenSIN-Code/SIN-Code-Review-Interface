# SIN-Code-Review-Interface

Human-centered review interface for agent-generated code. Provides a programmatic API (CLI + library + web UI) that can be consumed by both humans and agents via MCP.

## Quick Start

```bash
pip install -e ".[dev]"
pytest
```

## Usage

### Library

```python
from sin_code_review_interface import ReviewServer, Decision

server = ReviewServer(storage_path="reviews.db")
review = server.create_review(
    title="Implement auth flow",
    diff="...diff content...",
    author="agent-claude",
    files_changed=["auth.py", "test_auth.py"]
)
server.add_comment(review.id, "Use bcrypt", "jeremy", "auth.py", 42)
server.submit_decision(review.id, "jeremy", Decision.APPROVE)
```

### FastAPI Server

```bash
python -c "from sin_code_review_interface.server import get_app; import uvicorn; uvicorn.run(get_app(), host='0.0.0.0', port=8000)"
```

Endpoints:
- `POST /reviews` — create review
- `GET /reviews` — list reviews
- `GET /reviews/{id}` — review details + side-by-side diff
- `POST /reviews/{id}/comments` — add comment
- `POST /reviews/{id}/decisions` — submit decision
- `GET /reviews/{id}/ui` — HTML review page

### MCP Server

```python
from sin_code_review_interface.mcp_server import MCPReviewServer
mcp = MCPReviewServer()
mcp.create_review(title="...", diff="...")
```

Tools exposed:
- `create_review`
- `add_comment`
- `list_pending_reviews`
- `submit_decision`

## Architecture

```
┌─────────────────────────────────────────┐
│  SIN-Code-Review-Interface              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │  Server  │ │   API    │ │   MCP    │  │
│  │  (Fast)  │ │  (REST)  │ │ (Tools)  │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       └─────────────┴─────────────┘        │
│              Storage (SQLite/JSON)         │
└─────────────────────────────────────────┘
```

## License
MIT
