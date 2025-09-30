from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any


def _rewrite_file(path: Path, edit: dict[str, Any], results: dict[str, list]):
    if not path.is_file():
        results["skipped"].append({"path": edit.get("path"), "reason": "missing_file"})
        return

    original = path.read_text(encoding="utf-8", errors="ignore")
    updated = original

    match_literal = edit.get("match")
    regex_pattern = edit.get("regex")
    replacement = edit.get("replace", "")

    if match_literal:
        if match_literal not in original:
            results["skipped"].append({"path": edit.get("path"), "reason": "match_not_found"})
            return
        updated = original.replace(match_literal, replacement)
    elif regex_pattern:
        try:
            updated, count = re.subn(regex_pattern, replacement, original, flags=re.MULTILINE)
        except re.error as exc:  # pragma: no cover - defensive
            results["skipped"].append({"path": edit.get("path"), "reason": f"regex_error:{exc}"})
            return
        if count == 0:
            results["skipped"].append({"path": edit.get("path"), "reason": "regex_no_match"})
            return
    else:
        results["skipped"].append({"path": edit.get("path"), "reason": "no_operation"})
        return

    if updated == original:
        results["skipped"].append({"path": edit.get("path"), "reason": "no_change"})
        return

    path.write_text(updated, encoding="utf-8")
    results["touched"].append(edit.get("path"))


def apply_patch_plan(repo_dir: str, plan: list[dict[str, Any]] | None) -> dict[str, Any]:
    repo_path = Path(repo_dir)
    results: dict[str, list] = {"touched": [], "skipped": []}

    for item in plan or []:
        for edit in item.get("edits", []) or []:
            rel_path = edit.get("path")
            if not rel_path:
                results["skipped"].append({"path": None, "reason": "missing_path"})
                continue
            target = (repo_path / rel_path).resolve()
            try:
                target.relative_to(repo_path.resolve())
            except ValueError:
                results["skipped"].append({"path": rel_path, "reason": "outside_repo"})
                continue
            _rewrite_file(target, edit, results)

    diff_proc = subprocess.run(
        ["git", "diff"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )

    return {
        "touched": sorted(set(results["touched"])),
        "skipped": results["skipped"],
        "diff": diff_proc.stdout,
    }
