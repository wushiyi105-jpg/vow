"""倒排：从婚期反推，逾期未完成高亮。"""

from __future__ import annotations

from datetime import date

from ..models import Finding, Task

PENALTY = 4


def overdue(tasks: list[Task], today: date) -> list[Finding]:
    return [
        Finding(
            "timeline.overdue",
            f"{t.name} 原定 {t.due_on}，已过 {(today - t.due_on).days} 天没完成",
            PENALTY,
            t.name,
        )
        for t in tasks
        if not t.done and t.due_on < today
    ]


def milestones(wedding: date, weeks_before: int, name: str) -> date:
    from datetime import timedelta

    return wedding - timedelta(weeks=weeks_before)
