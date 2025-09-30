from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
from typing import Optional

from ..schemas.scan import ScanQueuedResponse, ScanRequest, ScanDetail, ScanListItem
from ..services.scan_service import start_scan, RepoNotFoundError, list_scans, get_scan

router = APIRouter()


@router.post("", response_model=ScanQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
def create_scan(request: ScanRequest, db: Session = Depends(get_db)) -> ScanQueuedResponse:
    try:
        job_ids = start_scan(db, request.repo_id, request.kinds)
    except RepoNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return ScanQueuedResponse(repo_id=request.repo_id, queued_jobs=job_ids)


@router.get("", response_model=list[ScanListItem])
def list_scans_endpoint(repo_id: Optional[str] = None, db: Session = Depends(get_db)) -> list[ScanListItem]:
    scans = list_scans(db, repo_id=repo_id)
    return [ScanListItem.model_validate(scan) for scan in scans]


@router.get("/{scan_id}", response_model=ScanDetail)
def get_scan_detail(scan_id: str, db: Session = Depends(get_db)) -> ScanDetail:
    scan = get_scan(db, scan_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    return ScanDetail.model_validate(scan)
