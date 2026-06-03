"""Diff API routes.

Exposes `POST /diff/parse` to parse a unified diff into structured
side-by-side data. The frontend uses this to render diffs without
needing its own parser.

Docs: diff.doc.md
"""
from fastapi import APIRouter, Request
from sin_code_review_interface.diff import SemanticDiff

router = APIRouter()

@router.post("/diff/parse")
async def parse_diff(request: Request):
    """Parse a unified diff into files-changed + side-by-side line pairs.

    Request body: `{"diff": "<unified diff text>"}`.

    Returns:
        `{"files_changed": [...], "side_by_side": [...]}`.
        See `SemanticDiff.get_files_changed` and `render_side_by_side`.
    """
    data = await request.json()
    diff_text = data.get("diff", "")
    sd = SemanticDiff(diff_text)
    return {
        "files_changed": sd.get_files_changed(),
        "side_by_side": sd.render_side_by_side()
    }
