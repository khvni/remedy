from __future__ import annotations

from fastapi import FastAPI

from .routes import health, repos, scans, prs, findings, webhook

app = FastAPI(title="Remedy API", version="0.1.0")
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(repos.router, prefix="/repos", tags=["repos"])
app.include_router(scans.router, prefix="/scans", tags=["scans"])
app.include_router(prs.router, prefix="/prs", tags=["prs"])
app.include_router(findings.router, prefix="/findings", tags=["findings"])
app.include_router(webhook.router, prefix="/webhooks", tags=["webhooks"])
