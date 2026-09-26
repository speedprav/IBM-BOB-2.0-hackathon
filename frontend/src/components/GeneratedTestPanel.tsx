import React, { useState } from 'react';
import { GeneratedTest, VerificationResult } from '../types/api';

interface Props {
  generatedTest?: GeneratedTest;
  verification?: VerificationResult;
}

export default function GeneratedTestPanel({ generatedTest, verification }: Props) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (generatedTest?.content) {
      navigator.clipboard.writeText(generatedTest.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!generatedTest) {
    return (
      <div className="empty-state">
        <p className="text-muted">No test was generated.</p>
      </div>
    );
  }

  return (
    <div className="generated-test">
      <div className="gen-header">
        <div>
          <h3>{generatedTest.file_name}</h3>
          <p className="text-small text-muted" style={{ marginTop: 4 }}>
            {generatedTest.rationale}
          </p>
        </div>
        <div className="flex gap-8">
          <button className="btn btn-secondary" onClick={handleCopy}>
            {copied ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      </div>

      {generatedTest.covers_risk_ids.length > 0 && (
        <div className="covers-risks">
          <span className="text-small text-muted">Covers risks: </span>
          <span className="text-small">{generatedTest.covers_risk_ids.length} finding(s)</span>
        </div>
      )}

      <div className="code-block" style={{ marginTop: 16 }}>
        {renderDiff(generatedTest.content)}
      </div>

      <style>{styles}</style>
    </div>
  );
}

function renderDiff(content: string) {
  return content.split('\n').map((line, i) => {
    const cls = line.startsWith('+') && !line.startsWith('+++')
      ? 'diff-add'
      : line.startsWith('-') && !line.startsWith('---')
      ? 'diff-remove'
      : line.startsWith('@@')
      ? 'diff-meta'
      : '';
    return (
      <div key={i} className={cls}>
        {line}
      </div>
    );
  });
}

const styles = `
.generated-test { }
.gen-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 12px; }
.covers-risks { display: flex; align-items: center; gap: 8px; background: var(--surface2); border: 1px solid var(--border); border-radius: var(--radius); padding: 6px 12px; }
.empty-state { padding: 24px; text-align: center; }
`;
