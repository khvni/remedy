from __future__ import annotations

from fastapi.testclient import TestClient

import apps.worker.tasks as tasks


def test_end_to_end_scan_flow(client: TestClient, monkeypatch):
    repo = client.post("/repos", json={"url": "https://github.com/example/app.git"}).json()

    monkeypatch.setattr(tasks, "_clone_repo", lambda url, dest: None)
    monkeypatch.setattr(tasks, "run_semgrep", lambda repo_dir: [
        {
            "severity": "HIGH",
            "path": "src/app.ts",
            "line": 42,
            "rule_id": "test.rule",
            "message": "Example finding",
        }
    ])
    monkeypatch.setattr(tasks, "run_osv", lambda repo_dir: [])
    monkeypatch.setattr(tasks, "generate_sbom", lambda repo_dir: None)
    monkeypatch.setattr(tasks, "run_grype", lambda path: [])

    def fake_prioritize(findings):
        first = findings[0]
        return [
            {
                "finding": first,
                "summary": "Patch example finding",
                "plan": {
                    "finding_id": first["finding_id"],
                    "summary": "Patch example finding",
                    "fix_kind": "manual",
                    "edits": [],
                    "test": {"cmd": "npm test", "expect": "pass"},
                },
            }
        ]

    monkeypatch.setattr(tasks, "prioritize_and_plan", fake_prioritize)
    monkeypatch.setattr(tasks, "apply_patch_plan", lambda repo_dir, plan: {
        "touched": ["src/app.ts"],
        "skipped": [],
        "diff": "diff --git a/src/app.ts b/src/app.ts",
    })
    monkeypatch.setattr(
        tasks,
        "create_branch_and_pr",
        lambda repo_dir, origin_url, plan: {
            "branch": "remedy/fix-5678",
            "commit": "1234567",
            "pr_url": "https://github.com/example/app/pull/1",
        },
    )

    tasks.run_scan(repo["id"], "sast")

    scans = client.get(f"/scans?repo_id={repo['id']}").json()
    assert len(scans) == 1
    assert scans[0]["status"] == "completed"

    findings = client.get(f"/findings?repo_id={repo['id']}").json()
    assert len(findings) == 1
    assert findings[0]["rule_id"] == "test.rule"

    prs = client.get(f"/prs?repo_id={repo['id']}").json()
    assert len(prs) == 1
    assert prs[0]["branch"] == "remedy/fix-5678"
