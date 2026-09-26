import React, { useEffect, useState } from 'react';
import { api } from '../api';
import { Project } from '../types/api';
import { AppState } from '../App';

interface Props {
  onStartAnalysis: (state: AppState) => void;
}

export default function LandingPage({ onStartAnalysis }: Props) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [demoMode, setDemoMode] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [changeDescription, setChangeDescription] = useState('');
  const [diffText, setDiffText] = useState('');
  const [changedFiles, setChangedFiles] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.listProjects()
      .then(data => { setProjects(data.projects); setDemoMode(data.demo_mode); })
      .catch(() => setError('Failed to connect to DevTwin backend. Is the server running?'))
      .finally(() => setLoadingProjects(false));
  }, []);

  const handleLoadDemoChange = async () => {
    if (!selectedProject) return;
    setLoading(true);
    try {
      const demo = await api.getDemoChange(selectedProject.id);
      setChangeDescription(demo.description);
      setDiffText(demo.diff);
      setChangedFiles(demo.changed_files);
    } catch {
      setError('Failed to load demo change.');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = () => {
    if (!selectedProject || !changeDescription.trim()) return;
    onStartAnalysis({
      projectId: selectedProject.id,
      projectName: selectedProject.name,
      projectPath: selectedProject.path,
      changeDescription,
      diffText,
      changedFiles,
      analysisId: null,
      result: null,
    });
  };

  const canAnalyze = selectedProject && changeDescription.trim().length > 0;

  return (
    <div className="landing">
      {/* Header */}
      <header className="landing-header">
        <div className="container">
          <div className="flex items-center justify-between" style={{ padding: '20px 0' }}>
            <div className="flex items-center gap-12">
              <div className="logo">
                <span className="logo-icon">⬡</span>
                <span className="logo-text">DevTwin</span>
              </div>
              <span className="badge badge-muted">IBM Bob 2.0 Hackathon</span>
            </div>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="hero">
        <div className="container">
          <div className="hero-content">
            <h1 className="hero-title">Know the impact<br />before you merge.</h1>
            <p className="hero-subtitle">
              DevTwin simulates proposed code changes against your repository — surfacing
              hidden dependencies, blast radius, broken tests, and security risks before they reach production.
            </p>
            <div className="hero-pipeline">
              {['Repository Map', 'Dependency Scan', 'Risk Analysis', 'Test Impact', 'Test Generation', 'Verification', 'Final Report'].map((step, i) => (
                <React.Fragment key={step}>
                  <span className="pipeline-step">{step}</span>
                  {i < 6 && <span className="pipeline-arrow">→</span>}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Main form */}
      <section className="section">
        <div className="container">
          <div className="analysis-form-wrapper">
            {error && (
              <div className="alert alert-danger" style={{ marginBottom: 20 }}>
                ⚠ {error}
              </div>
            )}
            {demoMode && !error && (
              <div className="alert alert-info" style={{ marginBottom: 20 }}>
                🎭 <strong>Demo Mode</strong> — No GEMINI_API_KEY set. Running with pre-computed realistic results for the Demo Orders scenario.
                Get a free key at <a href="https://aistudio.google.com/app/apikey" target="_blank" rel="noreferrer" style={{ color: 'var(--accent)' }}>aistudio.google.com</a> for live AI analysis.
              </div>
            )}

            {/* Step 1: Select Project */}
            <div className="form-section">
              <div className="form-section-header">
                <span className="step-number">1</span>
                <h3>Select Project</h3>
              </div>
              {loadingProjects ? (
                <p className="text-muted">Loading projects…</p>
              ) : (
                <div className="project-cards">
                  {projects.map(p => (
                    <button
                      key={p.id}
                      className={`project-card ${selectedProject?.id === p.id ? 'selected' : ''}`}
                      onClick={() => setSelectedProject(p)}
                    >
                      <div className="project-card-name">{p.name}</div>
                      <div className="project-card-desc text-muted">{p.description}</div>
                      <div className="flex gap-8" style={{ marginTop: 8 }}>
                        <span className="badge badge-muted">{p.language}</span>
                        <span className="badge badge-muted">{p.files} files</span>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Step 2: Describe Change */}
            <div className="form-section">
              <div className="form-section-header">
                <span className="step-number">2</span>
                <h3>Describe Proposed Change</h3>
              </div>
              <div className="form-group">
                <label className="form-label">What are you changing?</label>
                <input
                  type="text"
                  value={changeDescription}
                  onChange={e => setChangeDescription(e.target.value)}
                  placeholder="e.g. Allow customers to update orders in CONFIRMED status"
                  disabled={!selectedProject}
                />
                <span className="form-hint">Plain English description of your proposed change</span>
              </div>
            </div>

            {/* Step 3: Provide Diff */}
            <div className="form-section">
              <div className="form-section-header">
                <span className="step-number">3</span>
                <h3>Provide Diff (optional)</h3>
                <div style={{ marginLeft: 'auto' }}>
                  <button
                    className="btn btn-secondary"
                    onClick={handleLoadDemoChange}
                    disabled={!selectedProject || loading}
                  >
                    {loading ? 'Loading…' : '↓ Load Demo Change'}
                  </button>
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Unified diff</label>
                <textarea
                  rows={12}
                  value={diffText}
                  onChange={e => setDiffText(e.target.value)}
                  placeholder="Paste unified diff here, or click 'Load Demo Change' above…"
                  disabled={!selectedProject}
                />
              </div>
              {changedFiles.length > 0 && (
                <div className="changed-files-preview">
                  <span className="text-muted text-small">Changed files: </span>
                  {changedFiles.map(f => (
                    <code key={f} className="file-chip">{f}</code>
                  ))}
                </div>
              )}
            </div>

            {/* Analyze button */}
            <div className="form-actions">
              <button
                className="btn btn-primary btn-lg analyze-btn"
                onClick={handleAnalyze}
                disabled={!canAnalyze}
              >
                ⚡ Analyze Change
              </button>
              {!canAnalyze && (
                <span className="text-muted text-small">
                  {!selectedProject ? 'Select a project first' : 'Enter a change description'}
                </span>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Feature strip */}
      <section className="features-section">
        <div className="container">
          <div className="grid-3">
            {[
              { icon: '⬡', title: 'Blast Radius Graph', desc: 'Visual map of every file, symbol, and module affected by your change.' },
              { icon: '⚠', title: 'AI Risk Analysis', desc: 'Security, regression, API contract, and data risks — with evidence and mitigations.' },
              { icon: '✓', title: 'Regression Tests', desc: 'AI-generated tests targeting the exact gaps exposed by your change, run and verified.' },
            ].map(f => (
              <div key={f.title} className="feature-card">
                <div className="feature-icon">{f.icon}</div>
                <h4>{f.title}</h4>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <style>{landingStyles}</style>
    </div>
  );
}

const landingStyles = `
.landing { min-height: 100vh; }

.landing-header {
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.logo { display: flex; align-items: center; gap: 8px; }
.logo-icon { font-size: 22px; color: var(--accent); }
.logo-text { font-size: 18px; font-weight: 700; color: var(--text); }

.hero { padding: 64px 0 40px; }
.hero-title { font-size: 3rem; font-weight: 800; line-height: 1.15; margin-bottom: 16px; color: var(--text); }
.hero-subtitle { font-size: 1.1rem; color: var(--text-muted); max-width: 600px; margin-bottom: 32px; }
.hero-pipeline {
  display: flex; flex-wrap: wrap; align-items: center; gap: 8px;
  font-size: 12px; color: var(--text-muted);
}
.pipeline-step {
  background: var(--surface2); border: 1px solid var(--border);
  padding: 4px 10px; border-radius: 12px; color: var(--text);
}
.pipeline-arrow { color: var(--accent); }

.analysis-form-wrapper {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 32px;
  max-width: 800px;
  margin: 0 auto;
}

.form-section { margin-bottom: 28px; }
.form-section-header {
  display: flex; align-items: center; gap: 12px;
  margin-bottom: 16px;
}
.step-number {
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--accent-dim); color: #fff;
  font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.project-cards { display: flex; flex-wrap: wrap; gap: 12px; }
.project-card {
  background: var(--surface2); border: 2px solid var(--border);
  border-radius: var(--radius-lg); padding: 16px 20px;
  cursor: pointer; text-align: left; transition: border-color .15s;
  min-width: 220px;
}
.project-card:hover { border-color: var(--accent-dim); }
.project-card.selected { border-color: var(--accent); }
.project-card-name { font-weight: 600; margin-bottom: 4px; color: var(--text); }
.project-card-desc { font-size: 13px; margin-bottom: 8px; }

.changed-files-preview { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; }
.file-chip {
  background: var(--surface2); border: 1px solid var(--border);
  padding: 2px 8px; border-radius: var(--radius);
  font-size: 12px; font-family: var(--mono); color: var(--accent);
}

.form-actions { display: flex; align-items: center; gap: 16px; padding-top: 8px; }
.analyze-btn { min-width: 200px; justify-content: center; }

.alert { padding: 12px 16px; border-radius: var(--radius); }
.alert-danger { background: #3d1f1f; color: var(--danger); border: 1px solid var(--danger); }
.alert-info { background: #1a2a3d; color: var(--accent); border: 1px solid var(--accent-dim); line-height: 1.5; }

.features-section { padding: 48px 0 64px; border-top: 1px solid var(--border); }
.feature-card { padding: 24px; }
.feature-icon { font-size: 24px; margin-bottom: 12px; }
.feature-card h4 { color: var(--text); margin-bottom: 6px; }
`;
