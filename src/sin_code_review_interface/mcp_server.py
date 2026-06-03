"""MCP-compatible wrapper around the ReviewServer.

This module is a thin adapter that exposes the review server's operations
in the Model Context Protocol's tool-call shape. It does NOT use
`mcp.server.fastmcp` directly — instead, it returns tool definitions
(`get_tools()`) and dispatches via `invoke_tool(name, arguments)`. An
MCP client can drive it over any transport that supports those two
calls (e.g. stdio JSON-RPC, HTTP RPC).

Docs: mcp_server.doc.md
"""
from typing import Any, Dict, List
from sin_code_review_interface.server import ReviewServer
from sin_code_review_interface.decision import Decision


# ── MCP server class ───────────────────────────────────────────────────
class MCPReviewServer:
    """MCP-compatible server exposing review tools.

    Wraps a `ReviewServer` and adds the tool schema (`get_tools`) and
    dispatcher (`invoke_tool`) that MCP needs. Each tool maps 1:1 to a
    method on this class.
    """

    def __init__(self, storage_path: str = "reviews.db"):
        # Default storage path is the same SQLite file the standalone
        # server uses; this means a running `sin-review serve` and an
        # MCP client can share state.
        self.server = ReviewServer(storage_path=storage_path)

    def create_review(self, title: str, diff: str, author: str = "agent",
                      files_changed: List[str] = None) -> Dict[str, Any]:
        """Create a new review.

        Args:
            title: Human-readable title of the review.
            diff: Unified diff text.
            author: Who created the review (default: agent).
            files_changed: Optional list of files; inferred from diff if omitted.

        Returns:
            dict with review id, title, author, files_changed, status.
        """
        review = self.server.create_review(title=title, diff=diff, author=author, files_changed=files_changed)
        return {
            "id": review.id,
            "title": review.title,
            "author": review.author,
            "files_changed": review.files_changed,
            "status": review.status
        }

    def add_comment(self, review_id: str, body: str, author: str = "reviewer",
                    file: str = None, line: int = None) -> Dict[str, Any]:
        """Add a comment to a review.

        Args:
            review_id: Target review UUID.
            body: Comment text.
            author: Comment author (default: reviewer).
            file: File path (optional).
            line: Line number (optional).

        Returns:
            dict with comment id, review_id, author, body, file, line.
        """
        comment = self.server.add_comment(review_id=review_id, body=body, author=author, file=file, line=line)
        return {
            "id": comment.id,
            "review_id": review_id,
            "author": comment.author,
            "body": comment.body,
            "file": comment.file,
            "line": comment.line
        }

    def list_pending_reviews(self) -> List[Dict[str, Any]]:
        """List all reviews with status PENDING.

        Returns:
            List of review dicts (id, title, author, files_changed, status).
        """
        reviews = self.server.list_reviews()
        return [
            {"id": r.id, "title": r.title, "author": r.author,
             "files_changed": r.files_changed, "status": r.status}
            for r in reviews if r.status == Decision.PENDING
        ]

    def submit_decision(self, review_id: str, reviewer: str, decision: str) -> Dict[str, Any]:
        """Submit a review decision.

        Args:
            review_id: Target review UUID.
            reviewer: Name of the reviewer.
            decision: One of `approve`, `request_changes`, `comment`.

        Returns:
            dict with review_id, reviewer, decision.

        Raises:
            ValueError: if `decision` is not a valid Decision value
                        (Decision("...") raises on bad input).
        """
        d = Decision(decision)
        self.server.submit_decision(review_id, reviewer, d)
        return {
            "review_id": review_id,
            "reviewer": reviewer,
            "decision": d.value
        }

    # ── MCP dispatch ───────────────────────────────────────────────────
    def get_tools(self) -> List[Dict[str, Any]]:
        """Return the JSON-Schema tool definitions MCP clients need.

        The four tools are: `create_review`, `add_comment`,
        `list_pending_reviews`, `submit_decision`. Each definition
        includes a JSON-Schema for the parameters so clients can
        validate input before calling.
        """
        return [
            {
                "name": "create_review",
                "description": "Create a new code review",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "diff": {"type": "string"},
                        "author": {"type": "string"},
                        "files_changed": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["title", "diff"]
                }
            },
            {
                "name": "add_comment",
                "description": "Add a comment to a review",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "review_id": {"type": "string"},
                        "body": {"type": "string"},
                        "author": {"type": "string"},
                        "file": {"type": "string"},
                        "line": {"type": "integer"}
                    },
                    "required": ["review_id", "body"]
                }
            },
            {
                "name": "list_pending_reviews",
                "description": "List all pending reviews",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "submit_decision",
                "description": "Submit a review decision",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "review_id": {"type": "string"},
                        "reviewer": {"type": "string"},
                        "decision": {"type": "string", "enum": ["approve", "request_changes", "comment"]}
                    },
                    "required": ["review_id", "reviewer", "decision"]
                }
            }
        ]

    def invoke_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Dispatch a tool call to the matching method.

        Args:
            name: Tool name (must be in `get_tools()`).
            arguments: Dict of arguments matching the tool's JSON-Schema.

        Returns:
            Whatever the wrapped method returns.

        Raises:
            ValueError: if `name` is not a known tool.
        """
        if name == "create_review":
            return self.create_review(**arguments)
        elif name == "add_comment":
            return self.add_comment(**arguments)
        elif name == "list_pending_reviews":
            return self.list_pending_reviews()
        elif name == "submit_decision":
            return self.submit_decision(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
