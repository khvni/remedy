from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..deps import get_db
from ..services.webhook_service import handle_github_event

router = APIRouter()


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: Optional[str] = Header(default=None, alias="X-GitHub-Event"),
    db: Session = Depends(get_db),
):
    if not x_github_event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing X-GitHub-Event header")

    payload = await request.json()
    result = handle_github_event(db, x_github_event, payload)
    return result
