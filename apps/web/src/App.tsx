import { useEffect, useMemo, useState } from 'react';
import {
  fetchFindings,
  fetchPullRequests,
  fetchRepos,
  fetchScans,
  type Finding,
  type PullRequest,
  type Repo,
  type Scan,
} from './api';
import { RepoSelector } from './components/RepoSelector';
import { Scans } from './pages/Scans';
import { PullRequests } from './pages/PRs';

function dedupeFindings(allFindings: Finding[], scanId: string | null): Finding[] {
  if (!scanId) {
    return allFindings;
  }
  return allFindings.filter((finding) => finding.scan_id === scanId);
}

export default function App() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([]);
  const [repoFilter, setRepoFilter] = useState<string | null>(null);
  const [scanFilter, setScanFilter] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reload = async (repoId: string | null) => {
    try {
      setLoading(true);
      setError(null);
      const [repoPayload, scanList, findingList, prList] = await Promise.all([
        fetchRepos(),
        fetchScans(repoId ?? undefined),
        fetchFindings(repoId ?? undefined, scanFilter ?? undefined),
        fetchPullRequests(repoId ?? undefined),
      ]);
      setRepos(repoPayload.items);
      setScans(scanList);
      setFindings(findingList);
      setPullRequests(prList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void reload(repoFilter);
  }, [repoFilter, scanFilter]);

  const filteredFindings = useMemo(() => dedupeFindings(findings, scanFilter), [findings, scanFilter]);

  return (
    <main>
      <h1>Remedy Dashboard</h1>
      <p>Track registered repositories, scans, prioritized findings, and Remedy-authored pull requests.</p>
      <RepoSelector
        repos={repos}
        selectedId={repoFilter}
        onChange={(next) => {
          setRepoFilter(next);
          setScanFilter(null);
        }}
        onRefresh={() => void reload(repoFilter)}
      />
      {error && (
        <p style={{ color: '#c026d3', marginTop: '1rem' }}>
          Failed to load data: {error}
        </p>
      )}
      {loading && <p style={{ marginTop: '1rem' }}>Loading data…</p>}
      <Scans
        scans={scans}
        findings={filteredFindings}
        onSelectScan={setScanFilter}
        activeScanId={scanFilter}
      />
      <PullRequests pullRequests={pullRequests} />
    </main>
  );
}
