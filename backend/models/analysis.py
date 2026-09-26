"""
DevTwin backend domain models.
"""
from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────────────

class RiskSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RiskCategory(str, Enum):
    REGRESSION = "regression"
    API_CONTRACT = "api_contract"
    SECURITY = "security"
    DATA = "data"
    PERFORMANCE = "performance"
    CONFIGURATION = "configuration"
    MAINTAINABILITY = "maintainability"


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class NodeType(str, Enum):
    FILE = "file"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    MODULE = "module"


class EdgeType(str, Enum):
    CALLS = "calls"
    IMPORTS = "imports"
    INHERITS = "inherits"
    REFERENCES = "references"


# ─── Analysis Request / Response ──────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    project_path: str = Field(..., description="Absolute path to the project root")
    change_description: str = Field(..., description="Natural-language description of the change")
    diff_text: Optional[str] = Field(None, description="Unified diff of the proposed change")
    changed_files: Optional[List[str]] = Field(None, description="Explicit list of changed files")


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: AnalysisStatus
    progress_steps: List[ProgressStep] = []
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None


# ─── Graph ────────────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    type: NodeType
    file_path: str
    is_changed: bool = False
    is_directly_impacted: bool = False
    is_indirectly_impacted: bool = False
    symbol: Optional[str] = None
    metadata: Dict[str, Any] = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    type: EdgeType
    label: Optional[str] = None


class DependencyGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    changed_node_ids: List[str] = []
    direct_impact_ids: List[str] = []
    indirect_impact_ids: List[str] = []


# ─── Risk ─────────────────────────────────────────────────────────────────────

class RiskFinding(BaseModel):
    id: str
    severity: RiskSeverity
    category: RiskCategory
    title: str
    description: str
    why_it_matters: str
    affected_location: str
    evidence: str
    suggested_mitigation: str


# ─── Test Impact ──────────────────────────────────────────────────────────────

class TestImpact(BaseModel):
    test_file: str
    test_name: str
    relevance: str
    will_break: bool
    reason: str


class GeneratedTest(BaseModel):
    file_name: str
    content: str
    rationale: str
    covers_risk_ids: List[str] = []


class VerificationResult(BaseModel):
    command: str
    status: str       # "passed" | "failed" | "error"
    duration_ms: int
    output: str
    passed: bool


# ─── Progress ─────────────────────────────────────────────────────────────────

class ProgressStep(BaseModel):
    id: str
    name: str
    status: str       # "pending" | "running" | "complete" | "failed"
    detail: Optional[str] = None
    duration_ms: Optional[int] = None


# ─── Metrics ──────────────────────────────────────────────────────────────────

class ProductivityMetrics(BaseModel):
    files_analyzed: int
    symbols_analyzed: int
    files_impacted: int
    symbols_impacted: int
    tests_affected: int
    tests_generated: int
    risks_detected: int
    workflow_steps_automated: int
    baseline_estimate_minutes: int
    measured_duration_seconds: float


# ─── Final Result ─────────────────────────────────────────────────────────────

class AnalysisResult(BaseModel):
    analysis_id: str
    project_path: str
    change_description: str
    diff_text: Optional[str]

    # Core outputs
    dependency_graph: DependencyGraph
    risk_findings: List[RiskFinding]
    affected_tests: List[TestImpact]
    coverage_gaps: List[str]
    generated_test: Optional[GeneratedTest]
    verification: Optional[VerificationResult]

    # Report
    summary: str
    documentation_insights: List[str]
    progress_steps: List[ProgressStep]
    metrics: ProductivityMetrics

    # Provenance — so the UI can prove results are live vs demo
    analysis_source: str = "unknown"  # "live_gemini" | "demo"
    ai_model: Optional[str] = None
