import React, { useState } from 'react';
import { RiskFinding } from '../types/api';

interface Props {
  findings: RiskFinding[];
  compact?: boolean;
}

export default function RiskFindings({ findings, compact = false }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  if (findings.length === 0) {
    return (
      <div className="empty-state">
        <p className="text-muted">No risk findings identified.</p>
      </div>
    );
  }

  const sorted = [...findings].sort((a, b) => {
    const order = ['critical', 'high', 'medium', 'low', 'info'];
    return order.indexOf(a.severity) - order.indexOf(b.severity);
  });

  return (
    <div className="risk-findings">
      {sorted.map(finding => (
        <div key={finding.id} className={`risk-card risk-card-${finding.severity}`}>
          <div
            className="risk-card-header"
            onClick={() => !compact && setExpanded(expanded === finding.id ? null : finding.id)}
            style={{ cursor: compact ? 'default' : 'pointer' }}
          >
            <div className="flex items-center gap-8">
              <span className={`badge badge-${finding.severity}`}>
                {finding.severity.toUpperCase()}
              </span>
              <span className={`badge badge-muted`}>{finding.category.replace('_', ' ')}</span>
            </div>
            <div className="risk-title">{finding.title}</div>
            {!compact && (
              <div className="risk-location text-small text-mono text-muted">
                {finding.affected_location}
              </div>
            )}
            {!compact && (
              <span className="expand-icon text-muted">
                {expanded === finding.id ? '▲' : '▼'}
              </span>
            )}
          </div>

          {(compact || expanded === finding.id) && (
            <div className="risk-card-body">
              {!compact && (
                <div className="risk-section">
                  <div className="risk-section-label">Description</div>
                  <div>{finding.description}</div>
                </div>
              )}
              <div className="risk-section">
                <div className="risk-section-label">Why it matters</div>
                <div>{finding.why_it_matters}</div>
              </div>
              {!compact && (
                <>
                  <div className="risk-section">
                    <div className="risk-section-label">Evidence</div>
                    <div className="evidence-box">{finding.evidence}</div>
                  </div>
                  <div className="risk-section">
                    <div className="risk-section-label">Suggested mitigation</div>
                    <div className="mitigation-box">{finding.suggested_mitigation}</div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      ))}

      <style>{styles}</style>
    </div>
  );
}

const styles = `
.risk-findings { display: flex; flex-direction: column; gap: 10px; }
.risk-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
.risk-card-critical { border-left: 3px solid var(--critical); }
.risk-card-high     { border-left: 3px solid #ff9966; }
.risk-card-medium   { border-left: 3px solid var(--warning); }
.risk-card-low      { border-left: 3px solid var(--accent); }
.risk-card-info     { border-left: 3px solid #79c0ff; }
.risk-card-header { padding: 12px 14px; display: flex; flex-direction: column; gap: 6px; position: relative; }
.risk-title { font-weight: 600; color: var(--text); font-size: 14px; }
.risk-location { }
.expand-icon { position: absolute; right: 14px; top: 14px; font-size: 11px; }
.risk-card-body { padding: 0 14px 14px; border-top: 1px solid var(--border); }
.risk-section { margin-top: 12px; }
.risk-section-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); margin-bottom: 4px; font-weight: 600; }
.evidence-box { background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); padding: 10px 12px; font-family: var(--mono); font-size: 12px; color: var(--text); }
.mitigation-box { background: #0d2d0d; border: 1px solid #1a3d1a; border-radius: var(--radius); padding: 10px 12px; color: var(--success); font-size: 13px; }
.empty-state { padding: 24px; text-align: center; }
`;
