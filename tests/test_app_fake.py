"""真实内存 Store 跑 plan：不建 SQLite，mypy 校验 StorePort。"""

from __future__ import annotations

from datetime import date
from typing import Any

from vow.app.run import plan
from vow.config import Settings
from vow.domain.models import BudgetItem, Guest, Task, Vendor
from vow.ports import StorePort


class InMemoryStore:
    def list_budget(self) -> list[BudgetItem]:
        return []

    def list_guests(self) -> list[Guest]:
        return []

    def list_tasks(self) -> list[Task]:
        return []

    def list_vendors(self) -> list[Vendor]:
        return []

    def enqueue(self, idem_key: str, kind: str, payload: str, due_on: date) -> bool:
        return True

    def due_jobs(self, today: date) -> list[Any]:
        return []

    def finish_job(self, job_id: int, ok: bool, error: str = "") -> None:
        return None


def test_plan_with_memory_store(tmp_path) -> None:
    store: StorePort = InMemoryStore()
    out = plan(store, Settings(db_path=tmp_path / "x.db"), date(2026, 1, 5))
    assert out.planned == 0.0
    assert not (tmp_path / "x.db").exists()
