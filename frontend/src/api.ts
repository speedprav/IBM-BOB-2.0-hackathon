import {
  Project,
  AnalysisResult,
  AnalysisStatusResponse,
} from './types/api';

// In Vercel multi-service mode, /api is proxied by Vercel to the backend service.
// In local dev, Vite proxy forwards /api → localhost:8000.
// VITE_API_URL can override for standalone Render/other deployments.
const BASE = (import.meta.env.VITE_API_URL ?? '') + '/api';

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  async listProjects(): Promise<{ projects: Project[]; demo_mode: boolean }> {
    return fetchJson<{ projects: Project[]; demo_mode: boolean }>('/projects');
  },

  async getDemoChange(projectId: string): Promise<{
    project_id: string;
    description: string;
    diff: string;
    changed_files: string[];
  }> {
    return fetchJson(`/projects/${projectId}/change`);
  },

  async startAnalysis(params: {
    project_path: string;
    change_description: string;
    diff_text?: string;
    changed_files?: string[];
  }): Promise<{ analysis_id: string }> {
    return fetchJson('/analyze', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async getAnalysisStatus(analysisId: string): Promise<AnalysisStatusResponse> {
    return fetchJson(`/analyze/${analysisId}`);
  },

  async pollUntilComplete(
    analysisId: string,
    onProgress: (status: AnalysisStatusResponse) => void,
    intervalMs = 1500
  ): Promise<AnalysisResult> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const status = await api.getAnalysisStatus(analysisId);
          onProgress(status);
          if (status.status === 'complete' && status.result) {
            resolve(status.result);
          } else if (status.status === 'failed') {
            reject(new Error(status.error || 'Analysis failed'));
          } else {
            setTimeout(poll, intervalMs);
          }
        } catch (err) {
          reject(err);
        }
      };
      poll();
    });
  },
};
