"""一页备婚报告：预算、桌数、供应商比价、28 项倒排。

模型只负责补“报价疑点 + 谈判问题”，数字和排版都在本地完成。
"""

from __future__ import annotations

from datetime import date

from ..domain.catalog import checklist, due_on
from ..domain.engine import build
from ..domain.models import Plan, Task
from ..ports import LLMPort, StorePort
from .run import review_quote


def _money(value: float) -> str:
    return f"{value:,.0f}"


def _task_status(task: Task | None, today: date) -> str:
    if task is None:
        return "待建"
    if task.done:
        return "已完成"
    if task.due_on < today:
        return f"逾期 {(today - task.due_on).days} 天"
    return "进行中"


def build_report(
    store: StorePort,
    settings,
    today: date | None = None,
    llm: LLMPort | None = None,
) -> tuple[str, Plan]:
    day = today or date.today()
    p = build(
        store.list_budget(),
        store.list_guests(),
        store.list_tasks(),
        settings.wedding_on,
        day,
    )
    vendors = store.list_vendors()
    tasks = {t.name: t for t in store.list_tasks()}
    items = checklist()

    reviews: dict[int, tuple[list[dict[str, str]], list[str], str]] = {}
    for index, vendor in enumerate(vendors):
        # 一条命令最多问模型 3 家，剩下由本地加价词典兜底，避免报告等太久。
        fees, questions, _, source = review_quote(vendor, llm if index < 3 else None)
        reviews[vendor.id] = (fees, questions, source)

    lines = [
        f"# 备婚预算与供应商体检 · {settings.wedding_on.isoformat()}",
        "",
        f"> 婚期还有 **{p.days_left} 天**；本报告数字由本地核算，"
        f"{'AI 只补报价疑点，不写预算数字。' if llm is not None else '本次未调用模型，报价疑点由本地加价词典从原文提取。'}",
        "",
        "## 一、预算总览",
        "",
        "| 分类 | 计划 | 已花 | 差额 | 状态 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for item in store.list_budget():
        diff = item.actual - item.planned
        if item.planned <= 0:
            status = "未设预算"
        elif diff / item.planned >= 0.15:
            status = "红色超支"
        elif diff / item.planned >= 0.05:
            status = "黄色预警"
        elif diff > 0:
            status = "略超"
        else:
            status = "正常"
        lines.append(
            f"| {item.category} | {_money(item.planned)} | {_money(item.actual)} | "
            f"{'+' if diff > 0 else ''}{_money(diff)} | {status} |"
        )
    lines += [
        f"| **合计** | **{_money(p.planned)}** | **{_money(p.actual)}** | "
        f"**{'+' if p.actual > p.planned else ''}{_money(p.actual - p.planned)}** | "
        f"**{p.ratio:.0%}** |",
        "",
        f"- 定金已付：{_money(sum(i.deposit for i in store.list_budget()))} 元（不计入已花）。",
        f"- 宾客 {p.guests} 人，按 10 人一桌取整为 **{p.tables} 桌**；"
        f"每桌 {_money(p.per_table)} 元，人均 {_money(p.per_person)} 元。",
        f"- 最后一桌 {p.guests % 10 or 10} 人，空位 {0 if p.guests % 10 == 0 else 10 - p.guests % 10} 个。",
        "",
        "## 二、供应商比价与隐藏加价",
        "",
    ]
    if not vendors:
        lines.append("还没有录入供应商报价。")
        lines.append("")
    for vendor in vendors:
        fees, questions, source = reviews[vendor.id]
        lines += [
            f"### {vendor.name} · 报价 {_money(vendor.amount)} 元",
            "",
            f"> 报价原文：{vendor.quote}",
            "",
        ]
        if fees:
            lines.append("| 加价项 | 报价原文 | 为什么要注意 | 来源 |")
            lines.append("| --- | --- | --- | --- |")
            for fee in fees:
                lines.append(
                    f"| {fee['text']} | {fee['quote']} | {fee['why']} | "
                    f"{'模型' if fee['source'] == 'model' else '本地词典'} |"
                )
            lines.append("")
        else:
            lines.append("未在原文里识别到加价词，仍建议逐条确认“含/不含/另计”。")
            lines.append("")
        if questions:
            lines.append("**发给供应商前先问：**")
            lines.append("")
            for q in questions[:6]:
                lines.append(f"- {q}")
            lines.append("")
        if source != "model":
            lines.append("> 这一家的谈判问题未由模型生成，只保留了本地原文疑点。")
            lines.append("")

    lines += [
        "## 三、28 项筹备倒排",
        "",
        "| 节点 | 分类 | 计划日期 | 状态 |",
        "| --- | --- | --- | --- |",
    ]
    for row in items:
        due = due_on(row, settings.wedding_on)
        task = tasks.get(row["name"])
        lines.append(
            f"| {row['name']} | {row['category']} | {due.isoformat()} | "
            f"{_task_status(task, day)} |"
        )
    lines += [
        "",
        "## 四、现在最该做的 3 件事",
        "",
    ]
    urgent = [t for t in store.list_tasks() if not t.done and t.due_on <= day]
    urgent.sort(key=lambda t: t.due_on)
    if urgent:
        for task in urgent[:3]:
            lines.append(f"- **{task.name}**：原定 {task.due_on.isoformat()}，已逾期 {(day - task.due_on).days} 天。")
    else:
        lines.append("- 当前没有逾期节点；按上面的倒排表提前 2 周确认桌数与座位。")
    lines += [
        "",
        "---",
        "",
        "口径：桌数按 10 人/桌向上取整；预算按已花/计划算；隐藏加价必须能引回报价原文，引不到就不列。",
        "",
    ]
    p.source = "model" if any(v[2] == "model" for v in reviews.values()) else "offline"
    return "\n".join(lines), p
