"""
Risk Analyst — evaluates the proposed change for regression, security,
API contract, and other risk factors. Uses AI to reason about hidden risks.
"""
from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field
from typing import List
from agents.llm_client import complete
from agents.dependency_analyst import DependencyAnalysisResult


@dataclass
class RiskFinding:
    id: str
    severity: str      # critical | high | medium | low | info
    category: str      # regression | api_contract | security | data | performance | ...
    title: str
    description: str
    why_it_matters: str
    affected_location: str
    evidence: str
    suggested_mitigation: str


_SYSTEM_PROMPT = """\
You are a senior software engineer performing a risk analysis on a proposed code change.
You are given:
- A description of the change
- The diff
- The blast radius (files and symbols affected)
- Relevant source code context

Your job is to identify concrete risks, NOT to summarize the change.

Respond with a JSON array of risk findings. Each finding must have exactly these fields:
{
  "severity": one of exactly: critical, high, medium, low, info  (single word only),
  "category": one of exactly: regression, api_contract, security, data, performance, configuration, maintainability  (single word/value only — never combine with | or /),
  "title": "short title unique to this change",
  "description": "what the risk is",
  "why_it_matters": "business/technical consequence if not addressed",
  "affected_location": "file:function or module name",
  "evidence": "quote or paraphrase a SPECIFIC line/behavior from the provided diff or source",
  "suggested_mitigation": "concrete action to address it"
}

Rules:
- Base EVERY finding on the provided diff/code/docs — no generic template risks.
- Prefer 3–6 specific findings over vague ones.
- If the change description differs from the diff, analyze the DIFF as ground truth and note mismatches.
- Do not reuse stock titles like "Payment and Inventory Inconsistencies" unless the code truly shows that.
Focus on NON-OBVIOUS consequences. Do not list the change itself as a risk.
Return ONLY the JSON array, no other text.
"""


def analyze_risks(
    change_description: str,
    diff_text: str,
    dep_result: DependencyAnalysisResult,
    relevant_code: str,
    doc_context: str,
) -> List[RiskFinding]:
    """Call the LLM to reason about risks in this change."""

    user_prompt = f"""## Proposed Change
{change_description}

## Diff
```
{diff_text[:3000] if diff_text else 'No diff provided'}
```

## Blast Radius
{dep_result.blast_radius_summary}
Changed files: {dep_result.changed_files}
Directly impacted symbols: {dep_result.direct_impact_node_ids[:20]}

## Relevant Source Code
```python
{relevant_code[:3000]}
```

## Documentation Context
{doc_context[:1000] if doc_context else 'No documentation available'}

Identify all significant risks introduced by this change.
"""

    raw = complete(_SYSTEM_PROMPT, user_prompt, max_tokens=8192)
    from agents.json_utils import extract_json
    findings_data = extract_json(raw)
    if isinstance(findings_data, dict):
        findings_data = [findings_data]
    if not isinstance(findings_data, list):
        raise ValueError(f"Risk analyst expected a JSON array, got {type(findings_data).__name__}")

    findings = []
    for fd in findings_data:
        if not isinstance(fd, dict):
            continue
        findings.append(RiskFinding(
            id=str(uuid.uuid4()),
            severity=fd.get('severity', 'medium'),
            category=fd.get('category', 'regression'),
            title=fd.get('title', 'Unknown risk'),
            description=fd.get('description', ''),
            why_it_matters=fd.get('why_it_matters', ''),
            affected_location=fd.get('affected_location', ''),
            evidence=fd.get('evidence', ''),
            suggested_mitigation=fd.get('suggested_mitigation', ''),
        ))
    return findings

