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

The API becomes available at `http://localhost:8002`, the dashboard at `http://localhost:5175`.

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

## Testing & Demo Guide

### Quick Start Testing

1. **Ensure environment is configured:**
   ```bash
   # Check .env contains valid credentials
   cat .env | grep -E "(GITHUB_APP_ID|GEMINI_API_KEY|DATABASE_URL|REDIS_URL)"
   ```

2. **Start the full stack:**
   ```bash
   make up            # starts api, worker, db, redis, web
   make migrate       # apply Alembic migrations
   ```

3. **Verify services are running:**
   ```bash
   # Check API health
   curl http://localhost:8002/health
   # Should return: {"ok":true}
   
   # Check web dashboard
   open http://localhost:5175
   ```

### Testing with Your Repository

#### Option 1: Web Dashboard (Recommended)

1. **Open the dashboard:** `http://localhost:5175`
2. **Register your repository:**
   - Click "Add Repository"
   - Enter: `https://github.com/khvni/juice-shop`
   - Click "Register"
3. **Trigger a scan:**
   - Find your repository in the list
   - Click "Scan" button
   - Select scan types: "SAST" (Semgrep) and "SCA" (OSV + Grype)
   - Click "Start Scan"
4. **Monitor progress:**
   - Watch the "Scans" tab for status updates
   - Check "Findings" tab for discovered vulnerabilities
   - Look for "Pull Requests" tab for auto-generated fixes

#### Option 2: API Direct Testing

1. **Register repository:**
   ```bash
   curl -X POST http://localhost:8002/repos \
     -H "Content-Type: application/json" \
     -d '{"url": "https://github.com/khvni/juice-shop"}'
   ```

2. **Trigger scan:**
   ```bash
   # Get the repo_id from the response above
   curl -X POST http://localhost:8002/scans \
     -H "Content-Type: application/json" \
     -d '{"repo_id": "REPO_ID_HERE", "kinds": ["sast", "sca"]}'
   ```

3. **Check results:**
   ```bash
   # List scans
   curl http://localhost:8002/scans?repo_id=REPO_ID_HERE
   
   # List findings
   curl http://localhost:8002/findings?repo_id=REPO_ID_HERE
   
   # List PRs
   curl http://localhost:8002/prs?repo_id=REPO_ID_HERE
   ```

#### Option 3: CLI Testing (Quick Scan)

```bash
# Quick scan without full stack
python cli/remedy.py scan https://github.com/khvni/juice-shop
```

### What to Expect

#### SAST Scan (Semgrep)
- **Finds:** Code vulnerabilities, security anti-patterns, hardcoded secrets
- **Example findings:** SQL injection, XSS, insecure random, hardcoded passwords
- **Time:** 1-3 minutes depending on repo size

#### SCA Scan (OSV + Grype)
- **Finds:** Vulnerable dependencies, outdated packages, known CVEs
- **Example findings:** CVE-2023-1234 in express@4.17.1, vulnerable lodash version
- **Time:** 2-5 minutes depending on dependency count

#### AI Processing (Gemini)
- **Prioritizes:** Findings by severity and exploitability
- **Plans:** Minimal patches to fix vulnerabilities
- **Creates:** Pull requests with automated fixes

### Monitoring & Debugging

#### Check Worker Logs
```bash
# View worker container logs
docker compose -f infra/compose.yaml logs -f worker

# Look for:
# - "Worker started" - worker is running
# - "Running Semgrep..." - SAST scan started
# - "Running OSV..." - SCA scan started
# - "Creating branch..." - PR creation started
```

#### Check API Logs
```bash
# View API container logs
docker compose -f infra/compose.yaml logs -f api

# Look for:
# - "Repository registered" - repo added successfully
# - "Scan queued" - scan job created
# - "Findings stored" - results saved
```

#### Common Issues & Solutions

1. **"Repository not found" error:**
   - Ensure the GitHub App is installed on the target repository
   - Check `GITHUB_APP_ID` and `GITHUB_INSTALLATION_ID` in `.env`

2. **"Scanner not found" error:**
   - Verify scanner binaries are installed in the worker container
   - Check worker logs for missing dependencies

3. **"Gemini API error":**
   - Verify `GEMINI_API_KEY` is valid and has quota
   - Check API logs for authentication errors

4. **"Database connection failed":**
   - Ensure PostgreSQL is running: `docker compose -f infra/compose.yaml ps`
   - Check `DATABASE_URL` in `.env`

5. **"Redis connection failed":**
   - Ensure Redis is running: `docker compose -f infra/compose.yaml ps`
   - Check `REDIS_URL` in `.env`

### Expected Results for Juice Shop

The OWASP Juice Shop is a deliberately vulnerable application, so you should see:

#### SAST Findings (Semgrep):
- SQL injection vulnerabilities
- XSS vulnerabilities
- Insecure random number generation
- Hardcoded secrets
- Authentication bypasses

#### SCA Findings (OSV + Grype):
- Vulnerable npm packages
- Outdated dependencies
- Known CVEs in dependencies

#### AI-Generated Fixes:
- Patches for SQL injection (parameterized queries)
- XSS prevention (input sanitization)
- Secure random number generation
- Dependency updates

### Performance Expectations

- **Small repo (< 100 files):** 2-5 minutes total
- **Medium repo (100-1000 files):** 5-15 minutes total
- **Large repo (> 1000 files):** 15-30 minutes total

### Next Steps After Testing

1. **Review findings** in the dashboard
2. **Check generated PRs** in your GitHub repository
3. **Test the fixes** by reviewing the proposed changes
4. **Monitor webhook integration** (if configured)
5. **Scale up** by adding more repositories

## Demo Checklist

1. Ensure `.env` contains valid Postgres/Redis URIs, Gemini key, GitHub App credentials, and webhook secret.
2. Start services (`make up` or manual processes) and run `make migrate`.
3. Expose the API via ngrok (`ngrok http 8000`) and set the GitHub App webhook URL accordingly.
4. Register a test repo (`POST /repos` or via the dashboard) and trigger a scan (`POST /scans`).
5. Monitor worker logs; once complete, view findings and PRs in the dashboard.
6. Confirm a branch + PR were created in GitHub.

The README files within `apps/api`, `apps/worker`, `apps/web`, and `infra` provide component-level testing/deployment notes.
