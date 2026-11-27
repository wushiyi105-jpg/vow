"""迁移是真的：空库 upgrade 建出的表与模型一致，downgrade base 可往返。"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from vow.adapters.store import Base

ROOT = Path(__file__).resolve().parents[1]


def _cfg(db: Path) -> Config:
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db}")
    return cfg


def test_upgrade_creates_all_model_tables(tmp_path: Path) -> None:
    db = tmp_path / "schema.db"
    command.upgrade(_cfg(db), "head")
    names = set(inspect(create_engine(f"sqlite:///{db}")).get_table_names())
    assert set(Base.metadata.tables) <= names
    assert "alembic_version" in names


def test_downgrade_then_upgrade(tmp_path: Path) -> None:
    db = tmp_path / "round.db"
    cfg = _cfg(db)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    engine = create_engine(f"sqlite:///{db}")
    assert not set(Base.metadata.tables) & set(inspect(engine).get_table_names())
    command.upgrade(cfg, "head")
    assert set(Base.metadata.tables) <= set(inspect(engine).get_table_names())