# `mcp_server.py` — MCP-compatible Wrapper

What this file does: a thin adapter that exposes the review server's operations in the Model Context Protocol's tool-call shape. The class returns tool definitions (`get_tools()`) and dispatches via `invoke_tool(name, arguments)` — no use of `mcp.server.fastmcp`.

## Dependency map

- Imports: `typing`, `.server.ReviewServer`, `.decision.Decision`.
- Imported by: external MCP clients (over stdio JSON-RPC, HTTP RPC, etc.).

## Public API

| Symbol                                       | Purpose                                                            |
|----------------------------------------------|--------------------------------------------------------------------|
| `MCPReviewServer(storage_path="reviews.db")` | Construct with the same storage path the standalone server uses.   |
| `.create_review(title, diff, author?, files_changed?)` | Create a review; returns a summary dict.              |
| `.add_comment(review_id, body, author?, file?, line?)` | Add a comment; returns a dict with the new comment id. |
| `.list_pending_reviews()`                    | List reviews with status PENDING.                                  |
| `.submit_decision(review_id, reviewer, decision)` | Submit a review decision.                                     |
| `.get_tools()`                               | Return the JSON-Schema tool definitions (4 tools).                 |
| `.invoke_tool(name, arguments)`              | Dispatch by tool name. Raises `ValueError` on unknown tool.         |

## Important config / limits

- **No `mcp.server.fastmcp` dependency.** This module is a self-contained adapter; wire it to MCP over any transport that supports the two-method contract.
- **Default storage path: `reviews.db`**, same as the standalone server. A running `sin-review serve` and an MCP client can share state.
- **Decision must be a string** matching one of the `Decision` enum values (`"approve"`, `"request_changes"`, `"comment"`). Invalid values raise `ValueError`.
- **Comment body is limited to 64 KB** by the server (enforced in `server.py`).

## Design decisions

- **Why not use `mcp.server.fastmcp` directly?** Two reasons: (1) the tool dispatch (`invoke_tool`) is a clean two-method contract that works over any RPC transport, and (2) keeping the dep out of the base package means MCP is purely an integration concern.
- **Why are tool definitions hand-written JSON Schema?** It's small, stable, and avoids a dependency on `jsonschema` for the producer side. Clients that want to validate can use the schema as-is.
- **Why `storage_path` is shared with the standalone server?** State consistency. If you want isolation, pass a different path.

## Usage example

```python
from sin_code_review_interface.mcp_server import MCPReviewServer

mcp = MCPReviewServer(storage_path="reviews.db")

# Discover available tools
for tool in mcp.get_tools():
    print(tool["name"], tool["description"])

# Call a tool
result = mcp.invoke_tool("create_review", {
    "title": "Refactor auth",
    "diff": "...unified diff...",
    "author": "agent",
})
```

## Caveats / footguns

- **No authentication.** The server trusts whoever can call its methods. Run in a trusted environment.
- **Tool calls can be long** (creating a review involves parsing a diff). Configure your MCP client with a generous request timeout.
- **The server is single-threaded by default.** Concurrent invocations share the same `ReviewServer` instance and therefore the same SQLite connection. SQLite's default journal mode handles this, but heavy concurrency may want an explicit `pool`.
