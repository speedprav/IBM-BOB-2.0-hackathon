import React from 'react';
import { TestImpact } from '../types/api';

interface Props {
  affectedTests: TestImpact[];
  coverageGaps: string[];
}

export default function TestImpactPanel({ affectedTests, coverageGaps }: Props) {
  const breaking = affectedTests.filter(t => t.will_break);
  const related = affectedTests.filter(t => !t.will_break);

  return (
    <div className="test-impact">
      {/* Breaking tests */}
      {breaking.length > 0 && (
        <div className="test-section">
          <div className="test-section-header">
            <span className="badge badge-critical">WILL BREAK</span>
            <span className="text-muted text-small">{breaking.length} test(s) will fail after this change</span>
          </div>
          {breaking.map((t, i) => <TestRow key={i} test={t} />)}
        </div>
      )}

      {/* Related tests */}
      {related.length > 0 && (
        <div className="test-section" style={{ marginTop: 20 }}>
          <div className="test-section-header">
            <span className="badge badge-medium">AFFECTED</span>
            <span className="text-muted text-small">{related.length} test(s) may need review</span>
          </div>
          {related.map((t, i) => <TestRow key={i} test={t} />)}
        </div>
      )}

      {/* Coverage gaps */}
      {coverageGaps.length > 0 && (
        <div className="test-section" style={{ marginTop: 20 }}>
          <div className="test-section-header">
            <span className="badge badge-muted">COVERAGE GAPS</span>
            <span className="text-muted text-small">{coverageGaps.length} missing test scenario(s)</span>
          </div>
          {coverageGaps.map((gap, i) => (
            <div key={i} className="gap-item">
              <span className="gap-icon">⚠</span>
              <span className="text-small">{gap}</span>
            </div>
          ))}
        </div>
      )}

      {affectedTests.length === 0 && coverageGaps.length === 0 && (
        <div className="empty-state">
          <p className="text-muted">No test impact data available.</p>
        </div>
      )}

      <style>{styles}</style>
    </div>
  );
}

function TestRow({ test }: { test: TestImpact }) {
  return (
    <div className={`test-row ${test.will_break ? 'test-row-breaking' : ''}`}>
      <div className="flex items-center gap-8">
        <span className={`badge ${test.will_break ? 'badge-critical' : 'badge-muted'}`}>
          {test.relevance.replace('_', ' ')}
        </span>
        <code className="test-name">{test.test_name}</code>
      </div>
      <div className="test-file text-small text-muted text-mono">{test.test_file}</div>
      <div className="test-reason text-small text-muted">{test.reason}</div>
    </div>
  );
}

const styles = `
.test-impact { }
.test-section { }
.test-section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.test-row {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px 14px;
  margin-bottom: 8px; display: flex; flex-direction: column; gap: 4px;
}
.test-row-breaking { border-left: 3px solid var(--critical); }
.test-name { font-family: var(--mono); font-size: 13px; color: var(--text); }
.test-file { }
.test-reason { }
.gap-item { display: flex; align-items: flex-start; gap: 8px; padding: 8px 12px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 6px; }
.gap-icon { color: var(--warning); flex-shrink: 0; }
.empty-state { padding: 24px; text-align: center; }
`;
