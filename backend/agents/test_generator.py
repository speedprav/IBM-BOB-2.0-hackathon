"""
Test Generator — writes regression tests from live risk/gap analysis.
No silent canned test file when live mode is on.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from agents.llm_client import complete
from agents.risk_analyst import RiskFinding
from agents.test_analyst import TestAnalysisResult


@dataclass
class GeneratedTest:
    file_name: str
    content: str
    rationale: str
    covers_risk_ids: List[str]


_SYSTEM_PROMPT = """\
You are a senior Python test engineer. Generate a pytest regression test file
that covers the specific risks and gaps identified in a code change analysis.

Requirements:
- Use pytest conventions (class-based or function-based tests)
- Mirror the testing style of the existing tests shown
- Test the SPECIFIC behaviors that are now risky due to the change
- Include clear docstrings explaining what each test covers
- Use realistic test data (no magic numbers, meaningful names)
- Tests should be immediately runnable (correct imports, self-contained fixtures)
- The test file should be named test_regression_<short_description>.py

Return ONLY the Python test file content. No explanation, no markdown fences.
Do not emit a generic placeholder — write tests that match THIS change and THESE risks.
"""


def generate_tests(
    change_description: str,
    diff_text: str,
    risk_findings: List[RiskFinding],
    test_analysis: TestAnalysisResult,
    existing_test_sample: str,
    changed_file_content: str,
) -> GeneratedTest:
    """Generate regression tests covering the identified risks."""

    risk_summary = '\n'.join([
        f"- [{r.severity.upper()}] {r.title}: {r.description}"
        for r in risk_findings
    ])
    gap_summary = '\n'.join([f"- {g}" for g in test_analysis.coverage_gaps])
    risk_ids = [r.id for r in risk_findings]

    user_prompt = f"""## Proposed Change
{change_description}

## Diff
```
{diff_text[:2000] if diff_text else 'No diff'}
```

## Risk Findings
{risk_summary or '(none)'}

## Coverage Gaps
{gap_summary or '(none)'}

## Existing Test Style (reference)
```python
{existing_test_sample[:2000]}
```

## Changed Code
```python
{changed_file_content[:2000]}
```

Generate a regression test file that tests the risky behaviors exposed by this change.
The test file must be self-contained and immediately runnable.
"""

    content = complete(_SYSTEM_PROMPT, user_prompt, max_tokens=4096, json_mode=False)
    import re
    fence_match = re.search(r'```(?:python)?\s*\n([\s\S]*?)```', content)
    if fence_match:
        content = fence_match.group(1).strip()
    elif content.startswith('```'):
        lines = content.split('\n')
        content = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])

    stripped = content.strip()
    if stripped.startswith('{') and ('"content"' in stripped or '"code"' in stripped):
        try:
            from agents.json_utils import extract_json
            obj = extract_json(stripped)
            if isinstance(obj, dict):
                content = obj.get('content') or obj.get('code') or content
        except Exception:
            pass

    slug = change_description.lower().replace(' ', '_')[:40]
    slug = ''.join(c if c.isalnum() or c == '_' else '' for c in slug) or 'change'
    file_name = f"test_regression_{slug}.py"

    return GeneratedTest(
        file_name=file_name,
        content=content,
        rationale=(
            f"Live-generated regression suite covering {len(risk_findings)} risk(s) "
            f"and {len(test_analysis.coverage_gaps)} gap(s) for: {change_description}"
        ),
        covers_risk_ids=risk_ids,
    )
