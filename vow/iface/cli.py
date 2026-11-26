"""命令行：seed / status / vendor / jobs / doctor / serve。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..adapters.store import SqliteStore
from ..app.jobs import enqueue_daily, run_due
from ..app.run import plan, review_vendor
from ..config import Settings
from ..config import settings as default_settings
from ..doctor import main as doctor_main

app = typer.Typer(help="备婚：预算、供应商、倒排", no_args_is_help=True)
console = Console()


def _settings(db: Path | None, port: int | None = None) -> Settings:
    s = default_settings.model_copy(deep=True)
    if db:
        s.db_path = db
    if port:
        s.port = port
    return s


def _store(settings: Settings) -> SqliteStore:
    return SqliteStore(settings.db_path)


@app.command()
def seed(db: Path = typer.Option(None)) -> None:
    """写入预算、宾客、任务与供应商。"""
    s = _settings(db)
    store = _store(s)
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seed.json").read_text(encoding="utf-8")
    )
    for b in data["budget"]:
        store.add_budget(b["category"], b["planned"], b["actual"], b.get("deposit", 0))
    for g in data["guests"]:
        store.add_guest(g["name"], g["side"], g.get("count", 1))
    for t in data["tasks"]:
        store.add_task(t["name"], date.fromisoformat(t["due"]), t.get("done", False))
    for v in data["vendors"]:
        store.add_vendor(v["name"], v["quote"], v["amount"])
    console.print(f"已写入 {len(data['budget'])} 个预算项、{len(data['guests'])} 位宾客、{len(data['tasks'])} 个任务")


@app.command()
def status(day: str = typer.Option(""), db: Path = typer.Option(None)) -> None:
    """预算与倒排总览。"""
    s = _settings(db)
    d = date.fromisoformat(day) if day else date.today()
    p = plan(_store(s), s, d)
    table = Table(title=f"婚期 {p.wedding_on}（剩 {p.days_left} 天）")
    table.add_column("项")
    table.add_column("值")
    for k, v in [
        ("预算", f"{p.planned:.0f}"), ("已花", f"{p.actual:.0f}"), ("比例", f"{p.ratio:.0%}"),
        ("宾客", str(p.guests)), ("桌数", str(p.tables)), ("每桌", f"{p.per_table:.0f}"),
        ("人均", f"{p.per_person:.0f}"),
    ]:
        table.add_row(k, v)
    console.print(table)
    for f in p.findings:
        console.print(f"  [yellow]{f.rule_id}[/] -{f.penalty} {f.message}")


@app.command()
def vendor(vendor_id: int = typer.Option(...), db: Path = typer.Option(None)) -> None:
    """看某家供应商的隐藏项。"""
    s = _settings(db)
    try:
        p, questions, findings = review_vendor(_store(s), s, vendor_id)
    except ValueError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc
    for q in questions:
        console.print(f"问：{q}")
    for f in findings:
        console.print(f"  [yellow]{f.rule_id}[/] -{f.penalty} {f.message}")


@app.command()
def jobs(
    day: str = typer.Option(""), run: bool = typer.Option(False, "--run"), db: Path = typer.Option(None)
) -> None:
    """每日逾期扫描。"""
    s = _settings(db)
    d = date.fromisoformat(day) if day else date.today()
    store = _store(s)
    if run:
        console.print(f"发出 {run_due(store, s, d)} 条")
        return
    console.print("已入队" if enqueue_daily(store, d) else "今天已排过")


@app.command()
def doctor(db: Path = typer.Option(None)) -> None:
    """四项体检。"""
    raise typer.Exit(code=doctor_main(_settings(db)))


@app.command()
def serve(port: int = typer.Option(None), db: Path = typer.Option(None)) -> None:
    """Web 界面。"""
    import uvicorn

    from .web import create_app

    s = _settings(db, port)
    uvicorn.run(create_app(s), host="127.0.0.1", port=s.port)


if __name__ == "__main__":
    app()
