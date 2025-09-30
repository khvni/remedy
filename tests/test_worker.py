from __future__ import annotations

import uuid
from pathlib import Path

from apps.api.models.repo import Repo
from apps.api.models.scan import Scan
from apps.api.models.finding import Finding
from apps.api.models.pr import PullRequest
import apps.worker.tasks as tasks


def test_run_scan_persists_findings(monkeypatch, test_sessionmaker):
    session = test_sessionmaker()
    try:
        repo = Repo(id=str(uuid.uuid4()), name="demo", url="https://example.com/demo.git")
        session.add(repo)
        session.flush()
        repo_id = repo.id
        session.commit()
    finally:
        session.close()

    def fake_clone(_url: str, destination: Path):
        Path(destination).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(tasks, "_clone_repo", fake_clone)
    monkeypatch.setattr(tasks, "run_semgrep", lambda repo_dir: [
        {
            "severity": "HIGH",
            "path": "app.js",
            "line": 1,
            "rule_id": "test.rule",
            "message": "Hardcoded secret",
        }
    ])
    monkeypatch.setattr(tasks, "run_osv", lambda repo_dir: [])
    monkeypatch.setattr(tasks, "generate_sbom", lambda repo_dir: None)
    monkeypatch.setattr(tasks, "run_grype", lambda sbom: [])

    def fake_prioritize(findings):
        first = findings[0]
        return [
            {
                "finding": first,
                "summary": "Mask hardcoded secret",
                "plan": {
                    "finding_id": first["finding_id"],
                    "summary": "Mask hardcoded secret",
                    "fix_kind": "regex",
                    "edits": [
                        {
                            "path": "app.js",
                            "match": "secret",
                            "replace": "process.env.SECRET",
                            "note": "Replace literal with env",
                        }
                    ],
                    "test": {"cmd": "npm test", "expect": "pass"},
                },
            }
        ]

    monkeypatch.setattr(tasks, "prioritize_and_plan", fake_prioritize)
    monkeypatch.setattr(tasks, "apply_patch_plan", lambda repo_dir, plan: {
        "touched": ["app.js"],
        "skipped": [],
        "diff": "diff --git a/app.js b/app.js",
    })
    monkeypatch.setattr(tasks, "create_branch_and_pr", lambda repo_dir, origin_url, plan: {
        "branch": "remedy/fix-1234",
        "commit": "abcdef1",
        "pr_url": None,
    })

    result = tasks.run_scan(repo_id, "sast")
    assert result["finding_count"] == 1
    assert result["branch"] == "remedy/fix-1234"

    verify = test_sessionmaker()
    try:
        scans = verify.query(Scan).all()
        findings = verify.query(Finding).all()
        prs = verify.query(PullRequest).all()
    finally:
        verify.close()

    assert len(scans) == 1
    assert scans[0].status == "completed"
    assert len(findings) == 1
    assert findings[0].plan_json is not None
    assert len(prs) == 1
    assert prs[0].branch == "remedy/fix-1234"
