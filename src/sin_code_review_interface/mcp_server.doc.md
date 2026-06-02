# `mcp_server.py` — MCP Server for Review Interface

What this file does: exposes code review tools to AI agents via the Model Context Protocol.

## Dependencies

- Imported by: CLI, external MCP hosts
- Imports: `server` (ReviewServer), `decision` (Decision)

## Tools

- `create_review(title, diff, author, files_changed)` — create a new code review
- `add_comment(review_id, body, author, file, line)` — add a comment to a review
- `list_pending_reviews()` — list all reviews with status PENDING
- `submit_decision(review_id, reviewer, decision)` — submit a review decision

## Usage

```bash
python -m sin_code_review_interface.mcp_server
```

Requires `pip install -e ".[mcp]"`.

## Notes

Uses `mcp.server.fastmcp.FastMCP` for tool registration. Decisions are one of `approve`, `request_changes`, `comment`.
