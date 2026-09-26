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

function parseSseChunk(
  chunk: string,
  onEvent: (status: AnalysisStatusResponse) => void
): void {
  const blocks = chunk.split('\n\n');
  for (const block of blocks) {
    const line = block
      .split('\n')
      .map((l) => l.trimEnd())
      .find((l) => l.startsWith('data:'));
    if (!line) continue;
    const payload = line.slice(5).trim();
    if (!payload) continue;
    try {
      onEvent(JSON.parse(payload) as AnalysisStatusResponse);
    } catch {
      // ignore partial/malformed frames
    }
  }
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

  /**
   * Preferred path on Vercel: one long-lived request streams progress + result.
   * Avoids 404 "Analysis not found" from polling across separate serverless instances.
   */
  async streamAnalysis(
    params: {
      project_path: string;
      change_description: string;
      diff_text?: string;
      changed_files?: string[];
    },
    onProgress: (status: AnalysisStatusResponse) => void
  ): Promise<AnalysisResult> {
    const res = await fetch(`${BASE}/analyze/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify(params),
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`API error ${res.status}: ${body}`);
    }
    if (!res.body) {
      throw new Error('Streaming not supported by this browser/environment');
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let lastStatus: AnalysisStatusResponse | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Keep a trailing partial frame in the buffer
      const lastSep = buffer.lastIndexOf('\n\n');
      if (lastSep === -1) continue;
      const complete = buffer.slice(0, lastSep + 2);
      buffer = buffer.slice(lastSep + 2);
      parseSseChunk(complete, (status) => {
        lastStatus = status;
        onProgress(status);
      });
    }

    if (buffer.trim()) {
      parseSseChunk(buffer + '\n\n', (status) => {
        lastStatus = status;
        onProgress(status);
      });
    }

    if (!lastStatus) {
      throw new Error('Analysis stream ended with no status updates');
    }
    if (lastStatus.status === 'complete' && lastStatus.result) {
      return lastStatus.result;
    }
    if (lastStatus.status === 'failed') {
      throw new Error(lastStatus.error || 'Analysis failed');
    }
    throw new Error('Analysis stream ended before completion');
  },

  async pollUntilComplete(
    analysisId: string,
    onProgress: (status: AnalysisStatusResponse) => void,
    intervalMs = 1500
  ): Promise<AnalysisResult> {
    return new Promise((resolve, reject) => {
      let notFoundRetries = 0;
      const poll = async () => {
        try {
          const status = await api.getAnalysisStatus(analysisId);
          notFoundRetries = 0;
          onProgress(status);
          if (status.status === 'complete' && status.result) {
            resolve(status.result);
          } else if (status.status === 'failed') {
            reject(new Error(status.error || 'Analysis failed'));
          } else {
            setTimeout(poll, intervalMs);
          }
        } catch (err: any) {
          const msg = String(err?.message || err);
          // Brief tolerance for cold starts; still fail if the job is truly gone
          if (msg.includes('404') && notFoundRetries < 3) {
            notFoundRetries += 1;
            setTimeout(poll, intervalMs);
            return;
          }
          reject(err);
        }
      };
      poll();
    });
  },
};
