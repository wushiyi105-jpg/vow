"""SQLite：budget / vendors / tasks / guests / jobs。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Boolean, Date, Float, Integer, String, Text, inspect, select
from sqlalchemy.orm import Mapped, Session, mapped_column, sessionmaker

from ...domain.models import BudgetItem, Guest, Task, Vendor
from .base import Base, make_engine, make_session


class BudgetRow(Base):
    __tablename__ = "budget"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(40))
    planned: Mapped[float] = mapped_column(Float)
    actual: Mapped[float] = mapped_column(Float, default=0.0)
    deposit: Mapped[float] = mapped_column(Float, default=0.0)


class VendorRow(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    quote: Mapped[str] = mapped_column(Text, default="")
    amount: Mapped[float] = mapped_column(Float, default=0.0)


class TaskRow(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    due_on: Mapped[date] = mapped_column(Date)
    done: Mapped[bool] = mapped_column(Boolean, default=False)


class GuestRow(Base):
    __tablename__ = "guests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(60))
    side: Mapped[str] = mapped_column(String(12), default="bride")
    count: Mapped[int] = mapped_column(Integer, default=1)
    table_no: Mapped[int] = mapped_column(Integer, default=0)


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idem_key: Mapped[str] = mapped_column(String(80), unique=True)
    kind: Mapped[str] = mapped_column(String(24))
    payload: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(12), default="pending")
    due_on: Mapped[date] = mapped_column(Date)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str] = mapped_column(Text, default="")


def _upgrade_schema(engine) -> None:
    root = next(p for p in Path(__file__).resolve().parents if (p / "alembic.ini").exists())
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{engine.url.database}")
    command.upgrade(cfg, "head")


class SqliteStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.engine = make_engine(self.path)
        self.session: sessionmaker[Session] = make_session(self.engine)
        self.init_schema()

    def init_schema(self) -> None:
        _upgrade_schema(self.engine)

    def schema_ok(self) -> bool:
        return {"budget", "vendors", "tasks", "guests", "jobs"} <= set(
            inspect(self.engine).get_table_names()
        )

    def summary(self) -> str:
        return f"{len(self.list_budget())} 个预算项、{len(self.list_guests())} 位宾客"

    def add_budget(self, category: str, planned: float, actual: float, deposit: float = 0.0) -> int:
        if planned < 0 or actual < 0:
            raise ValueError("金额不能为负")
        with self.session() as s:
            row = BudgetRow(category=category, planned=planned, actual=actual, deposit=deposit)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_budget(self) -> list[BudgetItem]:
        with self.session() as s:
            rows = s.scalars(select(BudgetRow)).all()
        return [BudgetItem(r.id, r.category, r.planned, r.actual, r.deposit) for r in rows]

    def add_vendor(self, name: str, quote: str, amount: float) -> int:
        with self.session() as s:
            row = VendorRow(name=name, quote=quote, amount=amount)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_vendors(self) -> list[Vendor]:
        with self.session() as s:
            rows = s.scalars(select(VendorRow)).all()
        return [Vendor(r.id, r.name, r.quote, r.amount) for r in rows]

    def add_task(self, name: str, due_on: date, done: bool = False) -> int:
        with self.session() as s:
            row = TaskRow(name=name, due_on=due_on, done=done)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_tasks(self) -> list[Task]:
        with self.session() as s:
            rows = s.scalars(select(TaskRow).order_by(TaskRow.due_on)).all()
        return [Task(r.id, r.name, r.due_on, r.done) for r in rows]

    def add_guest(self, name: str, side: str, count: int = 1, table_no: int = 0) -> int:
        if count <= 0:
            raise ValueError("人数必须为正")
        with self.session() as s:
            row = GuestRow(name=name, side=side, count=count, table_no=table_no)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_guests(self) -> list[Guest]:
        with self.session() as s:
            rows = s.scalars(select(GuestRow)).all()
        return [Guest(r.id, r.name, r.side, r.count, r.table_no) for r in rows]

    def enqueue(self, idem_key: str, kind: str, payload: str, due_on: date) -> bool:
        with self.session() as s:
            if s.scalar(select(JobRow).where(JobRow.idem_key == idem_key)):
                return False
            s.add(JobRow(idem_key=idem_key, kind=kind, payload=payload, due_on=due_on))
            s.commit()
            return True

    def due_jobs(self, today: date) -> list[JobRow]:
        with self.session() as s:
            return list(s.scalars(select(JobRow).where(JobRow.status == "pending", JobRow.due_on <= today)).all())

    def finish_job(self, job_id: int, ok: bool, error: str = "") -> None:
        with self.session() as s:
            row = s.get(JobRow, job_id)
            if row is None:
                return
            row.status = "done" if ok else "pending"
            row.attempts += 1
            row.error = error
            s.commit()

