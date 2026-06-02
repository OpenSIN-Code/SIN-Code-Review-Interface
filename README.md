# SIN-Code Review Interface

> Human-centered review interface for agent-generated code. Provides a programmatic API (CLI + library + web UI) that can be consumed by both humans and agents via MCP.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](./LICENSE)

Part of the [SIN-Code](https://github.com/OpenSIN-Code) agent-engineering stack. Install all subsystems together via the [SIN-Code Bundle](https://github.com/OpenSIN-Code/SIN-Code-Bundle).

## Features

- **ReviewServer** — create, store, and manage code reviews programmatically
- **FastAPI server** — REST endpoints for creating reviews, adding comments, and submitting decisions
- **HTML UI** — side-by-side diff view with comments and decision status
- **Semantic diff** — automatic file-change detection from unified diff text
- **SQLite/JSON storage** — choose persistence backend via file extension
- **MCP server** — expose review tools to AI agents via the Model Context Protocol

## Installation

```bash
pip install -e .
```

Optional MCP server support:
```bash
pip install -e ".[mcp]"
```

See [INSTALL.md](./INSTALL.md) for detailed setup instructions.

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

# List reviews
for r in server.list_reviews():
    print(r.id, r.title, r.status)
```

### FastAPI Server

```bash
# Start the review server
sin-review serve --host 0.0.0.0 --port 8000
```

Endpoints:
- `POST /reviews` — create review
- `GET /reviews` — list reviews
- `GET /reviews/{id}` — review details + side-by-side diff
- `POST /reviews/{id}/comments` — add comment
- `POST /reviews/{id}/decisions` — submit decision
- `GET /reviews/{id}/ui` — HTML review page

### CLI

```bash
# Start the review server
sin-review serve --host 0.0.0.0 --port 8000

# Generate semantic diff as HTML
sin-review diff file_a.py file_b.py --out report.html
```

## Testing

```bash
pytest tests/ -v
```

## MCP Server

Run the MCP server for agent integration:

```bash
python -m sin_code_review_interface.mcp_server
```

Tools exposed:
- `create_review(title, diff, author, files_changed)` — create a new review
- `add_comment(review_id, body, author, file, line)` — add a comment to a review
- `list_pending_reviews()` — list all reviews with status PENDING
- `submit_decision(review_id, reviewer, decision)` — submit a review decision

## Integration

The Review Interface is designed to work as part of the SIN-Code ecosystem:

- **SIN-Code Bundle** — orchestrates all subsystems from a single CLI (`sin`)
- **Intent-Based Diffing (IBD)** — enrich reviews with intent and risk scores
- **Orchestration** — pause agent workflows for human review
- **Verification Oracle** — attach verification verdicts to review comments

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

MIT — see [LICENSE](./LICENSE).
