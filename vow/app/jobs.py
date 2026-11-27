"""每日逾期扫描。"""

from __future__ import annotations

from datetime import date

from ..config import Settings
from ..ports import NotifierPort, StorePort
from .run import plan


def enqueue_daily(store: StorePort, today: date) -> bool:
    return store.enqueue(f"vow:{today}", "overdue_scan", today.isoformat(), today)


def run_due(store: StorePort, settings: Settings, today: date, notifier: NotifierPort) -> int:
    sent = 0
    for job in store.due_jobs(today):
        p = plan(store, settings, today)
        text = f"备婚倒排：逾期 {len(p.overdue)} 项\n" + "\n".join(f"- {x}" for x in p.overdue)
        ok = notifier.send(text)
        store.finish_job(job.id, ok, "" if ok else "推送失败")
        sent += int(ok)
    return sent
