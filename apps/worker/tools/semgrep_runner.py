from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)
_DEFAULT_CONFIG = Path(__file__).resolve().parents[2] / "scanners" / "semgrep" / "profiles.yml"


def run_semgrep(repo_dir: str) -> list[dict[str, Any]]:
    config_override = os.getenv("SEMGREP_CONFIG_PATH")
    config_path = Path(config_override) if config_override else _DEFAULT_CONFIG

    cmd = [
        "semgrep",
        "--config",
        str(config_path),
        "--json",
        "--timeout",
        os.getenv("SEMGREP_TIMEOUT", "180"),
        "--quiet",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        logger.warning("Semgrep binary not found; skipping SAST scan")
        return []

    if result.returncode not in {0, 1}:
        logger.warning("Semgrep failed (%s): %s", result.returncode, result.stderr.strip())
        return []

    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError:
        logger.warning("Semgrep returned invalid JSON output")
        return []

    findings: list[dict[str, Any]] = []
    for item in payload.get("results", []) or []:
        extra = item.get("extra", {})
        finding = {
            "severity": str(extra.get("severity", "MEDIUM")).upper(),
            "path": item.get("path") or "",
            "line": (item.get("start") or {}).get("line"),
            "rule_id": item.get("check_id"),
            "message": extra.get("message") or extra.get("metadata", {}).get("short_message", ""),
        }
        findings.append(finding)

    return findings
