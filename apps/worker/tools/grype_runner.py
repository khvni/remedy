from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def run_grype(sbom_path: str | Path) -> list[dict[str, Any]]:
    path = Path(sbom_path)
    if not path.is_file():
        return []

    cmd = ["grype", f"sbom:{path}", "-o", "json"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        logger.warning("Grype binary not found; skipping SBOM scan")
        return []

    if result.returncode not in {0, 1}:
        logger.warning("Grype failed (%s): %s", result.returncode, result.stderr.strip())
        return []

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        logger.warning("Grype returned invalid JSON")
        return []

    findings: list[dict[str, Any]] = []
    for match in payload.get("matches", []) or []:
        if not isinstance(match, dict):
            continue
        vuln = match.get("vulnerability", {}) or {}
        artifact = match.get("artifact", {}) or {}
        locations = artifact.get("locations") or []
        location = locations[0] if locations else {}
        path_hint = location.get("path") or location.get("filepath") or artifact.get("name")
        summary = vuln.get("description") or vuln.get("summary")
        identifier = vuln.get("id") or vuln.get("ids", [{}])[0].get("id")
        severity = (vuln.get("severity") or "UNKNOWN").upper()

        if not identifier:
            continue

        findings.append(
            {
                "severity": severity,
                "path": path_hint or artifact.get("name", "dependency"),
                "line": None,
                "rule_id": identifier,
                "message": summary or f"{artifact.get('name')} {artifact.get('version')} vulnerable ({identifier})",
            }
        )

    return findings
