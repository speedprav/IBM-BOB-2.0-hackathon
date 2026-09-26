"""
Diff / change parser — extract changed files and symbols from a unified diff.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class ChangedHunk:
    file: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    added_lines: List[str]
    removed_lines: List[str]


@dataclass
class ParsedDiff:
    changed_files: List[str]
    hunks: List[ChangedHunk]
    raw: str

    @property
    def summary(self) -> str:
        added = sum(len(h.added_lines) for h in self.hunks)
        removed = sum(len(h.removed_lines) for h in self.hunks)
        return f"+{added} -{removed} lines across {len(self.changed_files)} file(s)"


_FILE_HEADER = re.compile(r'^(?:\+\+\+|---)\s+(?:b/|a/)?(.+)$', re.MULTILINE)
_HUNK_HEADER = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', re.MULTILINE)


def parse_diff(diff_text: str) -> ParsedDiff:
    """Parse a unified diff into structured change information."""
    if not diff_text or not diff_text.strip():
        return ParsedDiff(changed_files=[], hunks=[], raw=diff_text or '')

    changed_files: List[str] = []
    hunks: List[ChangedHunk] = []

    lines = diff_text.splitlines()
    current_file: Optional[str] = None
    i = 0

    while i < len(lines):
        line = lines[i]

        # Detect +++ header (new file path)
        if line.startswith('+++ '):
            path = line[4:].strip()
            # Strip a/ or b/ prefix
            for prefix in ('b/', 'a/'):
                if path.startswith(prefix):
                    path = path[len(prefix):]
                    break
            current_file = path
            if current_file not in changed_files:
                changed_files.append(current_file)
            i += 1
            continue

        # Detect hunk header
        m = _HUNK_HEADER.match(line)
        if m and current_file:
            old_start = int(m.group(1))
            old_count = int(m.group(2)) if m.group(2) else 1
            new_start = int(m.group(3))
            new_count = int(m.group(4)) if m.group(4) else 1
            added: List[str] = []
            removed: List[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith('@@') and \
                  not lines[i].startswith('--- ') and not lines[i].startswith('+++ '):
                hline = lines[i]
                if hline.startswith('+') and not hline.startswith('+++'):
                    added.append(hline[1:])
                elif hline.startswith('-') and not hline.startswith('---'):
                    removed.append(hline[1:])
                i += 1
            hunks.append(ChangedHunk(
                file=current_file,
                old_start=old_start,
                old_count=old_count,
                new_start=new_start,
                new_count=new_count,
                added_lines=added,
                removed_lines=removed,
            ))
            continue

        i += 1

    return ParsedDiff(changed_files=changed_files, hunks=hunks, raw=diff_text)


def extract_changed_symbols_from_diff(diff: ParsedDiff, file_symbols: dict) -> List[str]:
    """
    Given a parsed diff and a map of file→symbols, return names of symbols
    whose definition lines overlap with the changed hunks.
    """
    changed_symbol_names: List[str] = []

    for hunk in diff.hunks:
        file_path = hunk.file
        symbols = file_symbols.get(file_path, [])
        for sym in symbols:
            if sym.kind == 'import':
                continue
            # Check if the hunk's old range overlaps with the symbol's line
            if _line_in_range(sym.line, hunk.old_start, hunk.old_count):
                if sym.name not in changed_symbol_names:
                    changed_symbol_names.append(sym.name)

    return changed_symbol_names


def _line_in_range(line: int, start: int, count: int) -> bool:
    return start <= line <= start + max(count, 10)
