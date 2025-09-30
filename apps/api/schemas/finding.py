from __future__ import annotations

from typing import Optional, Any

from pydantic import BaseModel


class FindingListItem(BaseModel):
    id: str
    scan_id: str
    severity: str
    path: str
    line: Optional[int] = None
    rule_id: Optional[str] = None
    description: Optional[str] = None
    plan_json: Optional[Any] = None

    model_config = {"from_attributes": True}
