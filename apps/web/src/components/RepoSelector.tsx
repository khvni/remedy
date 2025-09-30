import type { Repo } from '../api';

interface Props {
  repos: Repo[];
  selectedId: string | null;
  onChange: (repoId: string | null) => void;
  onRefresh: () => void;
}

export function RepoSelector({ repos, selectedId, onChange, onRefresh }: Props) {
  return (
    <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
      <label htmlFor="repo-select" style={{ fontWeight: 600 }}>
        Repository
      </label>
      <select
        id="repo-select"
        value={selectedId ?? ''}
        onChange={(event) => onChange(event.target.value || null)}
      >
        <option value="">All</option>
        {repos.map((repo) => (
          <option key={repo.id} value={repo.id}>
            {repo.name}
          </option>
        ))}
      </select>
      <button type="button" onClick={onRefresh}>
        Refresh
      </button>
    </div>
  );
}
