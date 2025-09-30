from __future__ import annotations

import os
from collections.abc import Sequence
from typing import Optional

from rq import Queue
from redis import Redis
from sqlalchemy.orm import Session

from ...worker.tasks import run_scan
from ..models.repo import Repo
from ..models.scan import Scan

redis = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
q = Queue(os.getenv("RQ_QUEUE", "remedy"), connection=redis)


class RepoNotFoundError(Exception):
    """Raised when an operation is attempted on a repo that does not exist."""


def start_scan(db: Session, repo_id: str, kinds: Sequence[str]) -> list[str]:
    repo = db.get(Repo, repo_id)
    if not repo:
        raise RepoNotFoundError(repo_id)
    job_ids: list[str] = []
    for kind in kinds:
        job = q.enqueue(run_scan, repo_id, kind)
        job_ids.append(job.id)
    return job_ids


def list_scans(db: Session, repo_id: Optional[str] = None) -> list[Scan]:
    query = db.query(Scan).order_by(Scan.created_at.desc())
    if repo_id:
        query = query.filter(Scan.repo_id == repo_id)
    return query.all()


def get_scan(db: Session, scan_id: str) -> Optional[Scan]:
    return db.get(Scan, scan_id)
