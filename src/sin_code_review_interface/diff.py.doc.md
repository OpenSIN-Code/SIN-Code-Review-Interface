# Semantic diff for code reviews

## What this file does
Parses unified diffs into structured hunks and renders side-by-side or unified views.

## Dependencies
- `re` (stdlib) — hunk header parsing

## Important config values
None; parser is deterministic.

## Design decisions
- Why not use a third-party diff library? Because we want full control over the side-by-side renderer and to avoid heavy dependencies.
- Why line-by-line parsing? Unified diff is a stable format; regex is sufficient.

## Usage
```python
from sin_code_review_interface.diff import SemanticDiff
sd = SemanticDiff(unified_diff_text)
files = sd.get_files_changed()
rendered = sd.render_side_by_side()
```

## Known caveats
- Does not support binary diffs.
- Very large diffs (>10k lines) may be slow in side-by-side mode.
