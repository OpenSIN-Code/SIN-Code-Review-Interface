# `diff.py` — Semantic Diff Processing

What this file does: parses unified diff text into structured `DiffFile` / `DiffHunk` objects and renders them in two ways: side-by-side (line pairs for the UI) and unified (the original text, unchanged).

## Dependency map

- Imports: stdlib `re`, `dataclasses`, `typing`.
- Imported by: `.server` (get_review endpoint), `.api/diff` (parse endpoint), `cli` (lazy import for the `diff` command).

## Public API

| Symbol             | Purpose                                                          |
|--------------------|------------------------------------------------------------------|
| `DiffHunk`         | One hunk: old_start, old_lines, new_start, new_lines, lines      |
| `DiffFile`         | One file's diff: old_path, new_path, list of hunks               |
| `SemanticDiff(text)` | Parse unified diff text into `self.files`                      |
| `.get_files_changed()` | List of changed file paths (strips `a/`/`b/` prefixes)        |
| `.render_side_by_side()` | Line pairs for the UI: `[{old, new, old_line, new_line, type}]` |
| `.render_unified()` | Returns the original diff text (no transformation)              |

## Important config / limits

- **Parses standard `git diff` output.** Non-standard diff formats (e.g. `diff -u` with a custom header) may not parse cleanly.
- **Hunk header regex: `@@ -<a>[,<b>] +<c>[,<d>] @@`.** Both line counts default to 1 when omitted (per the unified diff spec).
- **`/dev/null`** is used as a sentinel for added (`old_path`) or deleted (`new_path`) files. `get_files_changed` resolves this to the other side.
- **Side-by-side output preserves leading `+`/`-`/` ` semantics.** Context lines (` `) appear on both sides; add/del lines appear on one side only.
- **`render_unified()` is a no-op** — it returns the input text unchanged. Provided for API symmetry.

## Design decisions

- **Why strip `a/`/`b/` prefixes in `get_files_changed`?** Git's diff format prefixes paths with `a/` and `b/`. Stripping makes the output match what other tools (and humans) expect.
- **Why are `old_line` / `new_line` `None` for context-less lines?** "No newline at end of file" and similar metadata lines don't correspond to a source line. `None` is the cleanest way to express "not anchored".
- **Why no incremental parsing?** Diffs are small (KBs to a few MBs at most), and the parser is O(n) on the input size. Incremental parsing would complicate the API for no measurable win.
- **Why a `_parse` method instead of `__init__`?** The constructor returns a fully-initialized object; `_parse` is the implementation detail. External code should never call `_parse` directly.

## Usage example

```python
from sin_code_review_interface.diff import SemanticDiff

diff_text = """\
diff --git a/foo.py b/foo.py
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,3 @@
 def greet(name):
-    return f"hi {name}"
+    return f"hello {name}"
"""

sd = SemanticDiff(diff_text)
print(sd.get_files_changed())         # ["foo.py"]
print(sd.render_side_by_side()[0]["hunks"][0]["lines"][0])
# {"old": "    return f\"hi {name}\"", "new": "", "old_line": 2, "new_line": None, "type": "del"}
```

## Caveats / footguns

- **Binary diffs are not handled.** The parser expects text diffs; binary diffs (with `GIT binary patch` markers) produce empty `lines` lists.
- **`render_side_by_side` doesn't merge adjacent hunks** in the same file. The UI is expected to display them as separate blocks.
- **`old_path == new_path` for modified files**; `old_path == "/dev/null"` for added; `new_path == "/dev/null"` for deleted. Code that doesn't handle all three will mis-render rename/edge cases.
