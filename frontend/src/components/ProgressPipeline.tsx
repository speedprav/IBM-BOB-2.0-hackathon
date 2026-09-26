import React from 'react';
import { ProgressStep } from '../types/api';

interface Props {
  steps: ProgressStep[];
  isRunning: boolean;
}

const STEP_ORDER = ['scan', 'graph', 'diff', 'deps', 'risk', 'tests', 'docs', 'gen', 'verify'];

export default function ProgressPipeline({ steps, isRunning }: Props) {
  const stepsMap = Object.fromEntries(steps.map(s => [s.id, s]));

  const displaySteps = STEP_ORDER.map(id => ({
    id,
    step: stepsMap[id] || null,
    name: STEP_LABELS[id] || id,
  }));

  return (
    <div className="progress-pipeline">
      {displaySteps.map(({ id, step, name }, i) => {
        const status = step?.status || 'pending';
        return (
          <React.Fragment key={id}>
            <div className={`pp-step pp-step-${status}`}>
              <div className={`pp-dot dot dot-${status}`} />
              <div className="pp-label">{name}</div>
              {step?.detail && (
                <div className="pp-detail text-small text-muted">{step.detail}</div>
              )}
            </div>
            {i < displaySteps.length - 1 && (
              <div className={`pp-connector ${status === 'complete' ? 'pp-connector-done' : ''}`} />
            )}
          </React.Fragment>
        );
      })}
      <style>{styles}</style>
    </div>
  );
}

const STEP_LABELS: Record<string, string> = {
  scan: 'Repo Scan',
  graph: 'Dep. Graph',
  diff: 'Diff Parse',
  deps: 'Blast Radius',
  risk: 'Risk AI',
  tests: 'Test AI',
  docs: 'Doc AI',
  gen: 'Test Gen',
  verify: 'Verify',
};

const styles = `
.progress-pipeline {
  display: flex; align-items: flex-start; gap: 0;
  overflow-x: auto; padding: 4px 0;
}
.pp-step {
  display: flex; flex-direction: column; align-items: center;
  min-width: 80px; gap: 4px; text-align: center;
}
.pp-dot { margin: 0 auto; }
.pp-label { font-size: 11px; color: var(--text-muted); white-space: nowrap; }
.pp-step-running .pp-label { color: var(--accent); font-weight: 500; }
.pp-step-complete .pp-label { color: var(--success); }
.pp-step-failed .pp-label { color: var(--danger); }
.pp-detail { display: none; }
.pp-connector {
  flex: 1; height: 2px; background: var(--border);
  margin-top: 8px; min-width: 12px;
}
.pp-connector-done { background: var(--success); }
`;
