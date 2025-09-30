from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from ..models.repo import Repo


def _derive_repo_name(url: str) -> str:
    stripped = url.rstrip("/")
    last = stripped.split("/")[-1]
    return last.replace(".git", "")


def create_repo(db: Session, url: str) -> Repo:
    existing = db.query(Repo).filter(Repo.url == url).one_or_none()
    if existing:
        return existing
    repo = Repo(
        id=str(uuid.uuid4()),
        name=_derive_repo_name(url),
        url=url,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def list_repos(db: Session) -> list[Repo]:
    return (
        db.query(Repo)
        .order_by(Repo.created_at.desc())
        .all()
    )


def get_repo(db: Session, repo_id: str) -> Optional[Repo]:
    return db.get(Repo, repo_id)
