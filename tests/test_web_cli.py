from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from vow.doctor import run_doctor
from vow.iface.cli import app
from vow.iface.web import create_app


def _seed(store):
    store.add_budget("宴席", 100000, 120000, 20000)
    store.add_guest("女方亲戚", "bride", 25)
    store.add_task("排座位", date(2026, 11, 25))


def test_web_index(store, settings):
    _seed(store)
    client = TestClient(create_app(settings, store))
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Vow" in resp.text


def test_web_status_text(store, settings):
    _seed(store)
    client = TestClient(create_app(settings, store))
    text = client.get("/status.txt").text
    assert "剩" in text and "3 桌" in text


def test_cli_status_and_bad_day(tmp_path):
    runner = CliRunner()
    db = str(tmp_path / "c.db")
    assert runner.invoke(app, ["status", "--db", db, "--day", "2026-11-27"]).exit_code == 0
    assert runner.invoke(app, ["status", "--db", db, "--day", "2026-13-01"]).exit_code != 0


def test_cli_vendor_missing(tmp_path):
    res = CliRunner().invoke(app, ["vendor", "--vendor-id", "99", "--db", str(tmp_path / "c.db")])
    assert res.exit_code == 2


def test_doctor_green(settings):
    checks, ok = run_doctor(settings)
    assert ok is True
