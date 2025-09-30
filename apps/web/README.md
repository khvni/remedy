# Remedy Web Dashboard

## Purpose
Vite + React single-page application that surfaces repositories, scans, findings, and Remedy-authored pull requests by calling the FastAPI backend.

## Architecture Decisions
- **API-first**: all data flows through `src/api.ts`, making it easy to swap API hosts via `VITE_API_BASE_URL`.
- **Client-side filtering**: scan/finding filtering is performed in-memory for MVP simplicity; the API already supports repo/scan query parameters if pagination is added later.
- **Simple component hierarchy**: `App.tsx` orchestrates state; `RepoSelector`, `Scans`, and `PullRequests` components focus on presentation.

## Key Files
- `src/api.ts` — typed fetch helpers for REST endpoints.
- `src/App.tsx` — main page combining selectors and tables.
- `src/pages/Scans.tsx`, `src/pages/PRs.tsx` — view components.
- `vite.config.ts`, `tsconfig.json` — build tooling.

## Development
```bash
cd apps/web
npm install
npm run dev -- --host --port 5173
```
Visit `http://localhost:5173` (or the port forwarded via Docker Compose). Ensure the API is reachable at the URL configured in `.env` or `VITE_API_BASE_URL`.

## Testing
- Add React Testing Library or Cypress as needed; currently smoke-tested manually by exercising API endpoints.

## Deployment Notes
- For production, run `npm run build` to generate static assets in `dist/` and host them behind a CDN or reverse proxy.
- Docker support (`infra/docker/web.Dockerfile`) runs the Vite dev server for MVP demos; adjust to serve the built assets for production.
