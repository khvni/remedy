from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Optional

import jwt
import requests

GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com")


@dataclass
class GitHubAuthConfig:
    app_id: str
    installation_id: str
    private_key_b64: str

    @classmethod
    def from_env(cls) -> Optional["GitHubAuthConfig"]:
        app_id = os.getenv("GITHUB_APP_ID")
        installation_id = os.getenv("GITHUB_INSTALLATION_ID")
        private_key = os.getenv("GITHUB_PRIVATE_KEY")
        if not app_id or not installation_id or not private_key:
            return None
        return cls(app_id=app_id, installation_id=installation_id, private_key_b64=private_key)

    def decode_private_key(self) -> bytes:
        return base64.b64decode(self.private_key_b64)


def _build_jwt(config: GitHubAuthConfig) -> str:
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 9 * 60,
        "iss": config.app_id,
    }
    token = jwt.encode(payload, config.decode_private_key(), algorithm="RS256")
    return token


def get_installation_token(config: GitHubAuthConfig) -> Optional[str]:
    try:
        jwt_token = _build_jwt(config)
    except Exception:
        return None

    url = f"{GITHUB_API_URL}/app/installations/{config.installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }

    response = requests.post(url, headers=headers, timeout=30)
    if response.status_code != 201:
        return None

    data = response.json()
    return data.get("token")


def open_pull_request(
    token: str,
    repo_full_name: str,
    head: str,
    base: str,
    title: str,
    body: str,
) -> Optional[str]:
    url = f"{GITHUB_API_URL}/repos/{repo_full_name}/pulls"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    payload = {"title": title, "head": head, "base": base, "body": body}

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    if response.status_code not in {200, 201}:
        return None
    data = response.json()
    return data.get("html_url")


def fetch_default_branch(token: str, repo_full_name: str) -> Optional[str]:
    url = f"{GITHUB_API_URL}/repos/{repo_full_name}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        return None
    data = response.json()
    return data.get("default_branch")
