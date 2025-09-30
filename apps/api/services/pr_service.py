from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..models.pr import PullRequest


def list_prs(db: Session, repo_id: Optional[str]) -> list[PullRequest]:
    query = db.query(PullRequest).order_by(PullRequest.created_at.desc())
    if repo_id:
        query = query.filter(PullRequest.repo_id == repo_id)
    return query.all()
