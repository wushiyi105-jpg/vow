"""用例：核算 → 供应商隐藏项 → 谈判问题。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ..config import Settings
from ..domain.engine import build
from ..domain.guard import check as hidden_check
from ..domain.models import Finding, Plan, Vendor
from ..ports import LLMPort, StorePort

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "vendor.md").read_text(encoding="utf-8")


def plan(store: StorePort, settings: Settings, today: date | None = None) -> Plan:
    return build(
        store.list_budget(), store.list_guests(), store.list_tasks(),
        settings.wedding_on, today or date.today(),
    )


def review_vendor(
    store: StorePort,
    settings: Settings,
    vendor_id: int,
    today: date | None = None,
    llm: LLMPort | None = None,
) -> tuple[Plan, list[str], list[Finding]]:
    p = plan(store, settings, today)
    vendor = next((v for v in store.list_vendors() if v.id == vendor_id), None)
    if vendor is None:
        raise ValueError(f"没有这个供应商：{vendor_id}")
    if llm is None:
        return p, [], []
    try:
        data = json.loads(llm.write(PROMPT, f"vendor={vendor.name}\nquote={vendor.quote}"))
    except Exception:  # noqa: BLE001
        return p, [], []
    fees, findings = hidden_check(data.get("hidden_fees", []), vendor.quote)
    return p, [str(q) for q in data.get("questions", [])], findings


def facts(p: Plan, vendors: list[Vendor]) -> str:
    lines = [
        f"婚期={p.wedding_on} 剩 {p.days_left} 天",
        f"预算={p.planned:.0f} 已花={p.actual:.0f} 比例={p.ratio:.0%}",
        f"宾客={p.guests} 桌={p.tables} 每桌={p.per_table:.0f} 人均={p.per_person:.0f}",
    ]
    for v in vendors:
        lines.append(f"- {v.name} 报价 {v.amount:.0f}")
    return "\n".join(lines)
