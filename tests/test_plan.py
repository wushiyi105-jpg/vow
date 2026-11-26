from __future__ import annotations

from datetime import date

from vow.domain.engine import build


def test_plan_matches_budget_and_seats():
    items = [__import__("vow.domain.models", fromlist=["BudgetItem"]).BudgetItem(1, "宴席", 100000, 120000)]
    guests = [__import__("vow.domain.models", fromlist=["Guest"]).Guest(1, "a", "bride", 25)]
    p = build(items, guests, [], date(2027, 5, 2), date(2026, 11, 27))
    assert p.tables == 3
    assert p.per_table == 40000
    assert p.per_person == 4800
    assert p.days_left == 156
    assert any(f.rule_id == "budget.over" for f in p.findings)
