from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_sbom(repo_dir: str) -> Path | None:
    """Generate a Syft SBOM for the given repository, returning the file path."""
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    sbom_path = Path(handle.name)
    handle.close()

    env = {**os.environ, "SYFT_LOG": os.getenv("SYFT_LOG", "error")}
    cmd = ["syft", f"dir:{repo_dir}", "-o", "json"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
    except FileNotFoundError:
        logger.warning("Syft binary not found; skipping SBOM generation")
        sbom_path.unlink(missing_ok=True)
        return None

    if result.returncode != 0:
        logger.warning("Syft failed (%s): %s", result.returncode, result.stderr.strip())
        sbom_path.unlink(missing_ok=True)
        return None

    sbom_path.write_text(result.stdout, encoding="utf-8")
    return sbom_path
