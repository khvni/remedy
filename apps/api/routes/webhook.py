from __future__ import annotations

from fastapi import APIRouter, Request, Header, HTTPException
import hmac
import hashlib
import os

router = APIRouter()


@router.post("/github")
async def github_webhook(request: Request, x_hub_signature_256: str = Header(None)):
    body = await request.body()
    secret = os.getenv("GITHUB_WEBHOOK_SECRET", "").encode()
    digest = "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, x_hub_signature_256 or ""):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    # TODO: handle event (push, pull_request, etc.)
    return {"ok": True}
