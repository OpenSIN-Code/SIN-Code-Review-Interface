"""Semantic diff processing.

Parses unified diff text into structured `DiffFile` / `DiffHunk` objects
and renders them in two ways: side-by-side (line pairs for the UI) and
unified (the original text, unchanged).

Docs: diff.doc.md
"""
import re
from dataclasses import dataclass
from typing import List, Tuple


# ── Data models ────────────────────────────────────────────────────────
@dataclass
class DiffHunk:
    """A single hunk of a diff.

    `old_start`/`old_lines` and `new_start`/`new_lines` come from the
    `@@ -<a>[,<b>] +<c>[,<d>] @@` header. `lines` is the raw hunk body
    (each line still starts with `+`/`-`/` `).
    """
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[str]


@dataclass
class DiffFile:
    """Diff for a single file.

    `old_path` may be `/dev/null` for new files; `new_path` may be
    `/dev/null` for deleted files. `get_files_changed()` resolves that.
    """
    old_path: str
    new_path: str
    hunks: List[DiffHunk]


# ── Parser / renderer ─────────────────────────────────────────────────
class SemanticDiff:
    """Parse and render unified diffs semantically.

    Construction parses the input; the parsed structure lives on
    `self.files` and is queryable via `get_files_changed()` and
    `render_side_by_side()`.
    """

    def __init__(self, diff_text: str):
        self.diff_text = diff_text
        self.files: List[DiffFile] = []
        self._parse()

    def _parse(self) -> None:
        """Parse unified diff text into a list of `DiffFile` objects.

        Handles the standard `git diff` output: `diff --git` headers,
        `--- a/path` / `+++ b/path` pairs, and `@@ -a,b +c,d @@` hunk
        headers. Anything else inside a hunk is appended verbatim to
        `hunk.lines`.
        """
        lines = self.diff_text.splitlines()
        current_file = None
        current_hunk = None
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("diff --git"):
                # Start of a new file diff — flush the previous one.
                if current_file:
                    self.files.append(current_file)
                current_file = None
                current_hunk = None
            elif line.startswith("--- "):
                # `--- a/path\t<timestamp>` — strip the optional tab+timestamp.
                old_path = line[4:].split("\t")[0]
                # Peek ahead: `+++ b/path` MUST follow to make this a valid pair.
                if i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
                    new_path = lines[i + 1][4:].split("\t")[0]
                    current_file = DiffFile(old_path=old_path, new_path=new_path, hunks=[])
                    i += 1  # consume the `+++` line
            elif line.startswith("@@") and current_file is not None:
                # Hunk header — flush the previous hunk first.
                if current_hunk:
                    current_file.hunks.append(current_hunk)
                # `@@ -<a>[,<b>] +<c>[,<d>] @@` — both line counts are optional
                # in the spec (default 1 when omitted).
                match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
                if match:
                    old_start = int(match.group(1))
                    old_lines = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_lines = int(match.group(4)) if match.group(4) else 1
                    current_hunk = DiffHunk(
                        old_start=old_start,
                        old_lines=old_lines,
                        new_start=new_start,
                        new_lines=new_lines,
                        lines=[]
                    )
            elif current_hunk is not None:
                # Plain hunk body line — keep the leading `+`/`-`/` `
                # so renderers can distinguish add/del/context.
                current_hunk.lines.append(line)
            i += 1
        # Flush the trailing file/hunk after the loop.
        if current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            self.files.append(current_file)

    def get_files_changed(self) -> List[str]:
        """Return the list of file paths changed in the diff.

        - For added files: returns `new_path` (old is `/dev/null`).
        - For deleted files: returns `old_path` (new is `/dev/null`).
        - Strips the leading `a/` / `b/` from `git diff` paths.
        """
        files = []
        for f in self.files:
            path = f.new_path if f.new_path != "/dev/null" else f.old_path
            if path.startswith("a/") or path.startswith("b/"):
                path = path[2:]
            files.append(path)
        return files

    def render_side_by_side(self) -> List[dict]:
        """Render hunks as side-by-side line pairs for the UI.

        Each line in the output is a dict:
            {"old", "new", "old_line", "new_line", "type": "add"|"del"|"ctx"|"info"}

        `add` lines have a `new_line` number but no `old_line`;
        `del` lines are the reverse. `ctx` (context) lines have both.
        `info` lines (e.g. "No newline at end of file") have neither.
        """
        result = []
        for f in self.files:
            file_result = {"old_path": f.old_path, "new_path": f.new_path, "hunks": []}
            for hunk in f.hunks:
                hunk_lines = []
                # Line counters start at the hunk header's start values.
                old_line = hunk.old_start
                new_line = hunk.new_start
                for line in hunk.lines:
                    if line.startswith("+"):
                        hunk_lines.append({"old": "", "new": line[1:], "old_line": None, "new_line": new_line, "type": "add"})
                        new_line += 1
                    elif line.startswith("-"):
                        hunk_lines.append({"old": line[1:], "new": "", "old_line": old_line, "new_line": None, "type": "del"})
                        old_line += 1
                    elif line.startswith(" "):
                        # Context line — same on both sides.
                        hunk_lines.append({"old": line[1:], "new": line[1:], "old_line": old_line, "new_line": new_line, "type": "ctx"})
                        old_line += 1
                        new_line += 1
                    else:
                        # E.g. "\ No newline at end of file" — surface as info.
                        hunk_lines.append({"old": line, "new": line, "old_line": None, "new_line": None, "type": "info"})
                file_result["hunks"].append({"header": f"@@ -{hunk.old_start},{hunk.old_lines} +{hunk.new_start},{hunk.new_lines} @@", "lines": hunk_lines})
            result.append(file_result)
        return result

    def render_unified(self) -> str:
        """Return the original unified diff text (unchanged)."""
        return self.diff_text
