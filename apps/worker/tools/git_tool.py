"""Utilities for turning patch plans into Git branches and PR metadata."""

from __future__ import annotations

import json
import os
import re
import subprocess
import uuid
from typing import Any, Optional

from .github_app import (
    GitHubAuthConfig,
    fetch_default_branch,
    get_installation_token,
    open_pull_request,
)


def _git(cmd: list[str], cwd: str, env: Optional[dict[str, str]] = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False, env=env)


def _repo_full_name(origin_url: str) -> Optional[str]:
    ssh_match = re.match(r"git@github.com:(?P<name>[^/]+/.+?)\.git$", origin_url)
    if ssh_match:
        return ssh_match.group("name")
    https_match = re.match(r"https://github.com/(?P<name>[^/]+/.+?)(\.git)?$", origin_url)
    if https_match:
        return https_match.group("name")
    return None


def _token_remote(origin_url: str, token: str) -> Optional[str]:
    repo_name = _repo_full_name(origin_url)
    if not repo_name:
        return None
    return f"https://x-access-token:{token}@github.com/{repo_name}.git"


def _ensure_branch(repo_dir: str, branch: str, plan: list[dict[str, Any]] | None) -> Optional[str]:
    author_name = os.getenv("GIT_AUTHOR_NAME", "Remedy Bot")
    author_email = os.getenv("GIT_AUTHOR_EMAIL", "remedy@example.com")

    _git(["git", "config", "user.name", author_name], cwd=repo_dir)
    _git(["git", "config", "user.email", author_email], cwd=repo_dir)

    checkout = _git(["git", "checkout", "-b", branch], cwd=repo_dir)
    if checkout.returncode != 0:
        return None

    add_result = _git(["git", "add", "-A"], cwd=repo_dir)
    if add_result.returncode != 0:
        return None

    commit_message = "Remedy automated fix"
    if plan:
        summaries = [item.get("summary") for item in plan if isinstance(item, dict)]
        commit_message = next((s for s in summaries if s), commit_message)

    commit = _git(["git", "commit", "-m", commit_message], cwd=repo_dir)
    if commit.returncode != 0:
        return None

    commit_sha = _git(["git", "rev-parse", "HEAD"], cwd=repo_dir)
    return commit_sha.stdout.strip() if commit_sha.returncode == 0 else None


def create_branch_and_pr(
    repo_dir: str,
    origin_url: str,
    plan: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    status = _git(["git", "status", "--porcelain"], cwd=repo_dir)
    if status.returncode != 0 or not status.stdout.strip():
        return None

    branch = f"remedy/fix-{uuid.uuid4().hex[:8]}"
    commit_sha = _ensure_branch(repo_dir, branch, plan)
    if not commit_sha:
        return None

    metadata = {
        "branch": branch,
        "commit": commit_sha,
        "origin_url": origin_url,
        "pr_url": None,
    }

    config = GitHubAuthConfig.from_env()
    if not config:
        return metadata

    token = get_installation_token(config)
    repo_full_name = _repo_full_name(origin_url)
    if not token or not repo_full_name:
        return metadata

    remote_url = _token_remote(origin_url, token)
    if not remote_url:
        return metadata

    _git(["git", "remote", "remove", "remedy-origin"], cwd=repo_dir)
    add_remote = _git(["git", "remote", "add", "remedy-origin", remote_url], cwd=repo_dir)
    if add_remote.returncode != 0:
        return metadata

    push_env = {**os.environ, "GIT_ASKPASS": "", "GIT_TERMINAL_PROMPT": "0"}
    push = _git(["git", "push", "-u", "remedy-origin", branch], cwd=repo_dir, env=push_env)
    if push.returncode != 0:
        return metadata

    default_branch = fetch_default_branch(token, repo_full_name) or os.getenv("GITHUB_DEFAULT_BRANCH", "main")
    title = plan[0].get("summary") if plan else "Remedy automated fix"
    body = "" if not plan else json.dumps(plan, indent=2)
    pr_url = open_pull_request(
        token=token,
        repo_full_name=repo_full_name,
        head=branch,
        base=default_branch,
        title=title or "Remedy automated fix",
        body=f"Automated remediation plan:\n\n```json\n{body}\n```" if body else "Automated remediation by Remedy.",
    )

    if pr_url:
        metadata["pr_url"] = pr_url

    return metadata
