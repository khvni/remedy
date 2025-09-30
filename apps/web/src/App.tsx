import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  fetchFindings,
  fetchPullRequests,
  fetchRepos,
  fetchScans,
  registerRepo,
  triggerScan,
  type Finding,
  type PullRequest,
  type Repo,
  type Scan,
} from './api';

const REFRESH_INTERVAL_MS = 15000;

function formatRelativeTime(date: Date | null): string {
  if (!date) return 'never';
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function getSeverityLabel(severity: string): string {
  const normalized = severity.toLowerCase();
  return ['critical', 'high', 'medium', 'low'].includes(normalized) ? normalized : 'info';
}

export default function App() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [scans, setScans] = useState<Scan[]>([]);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([]);
  const [selectedRepoId, setSelectedRepoId] = useState<string | null>(null);
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [repoUrlInput, setRepoUrlInput] = useState('');
  const [repoActionMessage, setRepoActionMessage] = useState<string | null>(null);
  const [isRegisteringRepo, setIsRegisteringRepo] = useState(false);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);
  const [notification, setNotification] = useState<{ message: string; url?: string } | null>(null);

  const prIdsRef = useRef<Set<string>>(new Set());
  const audioContextRef = useRef<AudioContext | null>(null);
  const hasBootstrappedPrsRef = useRef(false);

  const playPing = useCallback(async () => {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContextClass) return;
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContextClass();
      }
      const ctx = audioContextRef.current;
      if (ctx.state === 'suspended') {
        await ctx.resume();
      }
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();
      oscillator.type = 'triangle';
      oscillator.frequency.value = 880;
      oscillator.connect(gain);
      gain.connect(ctx.destination);
      const now = ctx.currentTime;
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.3, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);
      oscillator.start(now);
      oscillator.stop(now + 0.4);
    } catch (err) {
      console.warn('Unable to play PR notification ping', err);
    }
  }, []);

  const loadData = useCallback(
    async ({ silent = false, repoOverride, scanOverride }: { silent?: boolean; repoOverride?: string | null; scanOverride?: string | null } = {}) => {
      if (!silent) {
        setLoading(true);
      }
      const repoIdToUse = repoOverride ?? selectedRepoId;
      const scanIdToUse = scanOverride ?? selectedScanId;
      try {
        const [repoPayload, scanList, findingList, prList] = await Promise.all([
          fetchRepos(),
          fetchScans(repoIdToUse ?? undefined),
          fetchFindings(repoIdToUse ?? undefined, scanIdToUse ?? undefined),
          fetchPullRequests(repoIdToUse ?? undefined),
        ]);
        setRepos(repoPayload.items);
        setScans(scanList);
        setFindings(findingList);

        const nextPrIds = new Set(prList.map((pr) => pr.id));
        const previousIds = prIdsRef.current;
        const newlyCreated = prList.find((pr) => !previousIds.has(pr.id));
        prIdsRef.current = nextPrIds;
        setPullRequests(prList);

        if (hasBootstrappedPrsRef.current && newlyCreated) {
          setNotification({
            message: `Remedy opened ${newlyCreated.branch}`,
            url: newlyCreated.pr_url ?? undefined,
          });
          void playPing();
        }

        if (!hasBootstrappedPrsRef.current) {
          hasBootstrappedPrsRef.current = true;
        }

        setError(null);
        setLastRefreshedAt(new Date());
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unable to load dashboard data';
        setError(message);
        if (!silent) {
          setRepos([]);
          setScans([]);
          setFindings([]);
          setPullRequests([]);
        }
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [playPing, selectedRepoId, selectedScanId],
  );

  useEffect(() => {
    void loadData();
  }, [loadData]);

  useEffect(() => {
    const intervalId = window.setInterval(() => {
      void loadData({ silent: true });
    }, REFRESH_INTERVAL_MS);
    return () => window.clearInterval(intervalId);
  }, [loadData]);

  useEffect(() => {
    if (!notification) return;
    const timeoutId = window.setTimeout(() => setNotification(null), 6000);
    return () => window.clearTimeout(timeoutId);
  }, [notification]);

  const handleRepoSelect = (value: string) => {
    const nextValue = value || null;
    setSelectedRepoId(nextValue);
    setSelectedScanId(null);
    void loadData({ repoOverride: nextValue, scanOverride: null });
  };

  const handleScanSelect = (value: string) => {
    const nextValue = value || null;
    setSelectedScanId(nextValue);
    void loadData({ scanOverride: nextValue });
  };

  const handleRepoRegistration = async () => {
    const trimmed = repoUrlInput.trim();
    if (!trimmed) {
      setRepoActionMessage('Please provide a repository URL.');
      return;
    }
    setRepoActionMessage(null);
    setIsRegisteringRepo(true);
    try {
      const repo = await registerRepo(trimmed);
      setRepoActionMessage(`Registered ${repo.name}. Queuing scan…`);
      setRepoUrlInput('');
      setSelectedRepoId(repo.id);
      setSelectedScanId(null);
      await triggerScan(repo.id);
      setRepoActionMessage(`SAST + SCA scan queued for ${repo.name}.`);
      await loadData({ silent: true, repoOverride: repo.id, scanOverride: null });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to register repository';
      setRepoActionMessage(message);
    } finally {
      setIsRegisteringRepo(false);
    }
  };

  const handleScanTrigger = async () => {
    if (!selectedRepoId) {
      setRepoActionMessage('Select a repository to start a scan.');
      return;
    }
    setRepoActionMessage('Queueing scan…');
    try {
      const response = await triggerScan(selectedRepoId);
      setRepoActionMessage(`Scan queued (${response.queued_jobs.length} job${response.queued_jobs.length === 1 ? '' : 's'}).`);
      await loadData({ silent: true });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unable to queue scan';
      setRepoActionMessage(message);
    }
  };

  const selectedRepo = selectedRepoId ? repos.find((repo) => repo.id === selectedRepoId) ?? null : null;
  const activeScans = scans.filter((scan) => scan.status !== 'completed' && scan.status !== 'failed');
  const totalFindings = findings.length;
  const totalOpenPrs = pullRequests.filter((pr) => pr.status !== 'merged' && pr.status !== 'closed').length;

  const scansByRepo = useMemo(() => {
    if (!selectedRepoId) return scans;
    return scans.filter((scan) => scan.repo_id === selectedRepoId);
  }, [scans, selectedRepoId]);

  return (
    <main className="dashboard">
      <div className="hero">
        <div>
          <h1>Remedy Operations Center</h1>
          <p className="hero__subtitle">
            Orchestrate scans, monitor AI remediation, and showcase automated pull requests in real time.
          </p>
        </div>
        <div className="hero__meta">
          <span className="hero__meta-label">Last refresh</span>
          <span className="hero__meta-value">{formatRelativeTime(lastRefreshedAt)}</span>
          <button type="button" className="button button--ghost" onClick={() => void loadData()}>
            Refresh now
          </button>
        </div>
      </div>

      <section className="grid grid--metrics">
        <div className="metric-card">
          <span className="metric-card__label">Registered repositories</span>
          <strong className="metric-card__value">{repos.length}</strong>
          <span className="metric-card__hint">{selectedRepo ? selectedRepo.name : 'All workspaces'}</span>
        </div>
        <div className="metric-card">
          <span className="metric-card__label">Active scans</span>
          <strong className="metric-card__value">{activeScans.length}</strong>
          <span className="metric-card__hint">{scans.length} total runs</span>
        </div>
        <div className="metric-card">
          <span className="metric-card__label">Findings prioritised</span>
          <strong className="metric-card__value">{totalFindings}</strong>
          <span className="metric-card__hint">Scope: {selectedScanId ? 'Focused scan' : 'Latest data'}</span>
        </div>
        <div className="metric-card">
          <span className="metric-card__label">Remedy PRs</span>
          <strong className="metric-card__value">{pullRequests.length}</strong>
          <span className="metric-card__hint">{totalOpenPrs} open for review</span>
        </div>
      </section>

      <section className="card">
        <header className="card__header">
          <div>
            <h2>Repository onboarding</h2>
            <p className="card__subtitle">Drop in any public or connected GitHub repository and let Remedy take it from there.</p>
          </div>
        </header>
        <div className="repo-form">
          <input
            type="url"
            placeholder="https://github.com/organization/project"
            value={repoUrlInput}
            onChange={(event) => setRepoUrlInput(event.target.value)}
            className="repo-form__input"
            aria-label="Repository URL"
          />
          <button
            type="button"
            className="button button--primary"
            onClick={() => void handleRepoRegistration()}
            disabled={isRegisteringRepo}
          >
            {isRegisteringRepo ? 'Starting…' : 'Add & Scan'}
          </button>
        </div>
        <div className="repo-controls">
          <label htmlFor="repo-filter" className="repo-controls__label">
            Focus repository
          </label>
          <select
            id="repo-filter"
            value={selectedRepoId ?? ''}
            onChange={(event) => handleRepoSelect(event.target.value)}
            className="repo-controls__select"
          >
            <option value="">All repositories</option>
            {repos.map((repo) => (
              <option key={repo.id} value={repo.id}>
                {repo.name}
              </option>
            ))}
          </select>
          <button type="button" className="button button--secondary" onClick={() => void handleScanTrigger()}>
            Start new scan
          </button>
          {repoActionMessage && <span className="repo-controls__message">{repoActionMessage}</span>}
        </div>
      </section>

      <section className="grid grid--two">
        <div className="card">
          <header className="card__header card__header--with-select">
            <div>
              <h2>Scan timeline</h2>
              <p className="card__subtitle">Monitor pipeline execution across SAST + SCA scanners.</p>
            </div>
            <select
              value={selectedScanId ?? ''}
              onChange={(event) => handleScanSelect(event.target.value)}
              className="card__select"
            >
              <option value="">Latest scans</option>
              {scansByRepo.map((scan) => (
                <option key={scan.id} value={scan.id}>
                  {scan.kind.toUpperCase()} · {new Date(scan.created_at).toLocaleString()}
                </option>
              ))}
            </select>
          </header>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Scan</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Started</th>
                </tr>
              </thead>
              <tbody>
                {scansByRepo.map((scan) => (
                  <tr key={scan.id} className={scan.id === selectedScanId ? 'row--active' : undefined}>
                    <td>{scan.id.slice(0, 8)}</td>
                    <td>{scan.kind.toUpperCase()}</td>
                    <td>
                      <span className={`status-chip status-chip--${scan.status.toLowerCase()}`}>
                        {scan.status}
                      </span>
                    </td>
                    <td>{new Date(scan.created_at).toLocaleString()}</td>
                  </tr>
                ))}
                {scansByRepo.length === 0 && (
                  <tr>
                    <td colSpan={4} className="table-empty">
                      No scans yet. Kick one off to showcase the workflow.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <header className="card__header">
            <div>
              <h2>AI findings triage</h2>
              <p className="card__subtitle">Highest impact issues from the selected scope.</p>
            </div>
          </header>
          <div className="finding-list">
            {findings.map((finding) => (
              <article key={finding.id} className="finding">
                <div className={`chip chip--${getSeverityLabel(finding.severity)}`}>
                  {finding.severity.toUpperCase()}
                </div>
                <div>
                  <h3 className="finding__path">{finding.path}</h3>
                  <p className="finding__description">{finding.description ?? 'Remedy prioritised this issue for review.'}</p>
                  <dl className="finding__meta">
                    <div>
                      <dt>Rule</dt>
                      <dd>{finding.rule_id ?? '—'}</dd>
                    </div>
                    <div>
                      <dt>Line</dt>
                      <dd>{finding.line ?? '—'}</dd>
                    </div>
                  </dl>
                </div>
              </article>
            ))}
            {findings.length === 0 && (
              <div className="empty-state">No findings yet—queue a scan or adjust the filters.</div>
            )}
          </div>
        </div>
      </section>

      <section className="card">
        <header className="card__header">
          <div>
            <h2>Automated pull requests</h2>
            <p className="card__subtitle">Track Remedy-authored remediation branches and PR status.</p>
          </div>
        </header>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Branch</th>
                <th>Status</th>
                <th>Summary</th>
                <th>Link</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {pullRequests.map((pr) => (
                <tr key={pr.id}>
                  <td>{pr.branch}</td>
                  <td>
                    <span className={`status-chip status-chip--${pr.status.toLowerCase()}`}>
                      {pr.status}
                    </span>
                  </td>
                  <td>{pr.summary ?? 'Remedy automated fix'}</td>
                  <td>
                    {pr.pr_url ? (
                      <a href={pr.pr_url} target="_blank" rel="noreferrer" className="link">
                        View PR
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td>{new Date(pr.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {pullRequests.length === 0 && (
                <tr>
                  <td colSpan={5} className="table-empty">
                    Remedy has not created any pull requests yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {error && (
        <div className="banner banner--error">
          <strong>Failed to load data:</strong> {error}
        </div>
      )}

      {loading && (
        <div className="banner banner--info">Loading latest scan data…</div>
      )}

      {notification && (
        <div className="toast">
          <div className="toast__indicator" aria-hidden="true" />
          <div>
            <strong>New remediation shipped</strong>
            <p>{notification.message}</p>
            {notification.url && (
              <a className="link" href={notification.url} target="_blank" rel="noreferrer">
                Open pull request
              </a>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
