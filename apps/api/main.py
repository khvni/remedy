from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import health, repos, scans, prs, findings, webhook

app = FastAPI(title="Remedy API", version="0.1.0")


def _load_allowed_origins() -> List[str]:
    raw_origins = os.getenv("REM_CORS_ORIGINS")
    if not raw_origins:
        # Default to local dev dashboard; callers can override via REM_CORS_ORIGINS env var
        return ["http://localhost:5173", "http://127.0.0.1:5173"]
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_load_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(repos.router, prefix="/repos", tags=["repos"])
app.include_router(scans.router, prefix="/scans", tags=["scans"])
app.include_router(prs.router, prefix="/prs", tags=["prs"])
app.include_router(findings.router, prefix="/findings", tags=["findings"])
app.include_router(webhook.router, prefix="/webhooks", tags=["webhooks"])
