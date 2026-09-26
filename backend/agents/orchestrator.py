"""
Orchestrator — coordinates all analysis agents and produces the final report.
Runs independent analysis tasks (risk, test, documentation) in parallel using asyncio.
"""
from __future__ import annotations
import asyncio
import os
import time
import uuid
from functools import partial
from typing import Dict, List, Optional

from models.analysis import (
    AnalysisRequest, AnalysisResult, AnalysisStatusResponse,
    DependencyGraph, GraphNode, GraphEdge, NodeType, EdgeType,
    RiskFinding, TestImpact, GeneratedTest, VerificationResult,
    ProgressStep, ProductivityMetrics,
)
from analysis.scanner import scan_repository, get_file_content
from analysis.graph import build_dependency_graph, compute_impact
from analysis.diff_parser import parse_diff, extract_changed_symbols_from_diff
from agents.dependency_analyst import analyze_dependencies
from agents.risk_analyst import analyze_risks
from agents.test_analyst import analyze_tests
from agents.doc_analyst import analyze_documentation
from agents.test_generator import generate_tests
from agents.verifier import verify


def _resolve_project_root(project_path: str) -> str:
    """Resolve project path relative to the devtwin project root."""
    if os.path.isabs(project_path) and os.path.isdir(project_path):
        return project_path
    # Try relative to this file's location (devtwin/backend/agents/ → devtwin/)
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    candidate = os.path.normpath(os.path.join(base, project_path))
    if os.path.isdir(candidate):
        return candidate
    return project_path


class Orchestrator:
    def __init__(self, analysis_id: str, job: AnalysisStatusResponse) -> None:
        self.analysis_id = analysis_id
        self.job = job
        self._start_time = time.perf_counter()

    def _update_step(self, step_id: str, name: str, status: str, detail: str = '') -> None:
        steps = self.job.progress_steps
        for s in steps:
            if s.id == step_id:
                s.status = status
                if detail:
                    s.detail = detail
                if status in ('complete', 'failed'):
                    s.duration_ms = int((time.perf_counter() - self._start_time) * 1000)
                return
        steps.append(ProgressStep(id=step_id, name=name, status=status, detail=detail))

    async def run(self, request: AnalysisRequest) -> AnalysisResult:
        t0 = time.perf_counter()

        # ── Step 1: Scan repository ──────────────────────────────────────────
        self._update_step('scan', 'Repository Scan', 'running')
        project_root = _resolve_project_root(request.project_path)
        scan_result = await asyncio.get_event_loop().run_in_executor(
            None, scan_repository, project_root
        )
        self._update_step('scan', 'Repository Scan', 'complete',
                          f"{scan_result.file_count} files, {scan_result.total_lines} lines")

        # ── Step 2: Build dependency graph ───────────────────────────────────
        self._update_step('graph', 'Dependency Graph', 'running')
        graph, file_symbols = await asyncio.get_event_loop().run_in_executor(
            None, build_dependency_graph, scan_result
        )
        self._update_step('graph', 'Dependency Graph', 'complete',
                          f"{len(graph.nodes)} nodes, {len(graph.edges)} edges")

        # ── Step 3: Parse diff ───────────────────────────────────────────────
        self._update_step('diff', 'Change Analysis', 'running')
        parsed_diff = parse_diff(request.diff_text or '')
        changed_files = (
            request.changed_files
            or parsed_diff.changed_files
            or []
        )
        changed_symbols = extract_changed_symbols_from_diff(parsed_diff, file_symbols)
        self._update_step('diff', 'Change Analysis', 'complete',
                          f"{len(changed_files)} file(s), {len(changed_symbols)} symbol(s)")

        # ── Step 4: Dependency analysis (deterministic) ──────────────────────
        self._update_step('deps', 'Blast Radius Computation', 'running')
        dep_result = await asyncio.get_event_loop().run_in_executor(
            None, analyze_dependencies, graph, changed_files, changed_symbols
        )
        self._update_step('deps', 'Blast Radius Computation', 'complete',
                          dep_result.blast_radius_summary)

        # ── Step 5: Parallel AI analysis (risk + tests + docs) ──────────────
        self._update_step('risk', 'Risk Analysis', 'running')
        self._update_step('tests', 'Test Impact Analysis', 'running')
        self._update_step('docs', 'Documentation Analysis', 'running')

        relevant_code = self._gather_relevant_code(project_root, changed_files, scan_result)
        doc_context = self._gather_doc_context(scan_result)
        existing_test_sample = self._gather_test_sample(scan_result)

        # Run three independent analyses in parallel
        risk_task = asyncio.get_event_loop().run_in_executor(
            None,
            partial(
                analyze_risks,
                request.change_description,
                request.diff_text or '',
                dep_result,
                relevant_code,
                doc_context,
            )
        )
        test_task = asyncio.get_event_loop().run_in_executor(
            None,
            partial(
                analyze_tests,
                request.change_description,
                request.diff_text or '',
                changed_symbols,
                scan_result,
                dep_result.affected_files,
            )
        )
        doc_task = asyncio.get_event_loop().run_in_executor(
            None,
            partial(
                analyze_documentation,
                request.change_description,
                scan_result,
            )
        )

        risk_findings_raw, test_analysis, doc_insights = await asyncio.gather(
            risk_task, test_task, doc_task
        )

        self._update_step('risk', 'Risk Analysis', 'complete',
                          f"{len(risk_findings_raw)} finding(s)")
        self._update_step('tests', 'Test Impact Analysis', 'complete',
                          test_analysis.summary)
        self._update_step('docs', 'Documentation Analysis', 'complete',
                          f"{len(doc_insights)} insight(s)")

        # ── Step 6: Generate regression tests ───────────────────────────────
        self._update_step('gen', 'Test Generation', 'running')
        changed_file_content = ''
        if changed_files:
            changed_file_content = get_file_content(project_root, changed_files[0]) or ''
        generated_raw = await asyncio.get_event_loop().run_in_executor(
            None,
            partial(
                generate_tests,
                request.change_description,
                request.diff_text or '',
                risk_findings_raw,
                test_analysis,
                existing_test_sample,
                changed_file_content,
            )
        )
        self._update_step('gen', 'Test Generation', 'complete',
                          f"Generated {generated_raw.file_name}")

        # ── Step 7: Verification ─────────────────────────────────────────────
        self._update_step('verify', 'Verification', 'running')
        verification_raw = await asyncio.get_event_loop().run_in_executor(
            None, partial(verify, project_root)
        )
        status_label = 'passed' if verification_raw.passed else 'failed'
        self._update_step('verify', 'Verification', 'complete' if verification_raw.passed else 'failed',
                          f"Tests {status_label} in {verification_raw.duration_ms}ms")

        # ── Build final result ───────────────────────────────────────────────
        duration = time.perf_counter() - t0
        result = self._build_result(
            request=request,
            graph=graph,
            dep_result=dep_result,
            risk_findings_raw=risk_findings_raw,
            test_analysis=test_analysis,
            doc_insights=doc_insights,
            generated_raw=generated_raw,
            verification_raw=verification_raw,
            scan_result=scan_result,
            duration_seconds=duration,
        )
        return result

    def _build_result(self, request, graph, dep_result, risk_findings_raw,
                      test_analysis, doc_insights, generated_raw,
                      verification_raw, scan_result, duration_seconds) -> AnalysisResult:

        # Convert graph to API model
        api_graph = self._convert_graph(graph, dep_result)

        # Convert risk findings — sanitize AI-returned enum values before Pydantic validation
        risk_findings = [
            RiskFinding(
                id=r.id,
                severity=_coerce_severity(r.severity),
                category=_coerce_category(r.category),
                title=r.title,
                description=r.description,
                why_it_matters=r.why_it_matters,
                affected_location=r.affected_location,
                evidence=r.evidence,
                suggested_mitigation=r.suggested_mitigation,
            )
            for r in risk_findings_raw
        ]

        # Convert test impacts
        affected_tests = [
            TestImpact(
                test_file=t.test_file,
                test_name=t.test_name,
                relevance=t.relevance,
                will_break=t.will_break,
                reason=t.reason,
            )
            for t in test_analysis.affected_tests
        ]

        # Convert generated test
        generated_test = GeneratedTest(
            file_name=generated_raw.file_name,
            content=generated_raw.content,
            rationale=generated_raw.rationale,
            covers_risk_ids=generated_raw.covers_risk_ids,
        )

        # Convert verification
        verification = VerificationResult(
            command=verification_raw.command,
            status=verification_raw.status,
            duration_ms=verification_raw.duration_ms,
            output=verification_raw.output,
            passed=verification_raw.passed,
        )

        # Summary
        breaking = sum(1 for t in test_analysis.affected_tests if t.will_break)
        critical = sum(1 for r in risk_findings_raw if r.severity == 'critical')
        high = sum(1 for r in risk_findings_raw if r.severity == 'high')
        summary = (
            f"Analysis complete. "
            f"Found {len(risk_findings_raw)} risk(s)"
            f"{f' including {critical} critical' if critical else ''}"
            f"{f' and {high} high severity' if high else ''}. "
            f"{breaking} test(s) will break. "
            f"Blast radius: {len(dep_result.direct_impact_node_ids)} direct + "
            f"{len(dep_result.indirect_impact_node_ids)} indirect impact(s). "
            f"1 regression test generated."
        )

        metrics = ProductivityMetrics(
            files_analyzed=scan_result.file_count,
            symbols_analyzed=len(graph.nodes),
            files_impacted=len(dep_result.affected_files),
            symbols_impacted=len(dep_result.affected_symbols),
            tests_affected=len(affected_tests),
            tests_generated=1,
            risks_detected=len(risk_findings),
            workflow_steps_automated=7,
            baseline_estimate_minutes=45,
            measured_duration_seconds=round(duration_seconds, 1),
        )

        return AnalysisResult(
            analysis_id=self.analysis_id,
            project_path=request.project_path,
            change_description=request.change_description,
            diff_text=request.diff_text,
            dependency_graph=api_graph,
            risk_findings=risk_findings,
            affected_tests=affected_tests,
            coverage_gaps=test_analysis.coverage_gaps,
            generated_test=generated_test,
            verification=verification,
            summary=summary,
            documentation_insights=doc_insights,
            progress_steps=self.job.progress_steps,
            metrics=metrics,
        )

    def _convert_graph(self, graph, dep_result) -> DependencyGraph:
        """Convert internal graph to API model."""
        from models.analysis import DependencyGraph as ApiGraph, GraphNode as ApiNode, GraphEdge as ApiEdge

        nodes = []
        for nid, node in graph.nodes.items():
            is_changed = nid in dep_result.changed_node_ids
            is_direct = nid in dep_result.direct_impact_node_ids
            is_indirect = nid in dep_result.indirect_impact_node_ids
            nodes.append(ApiNode(
                id=nid,
                label=node.label,
                type=_map_node_type(node.node_type),
                file_path=node.file_path,
                is_changed=is_changed,
                is_directly_impacted=is_direct,
                is_indirectly_impacted=is_indirect,
                symbol=node.symbol,
                metadata=node.metadata,
            ))

        edges = []
        for edge in graph.edges:
            edges.append(ApiEdge(
                source=edge.source,
                target=edge.target,
                type=_map_edge_type(edge.edge_type),
                label=edge.label,
            ))

        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            changed_node_ids=dep_result.changed_node_ids,
            direct_impact_ids=dep_result.direct_impact_node_ids,
            indirect_impact_ids=dep_result.indirect_impact_node_ids,
        )

    def _gather_relevant_code(self, project_root: str, changed_files: List[str], scan_result) -> str:
        """Gather content of changed files for LLM context."""
        parts = []
        for cf in changed_files[:3]:
            content = get_file_content(project_root, cf)
            if content:
                parts.append(f"### {cf}\n```python\n{content[:2000]}\n```")
        return '\n\n'.join(parts)

    def _gather_doc_context(self, scan_result) -> str:
        """Gather first doc file content for context."""
        for f in scan_result.files:
            if 'readme' in f.path.lower() or 'architecture' in f.path.lower():
                return f.content[:2000]
        return ''

    def _gather_test_sample(self, scan_result) -> str:
        """Return content of the first test file for style reference."""
        for f in scan_result.files:
            if f.path in scan_result.test_files:
                return f.content[:2000]
        return ''


def _map_node_type(t: str) -> NodeType:
    mapping = {'file': NodeType.FILE, 'class': NodeType.CLASS,
                'function': NodeType.FUNCTION, 'method': NodeType.METHOD}
    return mapping.get(t, NodeType.FILE)


def _map_edge_type(t: str) -> EdgeType:
    mapping = {'calls': EdgeType.CALLS, 'imports': EdgeType.IMPORTS,
                'contains': EdgeType.REFERENCES, 'inherits': EdgeType.INHERITS}
    return mapping.get(t, EdgeType.REFERENCES)


# ── Enum coercers ─────────────────────────────────────────────────────────────
# Gemini sometimes returns multi-word or pipe-separated values like "race|data".
# These helpers map any such string to the nearest valid enum value.

_VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}
_VALID_CATEGORIES = {
    "regression", "api_contract", "security", "data",
    "performance", "configuration", "maintainability",
}

def _coerce_severity(value: str) -> str:
    v = str(value).lower().strip()
    if v in _VALID_SEVERITIES:
        return v
    # Check if any valid severity appears as a substring
    for s in ("critical", "high", "medium", "low", "info"):
        if s in v:
            return s
    return "medium"


def _coerce_category(value: str) -> str:
    v = str(value).lower().strip()
    if v in _VALID_CATEGORIES:
        return v
    # Handle pipe-separated values like "race|data" → pick first recognised token
    for token in v.replace("|", " ").replace("/", " ").replace(",", " ").split():
        if token in _VALID_CATEGORIES:
            return token
    # Fuzzy: check substrings
    for cat in ("regression", "api_contract", "security", "data",
                "performance", "configuration", "maintainability"):
        if cat in v or cat.replace("_", "") in v.replace("_", ""):
            return cat
    return "regression"
