"""命令行：seed / status / vendor / jobs / doctor / serve。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..adapters.llm import build_llm
from ..adapters.notify import WebhookNotifier
from ..adapters.store import SqliteStore
from ..app.jobs import enqueue_daily, run_due
from ..app.report import build_report
from ..app.run import PROMPT, plan, review_vendor
from ..config import Settings
from ..config import settings as default_settings
from ..doctor import main as doctor_main
from ..domain.catalog import checklist, due_on

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
    # 28 项清单按婚期倒排；前 7 项视为已办，方便第一次跑就有一条完整时间线。
    for index, item in enumerate(checklist()):
        store.add_task(item["name"], due_on(item, s.wedding_on), index < 7)
    for v in data["vendors"]:
        store.add_vendor(v["name"], v["quote"], v["amount"])
    console.print(
        f"已写入 {len(data['budget'])} 个预算项、{len(data['guests'])} 位宾客、"
        f"{len(checklist())} 个筹备节点、{len(data['vendors'])} 家供应商"
    )


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
def report(
    day: str = typer.Option("", help="核算日期 YYYY-MM-DD，默认今天"),
    out: Path = typer.Option(None, help="输出 Markdown 文件；不填打印到终端"),
    no_llm: bool = typer.Option(False, "--no-llm", help="强制只用本地加价词典"),
    db: Path = typer.Option(None),
) -> None:
    """一页备婚报告：预算、比价、隐藏加价、28 项倒排。"""
    s = _settings(db)
    d = date.fromisoformat(day) if day else date.today()
    llm = None
    if s.llm_enabled and not no_llm:
        llm = build_llm(s.llm_base_url, s.llm_api_key, s.llm_model, PROMPT)
    text, p = build_report(_store(s), s, d, llm)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        console.print(f"[green]已写出[/] {out}（{len(text.splitlines())} 行）")
    else:
        console.print(text)
    if p.source == "offline":
        console.print("[dim]本次为本地核算：模型未参与，报价疑点来自本地词典。[/]")


@app.command()
def vendor(vendor_id: int = typer.Option(...), db: Path = typer.Option(None)) -> None:
    """看某家供应商的隐藏项。"""
    s = _settings(db)
    try:
        llm = build_llm(s.llm_base_url, s.llm_api_key, s.llm_model, PROMPT) if s.llm_enabled else None
        p, questions, findings = review_vendor(_store(s), s, vendor_id, llm=llm)
    except ValueError as exc:
        console.print(f"[red]{exc}[/]")
        raise typer.Exit(code=2) from exc
    for fee in p.hidden:
        console.print(f"加价：{fee['text']}（{fee['quote']}）")
    for q in questions:
        console.print(f"问：{q}")
    for f in findings:
        console.print(f"  [yellow]{f.rule_id}[/] -{f.penalty} {f.message}")
    if p.source == "offline":
        console.print("[dim]本次为本地核算：模型未参与，疑点来自本地加价词典。[/]")


@app.command()
def jobs(
    day: str = typer.Option(""), run: bool = typer.Option(False, "--run"), db: Path = typer.Option(None)
) -> None:
    """每日逾期扫描。"""
    s = _settings(db)
    d = date.fromisoformat(day) if day else date.today()
    store = _store(s)
    if run:
        console.print(f"发出 {run_due(store, s, d, WebhookNotifier(s.webhook_url))} 条")
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
