"""隐藏项守卫：每条必须附报价原文片段，附不上就丢。"""

from __future__ import annotations

from .models import Finding

PENALTY = 6


def check(items: list[dict], quote: str) -> tuple[list[dict], list[Finding]]:
    kept: list[dict] = []
    findings: list[Finding] = []
    for it in items:
        text = str(it.get("text", ""))
        snippet = str(it.get("quote", ""))
        if not snippet or snippet not in quote:
            findings.append(
                Finding("guard.hidden", f"「{text}」找不到报价原文，不展示", PENALTY, text)
            )
            continue
        kept.append(it)
    return kept, findings

