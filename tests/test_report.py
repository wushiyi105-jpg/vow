"""新功能：一条命令出可直接转发的备婚报告。"""

from __future__ import annotations

from typer.testing import CliRunner

from vow.app.run import review_quote
from vow.domain.catalog import checklist, local_hidden
from vow.domain.models import Vendor
from vow.iface.cli import app


def test_catalog_has_28_items_and_30_surcharges() -> None:
    assert len(checklist()) == 28
    assert len(local_hidden("进场费 2000 元；服务费 10%；超时费 1500 元/小时。")) >= 3


def test_model_fee_kept_and_local_fee_added() -> None:
    vendor = Vendor(1, "测试酒店", "进场费 2000 元；服务费 10%。", 50000)
    fees, questions, findings, source = review_quote(vendor, None)
    texts = {f["text"] for f in fees}
    assert {"进场费", "服务费"} <= texts
    assert source == "offline"
    assert questions == []


def test_report_cli_writes_markdown(tmp_path) -> None:
    runner = CliRunner()
    db = str(tmp_path / "vow.db")
    out = tmp_path / "备婚报告.md"
    seed = runner.invoke(app, ["seed", "--db", db])
    assert seed.exit_code == 0
    result = runner.invoke(app, ["report", "--db", db, "--day", "2026-11-27", "--no-llm", "--out", str(out)])
    assert result.exit_code == 0
    body = out.read_text(encoding="utf-8")
    assert "# 备婚预算与供应商体检" in body
    assert "28 项筹备倒排" in body
    assert "进场费" in body
    assert "本次未调用模型" in body
    assert body.count("| 已完成 |") >= 6
