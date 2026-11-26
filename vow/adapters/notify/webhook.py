"""webhook 推送：飞书 / 钉钉 / 企微都收 text 这一层。"""

from __future__ import annotations

import httpx


class WebhookNotifier:
    def __init__(self, url: str, timeout: float = 8.0) -> None:
        self.url = url
        self.timeout = timeout

    def send(self, text: str) -> bool:
        if not self.url:
            return False
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    self.url,
                    json={"msg_type": "text", "content": {"text": text}},
                )
            return resp.status_code < 400
        except httpx.HTTPError:
            return False
