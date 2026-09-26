import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../api';
import { AppState } from '../App';
import { AnalysisResult, AnalysisStatusResponse, ProgressStep } from '../types/api';
import ProgressPipeline from '../components/ProgressPipeline';
import SummaryCards from '../components/SummaryCards';
import BlastRadiusGraph from '../components/BlastRadiusGraph';
import RiskFindings from '../components/RiskFindings';
import TestImpactPanel from '../components/TestImpactPanel';
import GeneratedTestPanel from '../components/GeneratedTestPanel';
import VerificationPanel from '../components/VerificationPanel';
import FinalReport from '../components/FinalReport';
import MetricsPanel from '../components/MetricsPanel';

interface Props {
  appState: AppState;
  onReset: () => void;
}

type ActiveTab = 'overview' | 'risks' | 'tests' | 'generated' | 'report';

export default function AnalysisPage({ appState, onReset }: Props) {
  const [status, setStatus] = useState<AnalysisStatusResponse | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState<ActiveTab>('overview');

  const startAnalysis = useCallback(async () => {
    try {
      const { analysis_id } = await api.startAnalysis({
        project_path: appState.projectPath,
        change_description: appState.changeDescription,
        diff_text: appState.diffText || undefined,
        changed_files: appState.changedFiles.length > 0 ? appState.changedFiles : undefined,
      });

      const finalResult = await api.pollUntilComplete(
        analysis_id,
        (s) => setStatus(s),
        1500
      );
      setResult(finalResult);
      setStatus(prev => prev ? { ...prev, status: 'complete', result: finalResult } : null);
    } catch (err: any) {
      setError(err?.message || 'Analysis failed');
    }
  }, [appState]);

  useEffect(() => {
    startAnalysis();
  }, [startAnalysis]);

  const isRunning = status?.status === 'running' || status?.status === 'pending';
  const isComplete = status?.status === 'complete';
  const isFailed = status?.status === 'failed';

  const steps: ProgressStep[] = status?.progress_steps || [];

  const tabs: { id: ActiveTab; label: string; badge?: number }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'risks', label: 'Risk Findings', badge: result?.risk_findings.length },
    { id: 'tests', label: 'Test Impact', badge: result?.affected_tests.length },
    { id: 'generated', label: 'Generated Test' },
    { id: 'report', label: 'Final Report' },
  ];

  return (
    <div className="analysis-page">
      {/* Top bar */}
      <header className="analysis-header">
        <div className="container">
          <div className="flex items-center justify-between" style={{ padding: '14px 0' }}>
            <div className="flex items-center gap-12">
              <button className="btn btn-secondary" onClick={onReset} style={{ padding: '6px 12px' }}>
                ← New Analysis
              </button>
              <div className="flex items-center gap-8">
                <div className="logo-sm">⬡ DevTwin</div>
                <span className="text-muted">›</span>
                <span style={{ color: 'var(--text)' }}>{appState.projectName}</span>
              </div>
            </div>
            <div className="flex items-center gap-8">
              <div className={`dot dot-${status?.status || 'pending'}`} />
              <span className="text-small text-muted">
                {isRunning ? 'Analyzing…' : isComplete ? 'Analysis complete' : isFailed ? 'Failed' : 'Pending'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Change summary bar */}
      <div className="change-bar">
        <div className="container">
          <div className="flex items-center gap-12" style={{ padding: '10px 0', flexWrap: 'wrap' }}>
            <span className="badge badge-muted">Proposed Change</span>
            <span style={{ color: 'var(--text)' }}>{appState.changeDescription}</span>
            {appState.changedFiles.length > 0 && (
              <div className="flex gap-4">
                {appState.changedFiles.map(f => (
                  <code key={f} className="file-chip-sm">{f}</code>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Progress pipeline */}
      <div className="pipeline-bar">
        <div className="container">
          <ProgressPipeline steps={steps} isRunning={isRunning} />
        </div>
      </div>

      {/* Error state */}
      {(error || isFailed) && (
        <div className="container" style={{ paddingTop: 24 }}>
          <div className="alert alert-danger">
            ⚠ {error || status?.error || 'Analysis failed'}
          </div>
        </div>
      )}

      {/* Loading state */}
      {isRunning && !result && (
        <div className="container" style={{ paddingTop: 40, textAlign: 'center' }}>
          <div className="loading-spinner" />
          <p className="text-muted" style={{ marginTop: 12 }}>
            Running parallel analysis — dependency scan, risk evaluation, test impact, documentation analysis…
          </p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="container results-container">
          {/* Summary cards */}
          <SummaryCards result={result} />

          {/* Tabs */}
          <div className="tabs">
            {tabs.map(t => (
              <button
                key={t.id}
                className={`tab ${activeTab === t.id ? 'active' : ''}`}
                onClick={() => setActiveTab(t.id)}
              >
                {t.label}
                {t.badge !== undefined && t.badge > 0 && (
                  <span className="tab-badge">{t.badge}</span>
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {activeTab === 'overview' && (
            <div className="tab-content">
              <div className="overview-layout">
                <div className="overview-main">
                  <h3 style={{ marginBottom: 16 }}>Blast Radius Graph</h3>
                  <BlastRadiusGraph graph={result.dependency_graph} />
                </div>
                <div className="overview-side">
                  <h3 style={{ marginBottom: 16 }}>Top Risks</h3>
                  <RiskFindings findings={result.risk_findings.slice(0, 3)} compact />
                  {result.documentation_insights.length > 0 && (
                    <div className="doc-insights" style={{ marginTop: 20 }}>
                      <h4 style={{ marginBottom: 10 }}>Documentation Insights</h4>
                      {result.documentation_insights.map((insight, i) => (
                        <div key={i} className="insight-item">
                          <span className="insight-icon">📖</span>
                          <span className="text-small">{insight}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'risks' && (
            <div className="tab-content">
              <RiskFindings findings={result.risk_findings} />
            </div>
          )}

          {activeTab === 'tests' && (
            <div className="tab-content">
              <TestImpactPanel
                affectedTests={result.affected_tests}
                coverageGaps={result.coverage_gaps}
              />
            </div>
          )}

          {activeTab === 'generated' && (
            <div className="tab-content">
              <GeneratedTestPanel
                generatedTest={result.generated_test}
                verification={result.verification}
              />
              {result.verification && (
                <div style={{ marginTop: 24 }}>
                  <VerificationPanel verification={result.verification} />
                </div>
              )}
            </div>
          )}

          {activeTab === 'report' && (
            <div className="tab-content">
              <FinalReport result={result} />
              <div style={{ marginTop: 24 }}>
                <MetricsPanel metrics={result.metrics} />
              </div>
            </div>
          )}
        </div>
      )}

      <style>{analysisStyles}</style>
    </div>
  );
}

const analysisStyles = `
.analysis-page { min-height: 100vh; }
.analysis-header { background: var(--surface); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; }
.logo-sm { font-weight: 700; color: var(--text); }
.change-bar { background: var(--surface2); border-bottom: 1px solid var(--border); }
.file-chip-sm { background: var(--surface); border: 1px solid var(--border); padding: 1px 6px; border-radius: 3px; font-size: 11px; font-family: var(--mono); color: var(--accent); }
.pipeline-bar { background: var(--bg); border-bottom: 1px solid var(--border); padding: 12px 0; }
.results-container { padding: 24px 0 64px; }
.overview-layout { display: grid; grid-template-columns: 1fr 340px; gap: 24px; }
@media (max-width: 900px) { .overview-layout { grid-template-columns: 1fr; } }
.tab-content { padding: 4px 0 0; }
.tab-badge { background: var(--accent-dim); color: #fff; font-size: 11px; padding: 1px 6px; border-radius: 10px; margin-left: 6px; }
.loading-spinner { width: 32px; height: 32px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto; }
@keyframes spin { to { transform: rotate(360deg); } }
.doc-insights { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; }
.insight-item { display: flex; align-items: flex-start; gap: 8px; padding: 4px 0; }
.insight-icon { flex-shrink: 0; }
.alert { padding: 12px 16px; border-radius: var(--radius); margin-bottom: 16px; }
.alert-danger { background: #3d1f1f; color: var(--danger); border: 1px solid var(--danger); }
`;
