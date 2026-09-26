"""
Documentation Analyst — reads README and architecture docs to extract
project constraints and context relevant to the proposed change.
Uses AI to understand documentation.
"""
from __future__ import annotations
import os
from typing import List
from agents.llm_client import complete
from analysis.scanner import ScanResult


_SYSTEM_PROMPT = """\
You are a technical documentation analyst. Read the provided project documentation
and extract insights relevant to a proposed code change.

Focus on:
- Stated architectural invariants or constraints
- API contracts or behavioral guarantees
- Security policies
- Business rules described in the docs
- Any warnings about the affected components

Return a JSON array of concise insight strings. Each insight should be one sentence.
Return ONLY the JSON array, no other text.
Example: ["Orders can only be modified by their owner or an admin.", "Status transitions must follow the defined lifecycle."]
"""


def analyze_documentation(
    change_description: str,
    scan_result: ScanResult,
) -> List[str]:
    """Extract documentation insights relevant to the change."""

    doc_texts = []

    # Read explicitly discovered doc files (README, docs/)
    for doc_path in scan_result.doc_files:
        abs_path = os.path.join(scan_result.project_root, doc_path)
        try:
            with open(abs_path, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
            doc_texts.append(f"### {doc_path}\n{content}")
        except OSError:
            pass

    # Also check source files that look like docs
    for scanned in scan_result.files:
        lower = scanned.path.lower()
        if 'readme' in lower or 'architecture' in lower:
            if not any(doc_path == scanned.path for doc_path in scan_result.doc_files):
                doc_texts.append(f"### {scanned.path}\n{scanned.content}")

    if not doc_texts:
        return ["No documentation files found in project."]

    combined = '\n\n'.join(doc_texts)[:4000]
    user_prompt = f"""## Proposed Change
{change_description}

## Project Documentation
{combined}

Extract insights from these docs that are relevant to this change.
"""
    try:
        raw = complete(_SYSTEM_PROMPT, user_prompt, max_tokens=800)
        from agents.json_utils import extract_json
        insights = extract_json(raw)
        return [str(i) for i in insights[:10]]
    except Exception as e:
        return [f"Documentation analysis unavailable: {str(e)[:100]}"]
