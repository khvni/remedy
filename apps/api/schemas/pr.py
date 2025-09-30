from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PullRequestListItem(BaseModel):
    id: str
    repo_id: str
    branch: str
    pr_url: Optional[str] = None
    status: str
    summary: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
