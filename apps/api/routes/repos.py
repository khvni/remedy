from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db
from ..schemas.repo import RepoCreate, RepoOut, RepoListOut
from ..services.repo_service import create_repo, list_repos, get_repo

router = APIRouter()


@router.post("", response_model=RepoOut, status_code=status.HTTP_201_CREATED)
def register_repo(body: RepoCreate, db: Session = Depends(get_db)) -> RepoOut:
    repo = create_repo(db, body.url)
    return RepoOut.model_validate(repo)


@router.get("", response_model=RepoListOut)
def list_registered_repos(db: Session = Depends(get_db)) -> RepoListOut:
    repos = list_repos(db)
    return RepoListOut(items=[RepoOut.model_validate(r) for r in repos])


@router.get("/{repo_id}", response_model=RepoOut)
def get_repo_detail(repo_id: str, db: Session = Depends(get_db)) -> RepoOut:
    repo = get_repo(db, repo_id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return RepoOut.model_validate(repo)
