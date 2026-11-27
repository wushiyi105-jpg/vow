"""备婚知识库：28 项清单与 30 条报价加价词典。

这些数据只做两件事：倒排节点、把报价里的“另计/不含/超时”揪出来。
模型可以补问题，但不能替代这套本地口径。
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SPLIT = re.compile(r"[。；;\n]")


@lru_cache(maxsize=1)
def checklist() -> list[dict[str, Any]]:
    return json.loads((ROOT / "data" / "checklist.json").read_text(encoding="utf-8"))["items"]


@lru_cache(maxsize=1)
def surcharges() -> list[dict[str, Any]]:
    return json.loads((ROOT / "data" / "surcharges.json").read_text(encoding="utf-8"))["items"]


def due_on(item: dict[str, Any], wedding: date) -> date:
    return wedding - timedelta(days=int(item["lead_days"]))


def _snippet(quote: str, keyword: str) -> str:
    for part in SPLIT.split(quote.replace("，", "；")):
        if keyword in part:
            return part.strip(" ，,、")
    return keyword


def local_hidden(quote: str) -> list[dict[str, str]]:
    """从报价原文里找加价词，quote 字段就是原文连续片段。"""
    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in surcharges():
        text = str(row["name"])
        hit = next((k for k in row["keywords"] if k in quote), "")
        if not hit or text in seen:
            continue
        seen.add(text)
        out.append(
            {
                "text": text,
                "quote": _snippet(quote, hit),
                "why": str(row["why"]),
                "source": "local",
            }
        )
    return out


def merge_hidden(quote: str, model_items: list[dict[str, Any]]) -> list[dict[str, str]]:
    """模型结果在前，本地只补模型漏掉的项；同一条不重复列。"""
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in model_items:
        text = str(item.get("text", "")).strip()
        source_quote = str(item.get("quote", "")).strip()
        if not text or not source_quote or text in seen:
            continue
        seen.add(text)
        merged.append(
            {
                "text": text,
                "quote": source_quote,
                "why": str(item.get("why", "")),
                "source": "model",
            }
        )
    for item in local_hidden(quote):
        if item["text"] not in seen:
            seen.add(item["text"])
            merged.append(item)
    return merged
