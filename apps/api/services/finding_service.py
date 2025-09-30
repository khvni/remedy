from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from ..models.finding import Finding
from ..models.scan import Scan


def list_findings(
    db: Session,
    repo_id: Optional[str] = None,
    scan_id: Optional[str] = None,
) -> list[Finding]:
    query = db.query(Finding).order_by(Finding.created_at.desc())
    if scan_id:
        query = query.filter(Finding.scan_id == scan_id)
    if repo_id:
        query = query.join(Scan, Scan.id == Finding.scan_id).filter(Scan.repo_id == repo_id)
    return query.all()
