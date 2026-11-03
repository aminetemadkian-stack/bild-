"""Dry-run every tool with a fixed sample input and report errors per tool.

No network calls, no writes outside memory. Tools that need a running server
or external credentials are reported as SKIPPED with the reason, never faked.
"""
import os
import traceback
from typing import Any, Callable

from app.agents.tool_registry import TOOLS, area_tool_from_text, takeoff_from_text
from app.agents.checklists import checklist_for
from app.services.dxf_export import concept_dxf

SAMPLE_BRIEF = "متره و مساحت سوله ۲۵×۶۰ متر با ارتفاع ۳ متر؛ فروشگاه، انبار و کانتر تحویل"

def _area():
    r = area_tool_from_text("مساحت ۲۵×۶۰ متر")
    assert r and r["area_m2"] == 1500, f"unexpected area result: {r}"
    return {"area_m2": r["area_m2"]}

def _takeoff():
    r = takeoff_from_text("متره با ارتفاع ۳ متر، ابعاد ۲۵×۶۰ متر")
    assert r and r["floor_area_m2"] == 1500 and r["wall_area_m2"] == 510, f"unexpected takeoff: {r}"
    return {"floor_area_m2": r["floor_area_m2"], "wall_area_m2": r["wall_area_m2"]}

def _checklist():
    r = checklist_for("structure", SAMPLE_BRIEF)
    assert "گزارش خاک" in r["missing"], f"soil report should be missing: {r}"
    return {"missing": len(r["missing"]), "present": len(r["present"])}

def _dxf():
    text = concept_dxf(25, 60, 3, 15, "dry-run")
    assert text.rstrip().endswith("EOF"), "DXF must end with EOF"
    return {"bytes": len(text)}

def _online_model():
    # Dry run never calls the network: it only checks that configuration exists.
    missing = [k for k in ("LLM_API_KEY", "LLM_MODEL") if not os.environ.get(k)]
    if missing:
        return {"status": "SKIPPED", "reason": "not configured: " + ", ".join(missing)}
    return {"configured": True}

def _document_reader():
    return {"status": "SKIPPED", "reason": "needs the running FastAPI upload path; covered by integration tests"}

def _workflow_monitor():
    return {"status": "SKIPPED", "reason": "reads live in-memory events; covered by integration tests"}

def _concept_svg():
    return {"status": "SKIPPED", "reason": "served by /api/v1/concept/drawing; covered by integration tests"}

RUNNERS: dict[str, Callable[[], dict[str, Any]]] = {
    "area_calculator": _area,
    "quantity_takeoff": _takeoff,
    "discipline_checklist": _checklist,
    "online_model": _online_model,
    "document_reader": _document_reader,
    "workflow_monitor": _workflow_monitor,
    "concept_svg": _concept_svg,
}

def dry_run_all() -> list[dict[str, Any]]:
    report = []
    for tool_id, spec in TOOLS.items():
        runner = RUNNERS.get(tool_id)
        if runner is None:
            report.append({"tool": tool_id, "name": spec.name, "status": "NO_RUNNER", "error": "no dry-run defined for this tool"})
            continue
        try:
            out = runner()
            status = out.pop("status", "PASS")
            reason = out.pop("reason", "")
            report.append({"tool": tool_id, "name": spec.name, "status": status, "output": out, "reason": reason})
        except AssertionError as exc:
            report.append({"tool": tool_id, "name": spec.name, "status": "FAIL", "error": str(exc)})
        except Exception as exc:
            report.append({"tool": tool_id, "name": spec.name, "status": "ERROR", "error": f"{type(exc).__name__}: {exc}", "trace": traceback.format_exc(limit=2)})
    return report

def to_markdown(report: list[dict[str, Any]]) -> str:
    lines = ["| ابزار | وضعیت | جزئیات |", "|---|---|---|"]
    for row in report:
        detail = row.get("error") or row.get("reason") or str(row.get("output", ""))
        lines.append(f"| {row['name']} (`{row['tool']}`) | {row['status']} | {detail} |")
    counts: dict[str, int] = {}
    for row in report:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    summary = " · ".join(f"{k}: {v}" for k, v in sorted(counts.items()))
    return "\n".join(lines) + f"\n\n**خلاصه:** {summary}\n"

if __name__ == "__main__":
    print(to_markdown(dry_run_all()))
