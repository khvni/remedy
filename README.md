# Remedy

Remedy is a Python-first, AI-augmented security remediation service. It runs SAST and SCA scanners on GitHub repositories, prioritises findings with Gemini, synthesises minimal patches, and opens pull requests via a GitHub App integration. This repository contains the FastAPI backend, RQ worker, scanner integrations, and a lightweight React dashboard for demoing the end-to-end flow.

## Architecture Overview

Remedy follows a service + worker model:

- **FastAPI (`apps/api`)** exposes REST endpoints for repositories, scans, findings, PRs, and GitHub webhooks. It persists state in Postgres via SQLAlchemy models and enqueues work on Redis/RQ.
- **Worker (`apps/worker`)** executes queued jobs. Each job clones the target repo, runs Semgrep and dependency scanners (OSV, Syft, Grype), calls Gemini for prioritisation and patch planning, applies guarded edits, commits to a topic branch, and (optionally) pushes + opens a PR through the GitHub App credentials.
- **React dashboard (`apps/web`)** presents a single-page UI that lists repos, scans, findings, and Remedy-authored PRs by consuming the API endpoints.
- **Scanners (`scanners/`)** holds the Semgrep profiles/rules and configuration placeholders for OSV and Grype. These can be customised per deployment.
- **Infrastructure (`infra/`)** offers Dockerfiles, a Docker Compose stack for local development, and Alembic migrations.

### Data Flow

1. A repository is registered via `POST /repos` or a GitHub webhook (`/webhooks/github`).
2. `POST /scans` (or webhook) enqueues `apps.worker.tasks.run_scan` with the repo & scan kind.
3. The worker clones the repo to a temp dir, runs Semgrep (SAST) and OSV/Syft/Grype (SCA), and stores raw findings.
4. Findings are enriched with IDs and passed to the Gemini prompts for prioritisation + patch planning.
5. Generated edits are applied via `patch_apply`, committed, and pushed using GitHub App credentials; a PR is opened if the push succeeds.
6. Scan, finding, and PR metadata is persisted to Postgres for API and UI consumption.

## Repository Layout

| Path | Description |
|------|-------------|
| `apps/api/` | FastAPI app (routers, schemas, services, SQLAlchemy models). |
| `apps/worker/` | RQ worker, scanner adapters, Gemini orchestrator, git/patch tooling. |
| `apps/web/` | React (Vite) dashboard. |
| `scanners/` | Semgrep rule packs and SCA configs. |
| `infra/` | Dockerfiles, Docker Compose config, Alembic migrations. |
| `scripts/` | Helper shell scripts for running scanners manually. |
| `tests/` | Pytest suite covering API, worker, and integration smoke flows. |
| `cli/remedy.py` | Typer CLI for quick local scans (without the API). |

Refer to the README within each directory for architecture, testing, and deployment notes specific to that component.

## Requirements

- Python 3.11+ (API + worker)
- Node 20 (React dashboard)
- Docker + Docker Compose (optional but simplifies local provisioning)
- External binaries (installed on worker hosts or baked into the image): `git`, `semgrep`, `osv-scanner`, `syft`, `grype`
- Gemini API key with access to `gemini-2.5-pro`
- GitHub App configured with the permissions noted below

## Environment Configuration

Create a `.env` at the repository root (see `.env.example`) including:

```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/remedy
REDIS_URL=redis://localhost:6379/0
GITHUB_APP_ID=...
GITHUB_INSTALLATION_ID=...
GITHUB_PRIVATE_KEY=... # base64-encoded PEM
GITHUB_WEBHOOK_SECRET=...
GEMINI_API_KEY=...
GIT_AUTHOR_NAME=Remedy Bot
GIT_AUTHOR_EMAIL=remedy@example.com
VITE_API_BASE_URL=http://localhost:8000
```

For the React app, `apps/web/.env` can override `VITE_API_BASE_URL`.

### GitHub App Credentials

Grant the GitHub App `Contents: Read & write`, `Pull requests: Read & write`, and `Metadata: Read` permissions. After installing it on the target repo/org, capture:

- **App ID** from Developer Settings → GitHub Apps
- **Installation ID** from the installation URL (`.../installations/<id>`)
- **Private key**: download the PEM, encode it with `base64 -w0 app.pem`
- **Webhook secret**: set the same value in the App configuration and `.env`

Remedy will generate a JWT, fetch an installation access token, push branches via HTTPS (`x-access-token:<token>`) and open PRs through the GitHub REST API.

## Local Development

### Option A: Docker Compose

```bash
cp .env.example .env
make up            # starts api, worker, db, redis, web
make migrate       # apply Alembic migrations
```

The API becomes available at `http://localhost:8000`, the dashboard at `http://localhost:5173`.

### Option B: Native

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[test]
uvicorn apps.api.main:app --reload
# separate shell
python apps/worker/worker.py

cd apps/web
npm install
npm run dev -- --host
```

If you want GitHub webhooks while developing locally, run `ngrok http 8000` and configure the GitHub App webhook URL as `https://<ngrok-host>/webhooks/github`.

## Testing

The repository ships with pytest-based unit and integration coverage. Execute:

```bash
pip install -e .[test]
python3 -m pytest
```

The tests stand up an in-memory SQLite database, replace the Redis queue with a stub, and monkeypatch the worker pipeline to avoid network calls. They validate API CRUD responses, worker persistence, and the scan-to-PR happy path.

## Deployment Considerations

- **Database**: use managed Postgres or provision your own. Run Alembic migrations at deploy time (`make migrate`).
- **Redis**: required for RQ workers. Configure `REDIS_URL` accordingly.
- **Scanners**: ensure binaries exist in the worker runtime. Consider container images with the CLI tools pre-installed.
- **Secrets**: store `GEMINI_API_KEY`, GitHub credentials, and webhook secret in your secret manager (AWS SSM, Vault, etc.).
- **Webhooks**: expose `/webhooks/github` over HTTPS (TLS termination via load balancer/ingress). The handler validates `X-Hub-Signature-256` using `GITHUB_WEBHOOK_SECRET`.
- **Scaling**: run multiple RQ workers for throughput; add observability (logs/metrics) and timeouts around scanner execution.
- **Security**: sandbox scanner execution if possible (containers with limited permissions), and audit generated patches before pushing to production repos.

## Demo Checklist

1. Ensure `.env` contains valid Postgres/Redis URIs, Gemini key, GitHub App credentials, and webhook secret.
2. Start services (`make up` or manual processes) and run `make migrate`.
3. Expose the API via ngrok (`ngrok http 8000`) and set the GitHub App webhook URL accordingly.
4. Register a test repo (`POST /repos` or via the dashboard) and trigger a scan (`POST /scans`).
5. Monitor worker logs; once complete, view findings and PRs in the dashboard.
6. Confirm a branch + PR were created in GitHub.

The README files within `apps/api`, `apps/worker`, `apps/web`, and `infra` provide component-level testing/deployment notes.
