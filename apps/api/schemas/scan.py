from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    repo_id: str
    kinds: list[str] = Field(default_factory=lambda: ["sast", "sca"], min_length=1)


class ScanQueuedResponse(BaseModel):
    repo_id: str
    queued_jobs: list[str]


class ScanListItem(BaseModel):
    id: str
    repo_id: str
    kind: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ScanDetail(ScanListItem):
    findings_json: Optional[Any] = None
