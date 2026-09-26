"""
Documentation Analyst — extracts project constraints relevant to the change.
Live Gemini only when an API key is set; no silent canned fallbacks.
"""
from __future__ import annotations
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

Rules:
- Quote or paraphrase ONLY what appears in the provided docs.
- Tie each insight to the proposed change when possible.
- Do not invent policies that are not in the documentation.
"""


def analyze_documentation(
    change_description: str,
    scan_result: ScanResult,
) -> List[str]:
    """Extract documentation insights relevant to the change."""

    doc_texts = []

    from analysis.scanner import get_file_content
    for doc_path in scan_result.doc_files:
        content = get_file_content(scan_result.project_root, doc_path)
        if content:
            doc_texts.append(f"### {doc_path}\n{content}")

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
    raw = complete(_SYSTEM_PROMPT, user_prompt, max_tokens=2048)
    from agents.json_utils import extract_json
    insights = extract_json(raw)
    if insights and isinstance(insights, list):
        return [str(i) for i in insights[:10]]
    if isinstance(insights, dict) and "insights" in insights:
        return [str(i) for i in insights["insights"][:10]]
    raise ValueError("Documentation analyst expected a JSON array of insight strings")
