"""FastAPI + Jinja2：备婚总览。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..adapters.store import SqliteStore
from ..app.run import plan
from ..config import Settings

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


def create_app(settings: Settings, store: SqliteStore | None = None) -> FastAPI:
    app = FastAPI(title="Vow", version="1.0.0")
    app.mount(
        "/static",
        StaticFiles(directory=str(Path(__file__).resolve().parents[2] / "static")),
        name="static",
    )
    store = store or SqliteStore(settings.db_path)

    def render(request: Request) -> HTMLResponse:
        p = plan(store, settings)
        return TEMPLATES.TemplateResponse(
            request, "index.html",
            {"p": p, "today": date.today().isoformat(), "tasks": store.list_tasks(),
             "budget": store.list_budget(), "vendors": store.list_vendors()},
        )

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        return render(request)

    @app.get("/status.txt", response_class=PlainTextResponse)
    def status_text() -> PlainTextResponse:
        p = plan(store, settings)
        return PlainTextResponse(
            f"婚期 {p.wedding_on} 剩 {p.days_left} 天；预算 {p.planned:.0f} 已花 {p.actual:.0f}"
            f"（{p.ratio:.0%}）；{p.guests} 人 {p.tables} 桌",
            media_type="text/plain; charset=utf-8",
        )

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "guests": len(store.list_guests())}

    return app


def app_factory(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        from ..config import settings as default_settings

        settings = default_settings
    return create_app(settings)

