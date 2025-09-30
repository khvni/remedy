# Remedy API

## Purpose
FastAPI application that exposes REST endpoints for repository registration, scan orchestration, findings, pull requests, and GitHub webhook ingestion. It persists data in Postgres via SQLAlchemy models and coordinates with Redis/RQ to enqueue worker jobs.

## Architecture Decisions
- **Thin routers, transactional services**: routers (`apps/api/routes/*.py`) validate inputs and delegate to service modules (`apps/api/services`). Services own DB session use and enforce simple domain rules (e.g., repo existence before enqueuing scans).
- **Session dependency**: `apps/api/deps.py` exposes `get_db()` so every request receives an independent SQLAlchemy session.
- **Schema-first responses**: Pydantic models under `apps/api/schemas` document each endpoint and map ORM objects to response payloads.
- **Webhook verification**: `/webhooks/github` validates `X-Hub-Signature-256` using `GITHUB_WEBHOOK_SECRET` before dispatching to the scan service.

## Key Files
- `main.py` — FastAPI app initialiser, registers routers.
- `routes/` — API surface (`repos`, `scans`, `findings`, `prs`, `webhooks`).
- `services/` — business logic; interacts with the database and Redis queue.
- `models/` — SQLAlchemy declarative models & session factory.
- `schemas/` — Pydantic request/response definitions.

## Testing
- Run the full suite from the repository root: `python3 -m pytest tests/test_api.py`.
- For route-specific manual testing, start the API (`uvicorn apps.api.main:app --reload`) and use `httpie`/`curl` against `http://localhost:8000`.

## Deployment Notes
- Requires `DATABASE_URL`, `REDIS_URL`, and GitHub/Gemini secrets from the root `.env`.
- Behind TLS/ingress, ensure `/webhooks/github` receives raw bodies (no transformations) for signature validation.
- Use Alembic migrations stored under `infra/migrations` to manage schema (`make migrate`).
