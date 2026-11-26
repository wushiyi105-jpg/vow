"""预算：超 5% 预警，超 15% 标红。"""

from __future__ import annotations

from ..models import BudgetItem, Finding

WARN = 0.05
RED = 0.15
PENALTY_WARN = 3
PENALTY_RED = 10


def check(items: list[BudgetItem]) -> list[Finding]:
    out: list[Finding] = []
    for it in items:
        if it.planned <= 0:
            continue
        ratio = it.actual / it.planned
        if ratio >= 1 + RED:
            out.append(
                Finding("budget.over", f"{it.category} 超支 {ratio - 1:.0%}（{it.actual:g}/{it.planned:g}）", PENALTY_RED, it.category)
            )
        elif ratio >= 1 + WARN:
            out.append(
                Finding("budget.warn", f"{it.category} 超支 {ratio - 1:.0%}", PENALTY_WARN, it.category)
            )
    return out


def total(items: list[BudgetItem]) -> tuple[float, float]:
    return sum(i.planned for i in items), sum(i.actual for i in items)


def deposit_gap(items: list[BudgetItem]) -> float:
    return sum(i.deposit for i in items)
