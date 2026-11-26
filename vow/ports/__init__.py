"""端口：domain 与 app 只认这里的协议，具体实现放在 adapters。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class StorePort(Protocol):
    def summary(self) -> str: ...


@runtime_checkable
class LLMPort(Protocol):
    def write(self, system: str, facts: str) -> str: ...


@runtime_checkable
class NotifierPort(Protocol):
    def send(self, text: str) -> bool: ...
