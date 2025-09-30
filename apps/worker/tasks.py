from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from apps.api.models.db import SessionLocal
from apps.api.models.finding import Finding
from apps.api.models.pr import PullRequest
from apps.api.models.repo import Repo
from apps.api.models.scan import Scan

from .agent.orchestrator import prioritize_and_plan
from .tools.git_tool import create_branch_and_pr
from .tools.grype_runner import run_grype
from .tools.osv_runner import run_osv
from .tools.patch_apply import apply_patch_plan
from .tools.semgrep_runner import run_semgrep
from .tools.syft_runner import generate_sbom

logger = logging.getLogger(__name__)


def _clone_repo(repo_url: str, destination: Path) -> None:
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(destination)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git clone failed: {result.stderr.strip()}")


def _enrich_findings(raw_findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for finding in raw_findings:
        item = dict(finding)
        item.setdefault("finding_id", str(uuid.uuid4()))
        enriched.append(item)
    return enriched


def run_scan(repo_id: str, kind: str) -> dict[str, Any]:
    tmpdir = Path(tempfile.mkdtemp(prefix="remedy_"))
    with SessionLocal() as session:
        repo = session.get(Repo, repo_id)
        if not repo:
            shutil.rmtree(tmpdir, ignore_errors=True)
            logger.error("Repository %s not found for scan", repo_id)
            return {"error": "repo_not_found", "repo_id": repo_id}

        scan = Scan(
            id=str(uuid.uuid4()),
            repo_id=repo_id,
            kind=kind,
            status="running",
            created_at=datetime.utcnow(),
        )
        session.add(scan)
        session.commit()
        session.refresh(scan)

        try:
            _clone_repo(repo.url, tmpdir)

            if kind == "sast":
                raw_findings = run_semgrep(str(tmpdir))
            else:
                raw_findings = run_osv(str(tmpdir))
                sbom_path = generate_sbom(str(tmpdir))
                if sbom_path:
                    try:
                        raw_findings.extend(run_grype(sbom_path))
                    finally:
                        sbom_path.unlink(missing_ok=True)

            if not isinstance(raw_findings, list):
                raw_findings = []

            findings = _enrich_findings(raw_findings)
            scan.findings_json = {"items": findings}
            scan.status = "completed"
            session.add(scan)
            session.commit()

            plans = prioritize_and_plan(findings)
            plan_payloads = [p.get("plan") for p in plans if isinstance(p, dict) and p.get("plan")]
            plan_payloads = [p for p in plan_payloads if isinstance(p, dict)]

            apply_result = None
            git_metadata = None
            if plan_payloads:
                apply_result = apply_patch_plan(str(tmpdir), plan_payloads)
                if apply_result.get("touched"):
                    git_metadata = create_branch_and_pr(str(tmpdir), repo.url, plan_payloads)

            for bundle in plans:
                finding_data = bundle.get("finding", {}) if isinstance(bundle, dict) else {}
                plan_data = bundle.get("plan") if isinstance(bundle, dict) else None
                session.add(
                    Finding(
                        id=str(uuid.uuid4()),
                        scan_id=scan.id,
                        severity=str(finding_data.get("severity", "UNKNOWN")),
                        path=str(finding_data.get("path", "")),
                        line=finding_data.get("line"),
                        rule_id=finding_data.get("rule_id"),
                        description=finding_data.get("message") or bundle.get("summary"),
                        plan_json=plan_data,
                    )
                )

            if git_metadata:
                pr = PullRequest(
                    id=str(uuid.uuid4()),
                    repo_id=repo_id,
                    branch=git_metadata.get("branch", ""),
                    pr_url=git_metadata.get("pr_url"),
                    status="draft" if git_metadata.get("pr_url") is None else "open",
                    summary="; ".join(
                        filter(
                            None,
                            [bundle.get("summary") for bundle in plans if isinstance(bundle, dict)],
                        )
                    ),
                    created_at=datetime.utcnow(),
                )
                session.add(pr)

            session.commit()

            return {
                "scan_id": scan.id,
                "repo_id": repo_id,
                "kind": kind,
                "finding_count": len(findings),
                "applied_files": (apply_result or {}).get("touched", []),
                "branch": (git_metadata or {}).get("branch"),
            }
        except Exception as exc:  # pragma: no cover - worker level safety
            session.rollback()
            scan.status = "failed"
            scan.findings_json = {"error": str(exc)}
            session.add(scan)
            session.commit()
            logger.exception("Scan %s failed", scan.id)
            raise
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
