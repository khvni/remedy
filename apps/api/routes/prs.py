from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from typing import Optional

from ..deps import get_db
from ..schemas.pr import PullRequestListItem
from ..services.pr_service import list_prs

router = APIRouter()


@router.get("", response_model=list[PullRequestListItem])
def list_pull_requests(repo_id: Optional[str] = None, db: Session = Depends(get_db)) -> list[PullRequestListItem]:
    prs = list_prs(db, repo_id)
    return [PullRequestListItem.model_validate(pr) for pr in prs]
