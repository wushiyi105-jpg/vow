"""OpenAI 兼容客户端：超时、指数退避、空 content 重试、截断翻倍重试。"""

from __future__ import annotations

import time
from typing import Any

import httpx

MAX_TOKENS_CAP = 8000


class LLMError(RuntimeError):
    pass


class OpenAICompatLLM:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        system_prompt: str,
        timeout: float = 30.0,
        retries: int = 3,
        max_tokens: int = 600,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt
        self.timeout = timeout
        self.retries = retries
        self.max_tokens = max_tokens

    def write(self, system: str, facts: str) -> str:
        system = system or self.system_prompt
        max_tokens = self.max_tokens
        last: str | None = None
        for attempt in range(self.retries):
            payload: dict[str, Any] = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": facts},
                ],
                "temperature": 0.2,
                "max_tokens": max_tokens,
            }
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(
                        f"{self.base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json=payload,
                    )
                    resp.raise_for_status()
                    data = resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                last = str(exc)
                time.sleep(0.4 * (2 ** attempt))
                continue

            choice = (data.get("choices") or [{}])[0]
            content = str((choice.get("message") or {}).get("content") or "").strip()
            if choice.get("finish_reason") == "length" and max_tokens < MAX_TOKENS_CAP:
                max_tokens = min(max_tokens * 2, MAX_TOKENS_CAP)
                continue
            if not content:
                last = "模型返回空 content"
                time.sleep(0.4 * (2 ** attempt))
                continue
            return content
        raise LLMError(last or "模型调用失败")


def build_llm(base_url: str, api_key: str, model: str, system_prompt: str) -> OpenAICompatLLM:
    return OpenAICompatLLM(base_url, api_key, model, system_prompt)
