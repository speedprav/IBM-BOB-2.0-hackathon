"""
Repository scanner — deterministic file discovery and filtering.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


SUPPORTED_EXTENSIONS = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.jsx': 'javascript',
    '.java': 'java',
    '.go': 'go',
    '.rb': 'ruby',
    '.rs': 'rust',
}

IGNORE_DIRS = {
    '__pycache__', '.git', 'node_modules', '.venv', 'venv',
    'env', 'dist', 'build', '.mypy_cache', '.pytest_cache',
    '.tox', 'coverage', '.coverage',
}

IGNORE_FILES = {'.DS_Store', 'Thumbs.db'}


@dataclass
class ScannedFile:
    path: str               # relative to project root
    abs_path: str
    language: str
    size_bytes: int
    lines: int
    content: str


@dataclass
class ScanResult:
    project_root: str
    files: List[ScannedFile] = field(default_factory=list)
    doc_files: List[str] = field(default_factory=list)   # README, docs
    test_files: List[str] = field(default_factory=list)

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def total_lines(self) -> int:
        return sum(f.lines for f in self.files)


def scan_repository(project_root: str) -> ScanResult:
    """Recursively scan a project directory and return all source files."""
    result = ScanResult(project_root=project_root)

    if not os.path.isdir(project_root):
        # Project directory not found (e.g. Vercel serverless) — return empty result
        # The orchestrator will use demo/AI mode with the diff text only
        return result

    for dirpath, dirnames, filenames in os.walk(project_root):
        # Prune ignored directories in place
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for filename in filenames:
            if filename in IGNORE_FILES:
                continue
            abs_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(abs_path, project_root).replace('\\', '/')

            ext = os.path.splitext(filename)[1].lower()
            lower_name = filename.lower()

            # Documentation files
            if lower_name in ('readme.md', 'readme.rst', 'readme.txt') or \
               rel_path.startswith('docs/') or rel_path.startswith('doc/'):
                try:
                    content = _read_file(abs_path)
                    result.doc_files.append(rel_path)
                except OSError:
                    pass
                continue

            # Source files
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            try:
                content = _read_file(abs_path)
            except OSError:
                continue

            scanned = ScannedFile(
                path=rel_path,
                abs_path=abs_path,
                language=SUPPORTED_EXTENSIONS[ext],
                size_bytes=os.path.getsize(abs_path),
                lines=content.count('\n') + 1,
                content=content,
            )
            result.files.append(scanned)

            # Mark test files
            if _is_test_file(rel_path, filename):
                result.test_files.append(rel_path)

    return result


def _is_test_file(rel_path: str, filename: str) -> bool:
    name_lower = filename.lower()
    return (
        name_lower.startswith('test_') or
        name_lower.endswith('_test.py') or
        name_lower.endswith('.test.ts') or
        name_lower.endswith('.spec.ts') or
        rel_path.startswith('tests/') or
        '/tests/' in rel_path or
        '/test/' in rel_path
    )


def _read_file(abs_path: str) -> str:
    with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def get_file_content(project_root: str, rel_path: str) -> Optional[str]:
    """Read a single file relative to project_root."""
    abs_path = os.path.normpath(os.path.join(project_root, rel_path))
    # Security: ensure the resolved path stays inside project_root
    if not abs_path.startswith(os.path.normpath(project_root)):
        raise ValueError(f"Path traversal detected: {rel_path}")
    try:
        return _read_file(abs_path)
    except OSError:
        return None
