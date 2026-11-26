from __future__ import annotations

from datetime import date

import pytest

from vow.adapters.store import SqliteStore
from vow.config import Settings


@pytest.fixture()
def store(tmp_path) -> SqliteStore:
    return SqliteStore(tmp_path / "t.db")


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(db_path=tmp_path / "t.db", llm_api_key="", port=8008, wedding_on=date(2027, 5, 2))
