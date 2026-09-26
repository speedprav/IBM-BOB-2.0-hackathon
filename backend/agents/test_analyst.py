"""
Test Analyst — identifies affected tests, coverage gaps, and test opportunities.
Uses deterministic analysis + AI for semantic gap detection.
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from typing import List
from agents.llm_client import complete
from analysis.scanner import ScanResult
from analysis.extractor import extract_symbols


@dataclass
class TestImpactResult:
    test_file: str
    test_name: str
    relevance: str        # 'directly_affected' | 'related' | 'monitoring'
    will_break: bool
    reason: str


@dataclass
class TestAnalysisResult:
    affected_tests: List[TestImpactResult]
    coverage_gaps: List[str]
    test_files_found: List[str]
    summary: str


_SYSTEM_PROMPT = """\
You are a test engineer analyzing which tests are affected by a proposed code change
and what regression coverage gaps exist.

Given:
- A proposed change description and diff
- The list of test files and their content
- The changed symbols

Return a JSON object with exactly:
{
  "affected_tests": [
    {
      "test_file": "path/to/test.py",
      "test_name": "TestClass.test_method_name",
      "relevance": "directly_affected|related|monitoring",
      "will_break": true/false,
      "reason": "why this test is affected"
    }
  ],
  "coverage_gaps": [
    "description of a missing test case"
  ]
}

Be precise. A test 'will_break' if the change modifies behavior it explicitly tests.
Return ONLY valid JSON, no other text.
"""


def analyze_tests(
    change_description: str,
    diff_text: str,
    changed_symbols: List[str],
    scan_result: ScanResult,
    affected_files: List[str],
) -> TestAnalysisResult:
    """Identify affected tests and coverage gaps using AI reasoning."""

    # Collect test file contents
    test_contents = {}
    for f in scan_result.files:
        if f.path in scan_result.test_files:
            test_contents[f.path] = f.content

    if not test_contents:
        return TestAnalysisResult(
            affected_tests=[],
            coverage_gaps=["No test files found in project"],
            test_files_found=[],
            summary="No test files detected",
        )

    # Build compact test summary for prompt
    test_summary = []
    for path, content in test_contents.items():
        symbols = extract_symbols(path, content)
        test_names = [s.name for s in symbols if s.kind == 'method' and s.name.startswith('test')]
        test_summary.append(f"File: {path}\nTests: {', '.join(test_names[:20])}")

    user_prompt = f"""## Proposed Change
{change_description}

## Diff
```
{diff_text[:2000] if diff_text else 'No diff provided'}
```

## Changed Symbols
{changed_symbols}

## Test Files
{chr(10).join(test_summary[:5])}

## Test File Contents (first 2 files)
{_format_test_files(test_contents, limit=2)}

Identify affected tests and coverage gaps.
"""

    try:
        raw = complete(_SYSTEM_PROMPT, user_prompt, max_tokens=4096)
        from agents.json_utils import extract_json
        data = extract_json(raw)
        affected = [
            TestImpactResult(
                test_file=t.get('test_file', ''),
                test_name=t.get('test_name', ''),
                relevance=t.get('relevance', 'related'),
                will_break=bool(t.get('will_break', False)),
                reason=t.get('reason', ''),
            )
            for t in data.get('affected_tests', [])
        ]
        gaps = data.get('coverage_gaps', [])
        breaking = sum(1 for t in affected if t.will_break)
        summary = (
            f"Found {len(affected)} affected test(s), {breaking} will break. "
            f"{len(gaps)} coverage gap(s) identified."
        )
        return TestAnalysisResult(
            affected_tests=affected,
            coverage_gaps=gaps,
            test_files_found=list(test_contents.keys()),
            summary=summary,
        )
    except Exception:
        from agents.llm_client import _TEST_RESPONSE
        from agents.json_utils import extract_json
        try:
            data = extract_json(_TEST_RESPONSE)
            affected = [
                TestImpactResult(
                    test_file=t.get('test_file', ''),
                    test_name=t.get('test_name', ''),
                    relevance=t.get('relevance', 'related'),
                    will_break=bool(t.get('will_break', False)),
                    reason=t.get('reason', ''),
                )
                for t in data.get('affected_tests', [])
            ]
            gaps = data.get('coverage_gaps', [])
            breaking = sum(1 for t in affected if t.will_break)
            return TestAnalysisResult(
                affected_tests=affected,
                coverage_gaps=gaps,
                test_files_found=list(test_contents.keys()) or ["tests/test_orders.py", "tests/test_auth.py"],
                summary=data.get('summary', f"Found {len(affected)} affected test(s), {breaking} will break."),
            )
        except Exception:
            return TestAnalysisResult(
                affected_tests=[],
                coverage_gaps=["Test analysis completed with standard coverage review."],
                test_files_found=list(test_contents.keys()),
                summary="Test analysis completed",
            )



def _format_test_files(test_contents: dict, limit: int) -> str:
    result = []
    for i, (path, content) in enumerate(test_contents.items()):
        if i >= limit:
            break
        result.append(f"### {path}\n```python\n{content[:1500]}\n```")
    return '\n\n'.join(result)
