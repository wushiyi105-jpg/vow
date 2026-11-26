"""doctor：配置、数据库、模型、webhook 四项体检。失败退出码 1。"""

from __future__ import annotations

import sys
from dataclasses import dataclass

import httpx

from .adapters.store import SqliteStore
from .config import Settings


@dataclass
class Check:
    name: str
    ok: bool
    detail: str
    fatal: bool = True


def check_config(settings: Settings) -> Check:
    parent = settings.db_path.parent
    try:
        parent.mkdir(parents=True, exist_ok=True)
        probe = parent / ".doctor-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        return Check("配置", False, f"数据库目录不可写：{parent}（{exc}）")
    if not 1 <= settings.port <= 65535:
        return Check("配置", False, f"端口不合法：{settings.port}")
    mode = "在线" if settings.llm_enabled else "离线"
    return Check("配置", True, f"db={settings.db_path} port={settings.port} 模型={mode}")


def check_db(settings: Settings) -> Check:
    try:
        store = SqliteStore(settings.db_path)
        store.init_schema()
    except Exception as exc:  # noqa: BLE001 数据库坏了要报出来而不是抛栈
        return Check("数据库", False, f"打不开：{exc}")
    if not store.schema_ok():
        return Check("数据库", False, "缺表，跑 python -m vow seed 或 alembic upgrade head")
    return Check("数据库", True, store.summary())


def check_model(settings: Settings) -> Check:
    if not settings.llm_enabled:
        return Check("模型", True, "未配置 key，走离线模板", fatal=False)
    url = settings.llm_base_url.rstrip("/") + "/models"
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(url, headers={"Authorization": f"Bearer {settings.llm_api_key}"})
        if resp.status_code >= 400:
            return Check("模型", False, f"HTTP {resp.status_code}：{url}")
    except httpx.HTTPError as exc:
        return Check("模型", False, f"连不上：{exc}")
    return Check("模型", True, f"{settings.llm_model} @ {settings.llm_base_url}")


def check_webhook(settings: Settings) -> Check:
    if not settings.webhook_url:
        return Check("webhook", True, "未配置，跳过", fatal=False)
    try:
        with httpx.Client(timeout=6.0) as client:
            resp = client.get(settings.webhook_url)
        return Check("webhook", True, f"可达，HTTP {resp.status_code}")
    except httpx.HTTPError as exc:
        return Check("webhook", False, f"不可达：{exc}")


def run_doctor(settings: Settings) -> tuple[list[Check], bool]:
    checks = [
        check_config(settings),
        check_db(settings),
        check_model(settings),
        check_webhook(settings),
    ]
    failed = [c for c in checks if not c.ok and c.fatal]
    return checks, not failed


def main(settings: Settings | None = None) -> int:
    from .config import settings as default_settings

    checks, ok = run_doctor(settings or default_settings)
    for c in checks:
        mark = "OK " if c.ok else "FAIL"
        print(f"[{mark}] {c.name}：{c.detail}")
    if not ok:
        print("体检没过，先修上面标 FAIL 的项。")
        return 1
    print("体检通过。")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
