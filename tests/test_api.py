from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def test_register_and_fetch_repo(client: TestClient):
    resp = client.post("/repos", json={"url": "https://github.com/example/juice-shop.git"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "juice-shop"

    list_resp = client.get("/repos")
    assert list_resp.status_code == 200
    listed = list_resp.json()["items"]
    assert len(listed) == 1
    assert listed[0]["id"] == body["id"]

    detail_resp = client.get(f"/repos/{body['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["url"] == body["url"]


def test_create_scan_enqueues_jobs(client: TestClient, queue_stub):
    repo = client.post("/repos", json={"url": "https://github.com/example/api.git"}).json()

    resp = client.post(
        "/scans",
        json={"repo_id": repo["id"], "kinds": ["sast", "sca"]},
    )
    assert resp.status_code == 202
    payload = resp.json()
    assert payload["repo_id"] == repo["id"]
    assert len(payload["queued_jobs"]) == 2
    assert len(queue_stub) == 2


def test_create_scan_missing_repo(client: TestClient):
    resp = client.post(
        "/scans",
        json={"repo_id": str(uuid.uuid4()), "kinds": ["sast"]},
    )
    assert resp.status_code == 404


def test_findings_endpoint_returns_empty_list(client: TestClient):
    resp = client.get("/findings")
    assert resp.status_code == 200
    assert resp.json() == []
