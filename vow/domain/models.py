"""领域对象：预算、供应商、宾客、筹备任务。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class BudgetItem:
    id: int
    category: str
    planned: float
    actual: float
    deposit: float = 0.0


@dataclass(frozen=True)
class Vendor:
    id: int
    name: str
    quote: str
    amount: float


@dataclass(frozen=True)
class Guest:
    id: int
    name: str
    side: str
    count: int = 1
    table_no: int = 0


@dataclass(frozen=True)
class Task:
    id: int
    name: str
    due_on: date
    done: bool = False


@dataclass
class Finding:
    rule_id: str
    message: str
    penalty: int
    target: str = ""


@dataclass
class Plan:
    wedding_on: date
    days_left: int
    planned: float = 0.0
    actual: float = 0.0
    guests: int = 0
    tables: int = 0
    per_table: float = 0.0
    per_person: float = 0.0
    overdue: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    hidden: list[dict[str, str]] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    source: str = "offline"

    @property
    def ratio(self) -> float:
        return self.actual / self.planned if self.planned else 0.0

    @property
    def penalty_total(self) -> int:
        return sum(f.penalty for f in self.findings)
