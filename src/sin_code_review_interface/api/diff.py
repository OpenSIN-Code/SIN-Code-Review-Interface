"""Diff API routes.

Docs: api/diff.doc.md
"""
from fastapi import APIRouter, Request
from sin_code_review_interface.diff import SemanticDiff

router = APIRouter()

@router.post("/diff/parse")
async def parse_diff(request: Request):
    data = await request.json()
    diff_text = data.get("diff", "")
    sd = SemanticDiff(diff_text)
    return {
        "files_changed": sd.get_files_changed(),
        "side_by_side": sd.render_side_by_side()
    }
