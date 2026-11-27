"""用例：核算 → 供应商隐藏项 → 谈判问题。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ..config import Settings
from ..domain.catalog import merge_hidden
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


def review_quote(
    vendor: Vendor, llm: LLMPort | None = None
) -> tuple[list[dict[str, str]], list[str], list[Finding], str]:
    """模型只填“疑点 + 原文 + 问题”，本地再补齐漏项。"""
    model_fees: list[dict] = []
    questions: list[str] = []
    findings: list[Finding] = []
    source = "offline"
    if llm is not None:
        try:
            data = json.loads(llm.write(PROMPT, f"vendor={vendor.name}\nquote={vendor.quote}"))
            raw_fees = list(data.get("hidden_fees", []))
            model_fees, findings = hidden_check(raw_fees, vendor.quote)
            questions = [str(q) for q in data.get("questions", []) if str(q).strip()]
            source = "model"
        except Exception:  # noqa: BLE001
            source = "offline"
    return merge_hidden(vendor.quote, model_fees), questions, findings, source


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
    fees, questions, findings, source = review_quote(vendor, llm)
    p.hidden = fees
    p.questions = questions
    p.findings.extend(findings)
    p.source = source
    return p, questions, findings


def facts(p: Plan, vendors: list[Vendor]) -> str:
    lines = [
        f"婚期={p.wedding_on} 剩 {p.days_left} 天",
        f"预算={p.planned:.0f} 已花={p.actual:.0f} 比例={p.ratio:.0%}",
        f"宾客={p.guests} 桌={p.tables} 每桌={p.per_table:.0f} 人均={p.per_person:.0f}",
    ]
    for v in vendors:
        lines.append(f"- {v.name} 报价 {v.amount:.0f}")
    return "\n".join(lines)
