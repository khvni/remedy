export type Repo = {
  id: string;
  name: string;
  url: string;
  default_branch?: string | null;
  created_at: string;
};

export type Scan = {
  id: string;
  repo_id: string;
  kind: string;
  status: string;
  created_at: string;
};

export type Finding = {
  id: string;
  scan_id: string;
  severity: string;
  path: string;
  line?: number | null;
  rule_id?: string | null;
  description?: string | null;
};

export type PullRequest = {
  id: string;
  repo_id: string;
  branch: string;
  pr_url?: string | null;
  status: string;
  summary?: string | null;
  created_at: string;
};

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/$/, '');

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(init?.headers ?? {}),
      },
      ...init,
    });
    if (!response.ok) {
      const detail = await response.text().catch(() => '');
      const message = detail || response.statusText || `HTTP ${response.status}`;
      throw new Error(message);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('Unable to reach Remedy API');
  }
}

export function fetchRepos(): Promise<{ items: Repo[] }> {
  return request('/repos');
}

export function fetchScans(repoId?: string): Promise<Scan[]> {
  const query = repoId ? `?repo_id=${encodeURIComponent(repoId)}` : '';
  return request(`/scans${query}`);
}

export function fetchFindings(repoId?: string, scanId?: string): Promise<Finding[]> {
  const params = new URLSearchParams();
  if (repoId) params.append('repo_id', repoId);
  if (scanId) params.append('scan_id', scanId);
  const suffix = params.toString() ? `?${params.toString()}` : '';
  return request(`/findings${suffix}`);
}

export function fetchPullRequests(repoId?: string): Promise<PullRequest[]> {
  const query = repoId ? `?repo_id=${encodeURIComponent(repoId)}` : '';
  return request(`/prs${query}`);
}

export function registerRepo(url: string): Promise<Repo> {
  return request('/repos', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

export function triggerScan(repoId: string, kinds: string[] = ['sast', 'sca']): Promise<{ repo_id: string; queued_jobs: string[] }> {
  return request('/scans', {
    method: 'POST',
    body: JSON.stringify({ repo_id: repoId, kinds }),
  });
}
