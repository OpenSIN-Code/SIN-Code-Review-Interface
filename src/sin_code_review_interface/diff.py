"""Semantic diff processing.

Docs: diff.py.doc.md
"""
import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class DiffHunk:
    """A single hunk of a diff."""
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    lines: List[str]


@dataclass
class DiffFile:
    """Diff for a single file."""
    old_path: str
    new_path: str
    hunks: List[DiffHunk]


class SemanticDiff:
    """Parse and render unified diffs semantically."""

    def __init__(self, diff_text: str):
        self.diff_text = diff_text
        self.files: List[DiffFile] = []
        self._parse()

    def _parse(self) -> None:
        """Parse unified diff into structured hunks."""
        lines = self.diff_text.splitlines()
        current_file = None
        current_hunk = None
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("diff --git"):
                # Start of a new file diff
                if current_file:
                    self.files.append(current_file)
                current_file = None
                current_hunk = None
            elif line.startswith("--- "):
                old_path = line[4:].split("\t")[0]
                if i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
                    new_path = lines[i + 1][4:].split("\t")[0]
                    current_file = DiffFile(old_path=old_path, new_path=new_path, hunks=[])
                    i += 1
            elif line.startswith("@@") and current_file is not None:
                if current_hunk:
                    current_file.hunks.append(current_hunk)
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
                current_hunk.lines.append(line)
            i += 1
        if current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            self.files.append(current_file)

    def get_files_changed(self) -> List[str]:
        """Return list of file paths changed in the diff."""
        files = []
        for f in self.files:
            path = f.new_path if f.new_path != "/dev/null" else f.old_path
            if path.startswith("a/") or path.startswith("b/"):
                path = path[2:]
            files.append(path)
        return files

    def render_side_by_side(self) -> List[dict]:
        """Render hunks as side-by-side line pairs."""
        result = []
        for f in self.files:
            file_result = {"old_path": f.old_path, "new_path": f.new_path, "hunks": []}
            for hunk in f.hunks:
                hunk_lines = []
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
                        hunk_lines.append({"old": line[1:], "new": line[1:], "old_line": old_line, "new_line": new_line, "type": "ctx"})
                        old_line += 1
                        new_line += 1
                    else:
                        hunk_lines.append({"old": line, "new": line, "old_line": None, "new_line": None, "type": "info"})
                file_result["hunks"].append({"header": f"@@ -{hunk.old_start},{hunk.old_lines} +{hunk.new_start},{hunk.new_lines} @@", "lines": hunk_lines})
            result.append(file_result)
        return result

    def render_unified(self) -> str:
        """Return the original unified diff text."""
        return self.diff_text
