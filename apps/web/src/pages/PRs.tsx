import type { PullRequest } from '../api';

interface Props {
  pullRequests: PullRequest[];
}

export function PullRequests({ pullRequests }: Props) {
  return (
    <section>
      <h2>Pull Requests</h2>
      <table>
        <thead>
          <tr>
            <th>Branch</th>
            <th>Status</th>
            <th>Summary</th>
            <th>Link</th>
          </tr>
        </thead>
        <tbody>
          {pullRequests.map((pr) => (
            <tr key={pr.id}>
              <td>{pr.branch}</td>
              <td>{pr.status}</td>
              <td>{pr.summary ?? '—'}</td>
              <td>
                {pr.pr_url ? (
                  <a href={pr.pr_url} target="_blank" rel="noreferrer">
                    View PR
                  </a>
                ) : (
                  '—'
                )}
              </td>
            </tr>
          ))}
          {pullRequests.length === 0 && (
            <tr>
              <td colSpan={4} style={{ textAlign: 'center', padding: '1rem' }}>
                No pull requests yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
