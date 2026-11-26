"""每日逾期扫描。"""

from __future__ import annotations

from datetime import date

from ..adapters.notify import WebhookNotifier
from ..adapters.store import SqliteStore
from ..config import Settings
from .run import plan


def enqueue_daily(store: SqliteStore, today: date) -> bool:
    return store.enqueue(f"vow:{today}", "overdue_scan", today.isoformat(), today)


def run_due(store: SqliteStore, settings: Settings, today: date) -> int:
    notifier = WebhookNotifier(settings.webhook_url)
    sent = 0
    for job in store.due_jobs(today):
        p = plan(store, settings, today)
        text = f"备婚倒排：逾期 {len(p.overdue)} 项\n" + "\n".join(f"- {x}" for x in p.overdue)
        ok = notifier.send(text)
        store.finish_job(job.id, ok, "" if ok else "推送失败")
        sent += int(ok)
    return sent
