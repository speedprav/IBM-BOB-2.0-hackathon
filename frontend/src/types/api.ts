// API types mirroring backend models

export type RiskSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type RiskCategory =
  | 'regression'
  | 'api_contract'
  | 'security'
  | 'data'
  | 'performance'
  | 'configuration'
  | 'maintainability';
export type NodeType = 'file' | 'class' | 'function' | 'method' | 'module';
export type EdgeType = 'calls' | 'imports' | 'inherits' | 'references';
export type AnalysisStatus = 'pending' | 'running' | 'complete' | 'failed';

export interface Project {
  id: string;
  name: string;
  description: string;
  path: string;
  language: string;
  files: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType;
  file_path: string;
  is_changed: boolean;
  is_directly_impacted: boolean;
  is_indirectly_impacted: boolean;
  symbol?: string;
  metadata: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: EdgeType;
  label?: string;
}

export interface DependencyGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  changed_node_ids: string[];
  direct_impact_ids: string[];
  indirect_impact_ids: string[];
}

export interface RiskFinding {
  id: string;
  severity: RiskSeverity;
  category: RiskCategory;
  title: string;
  description: string;
  why_it_matters: string;
  affected_location: string;
  evidence: string;
  suggested_mitigation: string;
}

export interface TestImpact {
  test_file: string;
  test_name: string;
  relevance: string;
  will_break: boolean;
  reason: string;
}

export interface GeneratedTest {
  file_name: string;
  content: string;
  rationale: string;
  covers_risk_ids: string[];
}

export interface VerificationResult {
  command: string;
  status: string;
  duration_ms: number;
  output: string;
  passed: boolean;
}

export interface ProgressStep {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'complete' | 'failed';
  detail?: string;
  duration_ms?: number;
}

export interface ProductivityMetrics {
  files_analyzed: number;
  symbols_analyzed: number;
  files_impacted: number;
  symbols_impacted: number;
  tests_affected: number;
  tests_generated: number;
  risks_detected: number;
  workflow_steps_automated: number;
  baseline_estimate_minutes: number;
  measured_duration_seconds: number;
}

export interface AnalysisResult {
  analysis_id: string;
  project_path: string;
  change_description: string;
  diff_text?: string;
  dependency_graph: DependencyGraph;
  risk_findings: RiskFinding[];
  affected_tests: TestImpact[];
  coverage_gaps: string[];
  generated_test?: GeneratedTest;
  verification?: VerificationResult;
  summary: string;
  documentation_insights: string[];
  progress_steps: ProgressStep[];
  metrics: ProductivityMetrics;
  analysis_source?: 'live_gemini' | 'demo' | string;
  ai_model?: string;
}

export interface AnalysisStatusResponse {
  analysis_id: string;
  status: AnalysisStatus;
  progress_steps: ProgressStep[];
  result?: AnalysisResult;
  error?: string;
}
