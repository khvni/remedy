from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from typing import Optional

from ..deps import get_db
from ..schemas.finding import FindingListItem
from ..services.finding_service import list_findings

router = APIRouter()


@router.get("", response_model=list[FindingListItem])
def list_findings_endpoint(
    repo_id: Optional[str] = None,
    scan_id: Optional[str] = None,
    db: Session = Depends(get_db),
) -> list[FindingListItem]:
    findings = list_findings(db, repo_id=repo_id, scan_id=scan_id)
    return [FindingListItem.model_validate(item) for item in findings]
