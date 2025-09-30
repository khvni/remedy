from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from .repo_service import create_repo
from .scan_service import start_scan, RepoNotFoundError


def handle_github_event(db: Session, event: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    if event not in {"push", "pull_request"}:
        return {"status": "ignored", "reason": "unsupported_event"}

    repo_info = payload.get("repository") if isinstance(payload, Mapping) else None
    if not isinstance(repo_info, Mapping):
        return {"status": "ignored", "reason": "missing_repository"}

    repo_url = (
        repo_info.get("clone_url")
        or repo_info.get("ssh_url")
        or repo_info.get("git_url")
    )
    if not repo_url:
        return {"status": "ignored", "reason": "missing_repo_url"}

    repo = create_repo(db, str(repo_url))

    if event == "pull_request":
        action = payload.get("action")
        if action not in {"opened", "synchronize", "reopened"}:
            return {"status": "ignored", "reason": f"action:{action}"}

    try:
        job_ids = start_scan(db, repo.id, ["sast", "sca"])
    except RepoNotFoundError:
        # Repo was just created, so this path is unlikely, but guard anyway.
        job_ids = []

    return {"status": "queued", "repo_id": repo.id, "jobs": job_ids}
