from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)
_DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "scanners" / "osv" / "config.toml"


def run_osv(repo_dir: str) -> list[dict[str, Any]]:
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp_path = Path(tmp.name)
    tmp.close()

    config_override = os.getenv("OSV_CONFIG_PATH")
    cmd = ["osv-scanner", "--recursive", repo_dir, "--format", "json", "--output", str(tmp_path)]
    if config_override:
        cmd.extend(["--config", config_override])
    elif _DEFAULT_CONFIG.exists():
        cmd.extend(["--config", str(_DEFAULT_CONFIG)])

    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        logger.warning("osv-scanner binary not found; skipping dependency scan")
        tmp_path.unlink(missing_ok=True)
        return []

    if result.returncode not in {0, 1}:  # osv-scanner returns 1 when it finds vulns
        logger.warning("osv-scanner failed (%s): %s", result.returncode, result.stderr.strip())
        tmp_path.unlink(missing_ok=True)
        return []

    try:
        data = json.loads(tmp_path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Unable to parse osv-scanner output: %s", exc)
        tmp_path.unlink(missing_ok=True)
        return []
    finally:
        tmp_path.unlink(missing_ok=True)

    findings: list[dict[str, Any]] = []
    for entry in data.get("results", []) or []:
        for vuln in entry.get("vulnerabilities", []) or []:
            severity_list = vuln.get("severity") or []
            severity = next((s.get("score") for s in severity_list if s.get("score")), "UNSPECIFIED")
            findings.append(
                {
                    "severity": str(severity).upper(),
                    "path": entry.get("source", ""),
                    "line": None,
                    "rule_id": vuln.get("id"),
                    "message": vuln.get("summary") or vuln.get("details", ""),
                }
            )

    return findings
