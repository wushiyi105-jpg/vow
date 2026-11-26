"""配置：多一个婚期。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="VOW_", extra="ignore")

    db_path: Path = Path("data/vow.db")
    port: int = 8008
    llm_base_url: str = "https://api.deepseek.com"
    llm_api_key: str = ""
    llm_model: str = "deepseek-flash"
    llm_timeout: float = 30.0
    webhook_url: str = ""
    TZ: str = "Asia/Shanghai"
    wedding_on: date = date(2027, 5, 2)

    @property
    def llm_enabled(self) -> bool:
        return bool(self.llm_api_key)


settings = Settings()
