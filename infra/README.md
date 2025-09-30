# Infrastructure

## Purpose
Containerisation artefacts and database migrations for running Remedy locally or in a demo environment.

## Components
- `docker/` — Dockerfiles for API (`api.Dockerfile`), worker (`worker.Dockerfile`), and web UI (`web.Dockerfile`).
- `compose.yaml` — Docker Compose stack standing up API, worker, Postgres, Redis, and the web dashboard.
- `alembic.ini` & `migrations/` — Alembic setup + initial schema migration (`versions/0001_init.py`).

## Architecture Decisions
- **Editable mounts for dev**: Compose mounts the repo into containers so code changes reload automatically.
- **Shared `.env`**: Compose services read environment variables from the root `.env` file for consistency.
- **Separate containers**: API and worker run in distinct containers, mirroring production separation of concerns.

## Usage
```bash
make up           # build + start containers
make down         # stop and remove containers
make migrate      # apply Alembic migrations against DATABASE_URL
```

## Deployment Notes
- For production, adapt these Dockerfiles to pin dependency versions, pre-install scanner binaries, and use multi-stage builds for minimal runtime images.
- Replace the in-repo Postgres/Redis with managed services; update `DATABASE_URL`/`REDIS_URL` accordingly.
- Configure logging and health checks (e.g., Postgres readiness) before deploying to orchestrators like ECS or Kubernetes.
