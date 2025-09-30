from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Template

from .providers.gemini_client import gemini_complete

_PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
_PRIORITIZE_TEMPLATE = Template((_PROMPT_DIR / "prioritize.j2").read_text(encoding="utf-8"))
_PLAN_TEMPLATE = Template((_PROMPT_DIR / "plan_patch.j2").read_text(encoding="utf-8"))


def _try_load_json(raw: str, default: Any) -> Any:
    try:
        return json.loads(raw)
    except Exception:
        return default


def prioritize_and_plan(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not findings:
        return []

    priority_prompt = _PRIORITIZE_TEMPLATE.render(findings=json.dumps(findings, indent=2))
    priority_response = gemini_complete(priority_prompt)
    priority = _try_load_json(priority_response, {})
    ordered = priority.get("ordered_findings") if isinstance(priority, dict) else None
    if not ordered:
        return []

    plans: list[dict[str, Any]] = []
    for item in ordered[:3]:
        if not isinstance(item, dict):
            continue
        finding_id = str(item.get("finding_id")) if item.get("finding_id") is not None else None
        if not finding_id:
            continue
        matched = next((f for f in findings if str(f.get("finding_id")) == finding_id), None)
        if not matched:
            continue

        plan_prompt = _PLAN_TEMPLATE.render(
            finding=json.dumps(matched, indent=2),
            fix_strategy=item.get("fix_strategy", ""),
        )
        plan_response = gemini_complete(plan_prompt)
        plan = _try_load_json(plan_response, None)
        if not isinstance(plan, dict):
            continue
        plan.setdefault("finding_id", finding_id)
        plan.setdefault("summary", item.get("summary"))
        plans.append(
            {
                "finding": matched,
                "summary": item.get("summary"),
                "justification": item.get("justification"),
                "plan": plan,
            }
        )

    return plans
