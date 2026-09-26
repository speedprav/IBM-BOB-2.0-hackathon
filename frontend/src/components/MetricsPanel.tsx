import React from 'react';
import { ProductivityMetrics } from '../types/api';

interface Props {
  metrics: ProductivityMetrics;
}

export default function MetricsPanel({ metrics }: Props) {
  const saved = Math.max(0, metrics.baseline_estimate_minutes - Math.ceil(metrics.measured_duration_seconds / 60));
  const pct = Math.round((saved / Math.max(metrics.baseline_estimate_minutes, 1)) * 100);

  const rows = [
    { label: 'Files analyzed', value: metrics.files_analyzed, note: 'Measured prototype run', highlight: false },
    { label: 'Files impacted', value: metrics.files_impacted, note: 'Measured prototype run', highlight: true },
    { label: 'Symbols impacted', value: metrics.symbols_impacted, note: 'Measured prototype run', highlight: true },
    { label: 'Tests affected', value: metrics.tests_affected, note: 'Measured prototype run', highlight: true },
    { label: 'Tests generated', value: metrics.tests_generated, note: 'Measured prototype run', highlight: true },
    { label: 'Risks detected', value: metrics.risks_detected, note: 'Measured prototype run', highlight: true },
    { label: 'Workflow steps automated', value: metrics.workflow_steps_automated, note: 'Measured prototype run', highlight: false },
    { label: 'Baseline estimate', value: `~${metrics.baseline_estimate_minutes} min`, note: 'Baseline estimate — manual investigation', highlight: false },
    { label: 'DevTwin time', value: `${metrics.measured_duration_seconds}s`, note: 'Measured prototype run', highlight: false },
    { label: 'Time saved', value: `~${saved} min (${pct}%)`, note: 'Baseline estimate vs. measured run', highlight: true },
  ];

  return (
    <div className="metrics-panel">
      <h3 style={{ marginBottom: 16 }}>Productivity Metrics</h3>
      <div className="metrics-note">
        All metrics are transparently labeled. Values marked <strong>Baseline estimate</strong> are based
        on typical manual investigation time. Values marked <strong>Measured prototype run</strong> are
        directly observed from this analysis run.
      </div>

      <table className="metrics-table">
        <tbody>
          {rows.map(row => (
            <tr key={row.label} className={row.highlight ? 'metrics-row-highlight' : ''}>
              <td className="metrics-label">{row.label}</td>
              <td className="metrics-value">{row.value}</td>
              <td className="metrics-note-cell text-muted text-small">{row.note}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <style>{styles}</style>
    </div>
  );
}

const styles = `
.metrics-panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; }
.metrics-note { color: var(--text-muted); font-size: 12px; margin-bottom: 16px; padding: 10px 12px; background: var(--surface2); border-radius: var(--radius); border: 1px solid var(--border); }
.metrics-table { width: 100%; border-collapse: collapse; }
.metrics-table tr { border-bottom: 1px solid var(--border); }
.metrics-table tr:last-child { border-bottom: none; }
.metrics-label { padding: 8px 0; color: var(--text-muted); font-size: 13px; width: 40%; }
.metrics-value { padding: 8px 12px; font-weight: 600; font-size: 14px; font-variant-numeric: tabular-nums; }
.metrics-note-cell { padding: 8px 0; font-size: 11px; }
.metrics-row-highlight .metrics-value { color: var(--accent); }
`;
