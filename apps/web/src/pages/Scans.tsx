import type { Finding, Scan } from '../api';

interface Props {
  scans: Scan[];
  findings: Finding[];
  onSelectScan: (scanId: string | null) => void;
  activeScanId: string | null;
}

export function Scans({ scans, findings, onSelectScan, activeScanId }: Props) {
  return (
    <section>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Scans</h2>
        <div>
          <label htmlFor="scan-select" style={{ fontWeight: 600, marginRight: '0.5rem' }}>
            Focus scan
          </label>
          <select
            id="scan-select"
            value={activeScanId ?? ''}
            onChange={(event) => onSelectScan(event.target.value || null)}
          >
            <option value="">All</option>
            {scans.map((scan) => (
              <option key={scan.id} value={scan.id}>
                {scan.kind.toUpperCase()} · {new Date(scan.created_at).toLocaleString()}
              </option>
            ))}
          </select>
        </div>
      </header>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Kind</th>
            <th>Status</th>
            <th>Started</th>
          </tr>
        </thead>
        <tbody>
          {scans.map((scan) => (
            <tr key={scan.id}>
              <td>{scan.id.split('-')[0]}</td>
              <td>{scan.kind.toUpperCase()}</td>
              <td>{scan.status}</td>
              <td>{new Date(scan.created_at).toLocaleString()}</td>
            </tr>
          ))}
          {scans.length === 0 && (
            <tr>
              <td colSpan={4} style={{ textAlign: 'center', padding: '1rem' }}>
                No scans yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
      <h3 style={{ marginTop: '1.5rem' }}>Findings</h3>
      <table>
        <thead>
          <tr>
            <th>Severity</th>
            <th>Path</th>
            <th>Rule</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((finding) => (
            <tr key={finding.id}>
              <td>{finding.severity}</td>
              <td>{finding.path}</td>
              <td>{finding.rule_id ?? '—'}</td>
              <td>{finding.description ?? '—'}</td>
            </tr>
          ))}
          {findings.length === 0 && (
            <tr>
              <td colSpan={4} style={{ textAlign: 'center', padding: '1rem' }}>
                No findings for the current filter.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
