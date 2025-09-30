# Remedy Worker

## Purpose
Executes asynchronous scan jobs queued by the API. Each job clones repositories, runs security scanners, delegates prioritisation and patch planning to Gemini, applies edits safely, and coordinates GitHub branch/PR automation.

## Architecture Decisions
- **RQ + Redis**: lightweight queuing fits the MVP, with `apps/worker/worker.py` running a simple RQ worker listening on the `remedy` queue.
- **Modular tooling**: scanner integrations live under `tools/` (Semgrep, OSV, Syft, Grype) so they can evolve independently. `patch_apply.py` constrains code edits to literal/regex replacements for MVP safety.
- **Agent orchestration**: `agent/orchestrator.py` renders Jinja prompts for Gemini, capturing prioritised findings and patch plans.
- **GitHub App integration**: `tools/git_tool.py` commits fixes, pushes to GitHub via installation tokens, and opens PRs using the REST API (credentials from environment variables).

## Key Files
- `tasks.py` — main entry point for `run_scan` jobs; orchestrates scanning, planning, patching, and persistence.
- `agent/` — Gemini prompts, provider wrapper, and orchestration logic.
- `tools/` — scanner runners, git helpers, patch applier, GitHub App client.
- `worker.py` — RQ worker bootstrap.

## Testing
- Run worker-focused tests: `python3 -m pytest tests/test_worker.py tests/test_integration_smoke.py`.
- To simulate a queue job manually: `python -m apps.worker.tasks run_scan <repo_id> sast` (note: requires proper env and DB entries).

## Deployment Notes
- Ensure the worker environment has scanner binaries (`semgrep`, `osv-scanner`, `syft`, `grype`) and git installed.
- Provide access to Postgres (`DATABASE_URL`) and Redis (`REDIS_URL`).
- Set GitHub/Gemini secrets: `GITHUB_APP_ID`, `GITHUB_INSTALLATION_ID`, `GITHUB_PRIVATE_KEY`, `GITHUB_WEBHOOK_SECRET`, `GEMINI_API_KEY`.
- For production, consider containerising the worker with scanners baked in, add execution timeouts, and run multiple worker replicas for concurrency.
