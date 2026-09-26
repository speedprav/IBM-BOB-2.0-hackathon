import React from 'react';
import { AnalysisResult } from '../types/api';

interface Props {
  result: AnalysisResult;
}

export default function FinalReport({ result }: Props) {
  const { summary, risk_findings, affected_tests, coverage_gaps, verification, documentation_insights } = result;
  const breaking = affected_tests.filter(t => t.will_break).length;
  const critical = risk_findings.filter(r => r.severity === 'critical').length;
  const high = risk_findings.filter(r => r.severity === 'high').length;

  const overallRisk = critical > 0 ? 'CRITICAL' : high > 0 ? 'HIGH' : risk_findings.length > 0 ? 'MEDIUM' : 'LOW';
  const riskColor = { CRITICAL: 'var(--critical)', HIGH: '#ff9966', MEDIUM: 'var(--warning)', LOW: 'var(--success)' }[overallRisk];

  return (
    <div className="final-report">
      <div className="report-banner" style={{ borderColor: riskColor }}>
        <div className="report-verdict" style={{ color: riskColor }}>
          {overallRisk} RISK
        </div>
        <div className="report-summary">{summary}</div>
      </div>

      <div className="report-sections">
        {/* Risk summary */}
        <div className="report-section">
          <h4 className="report-section-title">Risk Summary</h4>
          {risk_findings.length === 0 ? (
            <p className="text-muted text-small">No risks identified.</p>
          ) : (
            <div className="risk-table">
              {risk_findings.map(r => (
                <div key={r.id} className="risk-table-row">
                  <span className={`badge badge-${r.severity}`}>{r.severity.toUpperCase()}</span>
                  <span className="risk-table-title">{r.title}</span>
                  <span className="text-small text-muted text-mono">{r.affected_location}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Test impact */}
        <div className="report-section">
          <h4 className="report-section-title">Test Impact</h4>
          <div className="report-stats">
            <div className="report-stat">
              <span className="report-stat-value" style={{ color: breaking > 0 ? 'var(--danger)' : 'var(--success)' }}>
                {breaking}
              </span>
              <span className="report-stat-label">Tests will break</span>
            </div>
            <div className="report-stat">
              <span className="report-stat-value">{affected_tests.length}</span>
              <span className="report-stat-label">Tests affected</span>
            </div>
            <div className="report-stat">
              <span className="report-stat-value">{coverage_gaps.length}</span>
              <span className="report-stat-label">Coverage gaps</span>
            </div>
          </div>
        </div>

        {/* Verification */}
        {verification && (
          <div className="report-section">
            <h4 className="report-section-title">Verification</h4>
            <div className="flex items-center gap-8">
              <span className={`badge ${verification.passed ? 'badge-success' : 'badge-critical'}`}>
                {verification.passed ? '✓ PASSED' : '✗ FAILED'}
              </span>
              <code className="text-small text-mono text-muted">{verification.command}</code>
              <span className="text-small text-muted">{verification.duration_ms}ms</span>
            </div>
          </div>
        )}

        {/* Docs */}
        {documentation_insights.length > 0 && (
          <div className="report-section">
            <h4 className="report-section-title">Documentation Insights</h4>
            <ul className="doc-list">
              {documentation_insights.map((d, i) => (
                <li key={i} className="text-small">{d}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Recommendation */}
        <div className="report-section report-recommendation">
          <h4 className="report-section-title">Recommendation</h4>
          <p className="text-small">
            {overallRisk === 'CRITICAL' || overallRisk === 'HIGH'
              ? '⛔ Do not merge. Address critical/high risk findings and fix breaking tests before proceeding.'
              : overallRisk === 'MEDIUM'
              ? '⚠ Review medium risks before merging. Consider adding the generated regression test to the PR.'
              : '✓ Low risk. Recommended to add the generated regression test for additional confidence.'}
          </p>
        </div>
      </div>

      <style>{styles}</style>
    </div>
  );
}

const styles = `
.final-report { }
.report-banner { border: 2px solid var(--border); border-radius: var(--radius-lg); padding: 20px 24px; margin-bottom: 24px; background: var(--surface); }
.report-verdict { font-size: 24px; font-weight: 800; margin-bottom: 8px; }
.report-summary { color: var(--text-muted); font-size: 14px; line-height: 1.6; }
.report-sections { display: flex; flex-direction: column; gap: 20px; }
.report-section { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px 18px; }
.report-section-title { color: var(--text); margin-bottom: 12px; font-size: 13px; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 600; }
.risk-table { display: flex; flex-direction: column; gap: 6px; }
.risk-table-row { display: flex; align-items: center; gap: 10px; padding: 6px 0; border-bottom: 1px solid var(--border); }
.risk-table-row:last-child { border-bottom: none; }
.risk-table-title { flex: 1; font-size: 13px; color: var(--text); }
.report-stats { display: flex; gap: 24px; }
.report-stat { display: flex; flex-direction: column; gap: 2px; }
.report-stat-value { font-size: 22px; font-weight: 700; }
.report-stat-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; }
.doc-list { padding-left: 18px; color: var(--text-muted); }
.doc-list li { margin-bottom: 4px; }
.report-recommendation { background: #0d1a0d; border-color: var(--success); }
.report-recommendation .report-section-title { color: var(--success); }
`;
