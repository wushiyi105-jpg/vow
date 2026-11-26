"""桌数：10 人一桌，向上取整，人均随桌数同步。"""

from __future__ import annotations

import math

from ..models import Finding, Guest

PER_TABLE = 10
ROUND_PENALTY = 2


def guest_count(guests: list[Guest]) -> int:
    return sum(g.count for g in guests)


def tables(count: int, per_table: int = PER_TABLE) -> int:
    if count <= 0:
        return 0
    return math.ceil(count / per_table)


def per_table_cost(total: float, count: int) -> float:
    t = tables(count)
    return total / t if t else 0.0


def per_person_cost(total: float, count: int) -> float:
    return total / count if count else 0.0


def rounding(guests: list[Guest], per_table: int = PER_TABLE) -> list[Finding]:
    count = guest_count(guests)
    if count == 0:
        return []
    left = count % per_table
    if left == 0:
        return []
    return [
        Finding(
            "seats.round",
            f"{count} 人坐 {tables(count, per_table)} 桌，最后一桌只坐 {left} 人",
            ROUND_PENALTY,
            "seats",
        )
    ]
