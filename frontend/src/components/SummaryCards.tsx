import React from 'react';
import { AnalysisResult } from '../types/api';

interface Props {
  result: AnalysisResult;
}

export default function SummaryCards({ result }: Props) {
  const { metrics, risk_findings, affected_tests, verification } = result;

  const highestSeverity = risk_findings.length > 0
    ? risk_findings.reduce((acc, r) => {
        const order = ['critical', 'high', 'medium', 'low', 'info'];
        return order.indexOf(r.severity) < order.indexOf(acc) ? r.severity : acc;
      }, 'info')
    : 'none';

  const breaking = affected_tests.filter(t => t.will_break).length;

  const cards = [
    {
      label: 'Risk Level',
      value: highestSeverity.toUpperCase(),
      sub: `${risk_findings.length} finding(s)`,
      color: SEVERITY_COLORS[highestSeverity] || 'var(--text-muted)',
    },
    {
      label: 'Files Impacted',
      value: String(metrics.files_impacted),
      sub: `of ${metrics.files_analyzed} analyzed`,
      color: metrics.files_impacted > 0 ? 'var(--warning)' : 'var(--success)',
    },
    {
      label: 'Symbols Impacted',
      value: String(metrics.symbols_impacted),
      sub: 'direct + indirect',
      color: metrics.symbols_impacted > 0 ? 'var(--warning)' : 'var(--success)',
    },
    {
      label: 'Tests Affected',
      value: String(metrics.tests_affected),
      sub: `${breaking} will break`,
      color: breaking > 0 ? 'var(--danger)' : metrics.tests_affected > 0 ? 'var(--warning)' : 'var(--success)',
    },
    {
      label: 'Test Generated',
      value: '1',
      sub: 'regression test',
      color: 'var(--accent)',
    },
    {
      label: 'Verification',
      value: verification?.passed ? 'PASS' : verification?.status === 'failed' ? 'FAIL' : 'N/A',
      sub: verification ? `${verification.duration_ms}ms` : '—',
      color: verification?.passed ? 'var(--success)' : verification ? 'var(--danger)' : 'var(--text-muted)',
    },
  ];

  return (
    <div className="summary-cards">
      {cards.map(card => (
        <div key={card.label} className="summary-card">
          <div className="summary-card-label">{card.label}</div>
          <div className="summary-card-value" style={{ color: card.color }}>
            {card.value}
          </div>
          <div className="summary-card-sub text-muted text-small">{card.sub}</div>
        </div>
      ))}
      <style>{styles}</style>
    </div>
  );
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'var(--critical)',
  high: '#ff9966',
  medium: 'var(--warning)',
  low: 'var(--accent)',
  info: '#79c0ff',
  none: 'var(--success)',
};

const styles = `
.summary-cards {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
  margin-bottom: 28px;
}
@media (max-width: 1100px) { .summary-cards { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 600px)  { .summary-cards { grid-template-columns: repeat(2, 1fr); } }
.summary-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px 16px;
  text-align: center;
}
.summary-card-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }
.summary-card-value { font-size: 22px; font-weight: 700; margin-bottom: 4px; font-variant-numeric: tabular-nums; }
.summary-card-sub { font-size: 11px; }
`;
