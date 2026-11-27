"""主用例只依赖 ports：用 MagicMock 内存假实现，不建 SQLite 文件。"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from vow.app.run import plan
from vow.config import Settings
from vow.ports import StorePort


def test_main_path_with_memory_store(tmp_path) -> None:
    store = MagicMock(spec=StorePort)
    
    out = plan(store, Settings(), date(2026, 1, 5))
    assert out is not None
    assert not (tmp_path / "app.db").exists()
