import React, { useState } from 'react';
import { VerificationResult } from '../types/api';

interface Props {
  verification: VerificationResult;
}

export default function VerificationPanel({ verification }: Props) {
  const [showFull, setShowFull] = useState(false);
  const truncated = verification.output.length > 1000;
  const displayOutput = showFull ? verification.output : verification.output.slice(0, 1000);

  return (
    <div className="verification-panel">
      <div className="ver-header">
        <div className="flex items-center gap-12">
          <h3>Verification Results</h3>
          <span className={`badge ${verification.passed ? 'badge-success' : 'badge-critical'}`}>
            {verification.passed ? '✓ PASSED' : '✗ FAILED'}
          </span>
        </div>
        <div className="flex items-center gap-12 text-small text-muted">
          <span>Duration: <strong>{verification.duration_ms}ms</strong></span>
          <code className="text-mono">{verification.command}</code>
        </div>
      </div>

      <div className={`ver-output code-block ${!verification.passed ? 'ver-output-failed' : ''}`}>
        {displayOutput}
        {truncated && !showFull && (
          <div className="show-more">
            <button className="btn btn-secondary" style={{ marginTop: 8, fontSize: 12 }} onClick={() => setShowFull(true)}>
              Show full output
            </button>
          </div>
        )}
      </div>

      <style>{styles}</style>
    </div>
  );
}

const styles = `
.verification-panel { }
.ver-header { margin-bottom: 12px; display: flex; flex-direction: column; gap: 6px; }
.ver-output { max-height: 400px; overflow-y: auto; }
.ver-output-failed { border-color: var(--danger); }
.show-more { display: flex; justify-content: center; }
`;
