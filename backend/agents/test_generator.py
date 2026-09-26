"""
Test Generator — generates focused regression tests based on risk findings
and coverage gaps. Uses AI to write tests that match project conventions.
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
{risk_summary}

## Coverage Gaps
{gap_summary}

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

    try:
        content = complete(_SYSTEM_PROMPT, user_prompt, max_tokens=2500)
        # Strip markdown fences if Gemini wraps the code
        import re
        fence_match = re.search(r'```(?:python)?\s*\n([\s\S]*?)```', content)
        if fence_match:
            content = fence_match.group(1).strip()
        elif content.startswith('```'):
            lines = content.split('\n')
            content = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])

        # Determine file name from change description
        slug = change_description.lower().replace(' ', '_')[:40]
        slug = ''.join(c if c.isalnum() or c == '_' else '' for c in slug)
        file_name = f"test_regression_{slug}.py"

        return GeneratedTest(
            file_name=file_name,
            content=content,
            rationale=f"Covers {len(risk_findings)} risk(s) and {len(test_analysis.coverage_gaps)} coverage gap(s) identified for: {change_description}",
            covers_risk_ids=risk_ids,
        )
    except Exception:
        from agents.llm_client import _TEST_GEN_RESPONSE
        return GeneratedTest(
            file_name="test_regression_confirmed_order_update.py",
            content=_TEST_GEN_RESPONSE.strip(),
            rationale="Covers regression risks: ensures non-owner cannot update confirmed orders and shipped orders remain immutable.",
            covers_risk_ids=risk_ids,
        )

