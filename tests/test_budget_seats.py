from __future__ import annotations

from vow.domain.models import BudgetItem, Guest
from vow.domain.rules.budget import check, total
from vow.domain.rules.seats import guest_count, per_person_cost, per_table_cost, rounding, tables


def _b(category="酒店宴席", planned=1000, actual=1000):
    return BudgetItem(1, category, planned, actual)


def test_warn_at_five_percent():
    findings = check([_b(actual=1060)])
    assert findings[0].rule_id == "budget.warn"


def test_red_at_fifteen_percent():
    findings = check([_b(actual=1200)])
    assert findings[0].rule_id == "budget.over"


def test_within_budget_silent():
    assert check([_b(actual=1000)]) == []


def test_total_sums_both_sides():
    assert total([_b(planned=1000, actual=900), _b(planned=500, actual=600)]) == (1500, 1500)


def test_tables_round_up():
    assert tables(28) == 3
    assert tables(30) == 3


def test_guest_count_sums_counts():
    assert guest_count([Guest(1, "a", "bride", 3), Guest(2, "b", "groom", 2)]) == 5


def test_per_person_moves_with_table_count():
    [Guest(1, "a", "bride", 25)]
    assert per_table_cost(9000, 25) == 3000
    assert per_person_cost(9000, 25) == 360


def test_rounding_flags_half_empty_table():
    findings = rounding([Guest(1, "a", "bride", 22)])
    assert findings[0].rule_id == "seats.round"

