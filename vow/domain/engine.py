"""本地核算：预算、桌数、倒排。"""

from __future__ import annotations

from datetime import date

from .models import BudgetItem, Finding, Guest, Plan, Task
from .rules.budget import check as budget_check
from .rules.budget import total
from .rules.seats import guest_count, per_person_cost, per_table_cost, rounding, tables
from .rules.timeline import overdue


def build(
    items: list[BudgetItem], guests: list[Guest], tasks: list[Task], wedding: date, today: date
) -> Plan:
    planned, actual = total(items)
    count = guest_count(guests)
    findings: list[Finding] = []
    findings += budget_check(items)
    findings += rounding(guests)
    findings += overdue(tasks, today)
    return Plan(
        wedding_on=wedding,
        days_left=(wedding - today).days,
        planned=planned,
        actual=actual,
        guests=count,
        tables=tables(count),
        per_table=per_table_cost(actual, count),
        per_person=per_person_cost(actual, count),
        overdue=[f.target for f in findings if f.rule_id == "timeline.overdue"],
        findings=findings,
    )
