from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RepoCreate(BaseModel):
    url: str = Field(..., description="Git repository URL (https or ssh)")


class RepoOut(BaseModel):
    id: str
    name: str
    url: str
    default_branch: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RepoListOut(BaseModel):
    items: list[RepoOut]
