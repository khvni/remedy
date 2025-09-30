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

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
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
