from __future__ import annotations

from datetime import date

from vow.domain.guard import check
from vow.domain.models import Task
from vow.domain.rules.timeline import milestones, overdue


def test_overdue_task_flagged():
    findings = overdue([Task(1, "婚车与路线", date(2026, 11, 25))], date(2026, 11, 27))
    assert findings[0].rule_id == "timeline.overdue"


def test_done_task_never_overdue():
    assert overdue([Task(1, "定酒店", date(2026, 6, 30), True)], date(2026, 11, 27)) == []


def test_milestone_counts_backwards():
    assert milestones(date(2027, 5, 2), 4, "发请柬") == date(2027, 4, 4)


def test_hidden_fee_with_quote_kept():
    quote = "宴席 86000 元；进场费 2000 元。"
    kept, findings = check([{"text": "进场费", "quote": "进场费 2000 元"}], quote)
    assert kept and findings == []


def test_hidden_fee_without_quote_dropped():
    quote = "宴席 86000 元。"
    kept, findings = check([{"text": "进场费", "quote": "进场费 2000 元"}], quote)
    assert kept == []
    assert findings[0].rule_id == "guard.hidden"
