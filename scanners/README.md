# Scanners Configuration

## Purpose
Holds Semgrep rulesets and configuration files for the SAST + SCA tools invoked by the worker.

## Layout
- `semgrep/profiles.yml` — primary ruleset aggregation loaded by the Semgrep runner.
- `semgrep/rules/*.yml` — curated Semgrep rules for secrets, input validation, and basic authZ checks.
- `osv/` — placeholder `config.toml` for OSV scanner allow/deny lists.
- `grype/` — placeholder `config.yaml` for Grype severity filtering.

## Customisation
- Add or tweak Semgrep rules to tune signal/noise for your target applications.
- Supply OSV/Grype configs to ignore known issues or restrict severities.
- Ensure worker containers include the rule directories and configs at the expected paths (`scanners/...`).

## Testing
- Run Semgrep manually: `scripts/run_semgrep.sh` (from repo root).
- Run OSV: `scripts/run_osv.sh /path/to/repo`.
- Run Syft/Grype: `scripts/run_syft_grype.sh /path/to/repo`.

## Deployment Notes
- Keep the `scanners/` directory in sync across API/worker nodes (bind-mount in Docker, bake into images, or store in object storage).
- Monitor scanner runtimes; adjust `SEMGREP_TIMEOUT` or prune rules for large monorepos.
