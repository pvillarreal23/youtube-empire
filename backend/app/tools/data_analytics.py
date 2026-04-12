"""Data analytics tools: reports and metrics."""
from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tool_data import Task, Invoice
from app.models.thread import Thread, Message
from app.models.tool import ToolCall
from app.tools.registry import tool


@tool(
    id="generate_report",
    name="Generate Report",
    description="Generate a structured analytics report based on system data. Reports available: performance (task completion metrics), revenue (invoice data), activity (thread and message activity).",
    category="data_analytics",
    input_schema={
        "type": "object",
        "properties": {
            "report_type": {
                "type": "string",
                "enum": ["performance", "revenue", "activity"],
                "description": "Type of report to generate",
            },
            "period": {
                "type": "string",
                "description": "Time period for the report (e.g., 'all_time', 'last_7_days')",
                "default": "all_time",
            },
        },
        "required": ["report_type"],
    },
)
async def generate_report(
    report_type: str,
    period: str = "all_time",
    *,
    agent_id: str,
    db: AsyncSession,
    **kwargs,
) -> dict:
    if report_type == "performance":
        return await _performance_report(db)
    elif report_type == "revenue":
        return await _revenue_report(db)
    elif report_type == "activity":
        return await _activity_report(db)
    else:
        return {"error": f"Unknown report type: {report_type}"}


async def _performance_report(db: AsyncSession) -> dict:
    """Task completion metrics."""
    result = await db.execute(select(Task))
    tasks = list(result.scalars().all())

    total = len(tasks)
    by_status = {}
    by_priority = {}
    by_assignee = {}

    for t in tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        by_priority[t.priority] = by_priority.get(t.priority, 0) + 1
        assignee = t.assigned_to or "unassigned"
        by_assignee[assignee] = by_assignee.get(assignee, 0) + 1

    completion_rate = (by_status.get("complete", 0) / total * 100) if total > 0 else 0

    return {
        "report_type": "performance",
        "total_tasks": total,
        "completion_rate": f"{completion_rate:.1f}%",
        "by_status": by_status,
        "by_priority": by_priority,
        "by_assignee": by_assignee,
        "blocked_tasks": by_status.get("blocked", 0),
    }


async def _revenue_report(db: AsyncSession) -> dict:
    """Invoice and revenue metrics."""
    result = await db.execute(select(Invoice))
    invoices = list(result.scalars().all())

    total_invoices = len(invoices)
    total_amount = sum(i.amount for i in invoices)
    by_status = {}
    by_currency = {}

    for i in invoices:
        by_status[i.status] = by_status.get(i.status, 0) + 1
        key = i.currency or "USD"
        by_currency[key] = by_currency.get(key, 0) + i.amount

    return {
        "report_type": "revenue",
        "total_invoices": total_invoices,
        "total_amount": total_amount,
        "by_status": by_status,
        "by_currency": by_currency,
    }


async def _activity_report(db: AsyncSession) -> dict:
    """Thread and message activity metrics."""
    threads_result = await db.execute(select(func.count()).select_from(Thread))
    total_threads = threads_result.scalar() or 0

    messages_result = await db.execute(select(func.count()).select_from(Message))
    total_messages = messages_result.scalar() or 0

    agent_messages_result = await db.execute(
        select(func.count()).select_from(Message).where(Message.sender_type == "agent")
    )
    agent_messages = agent_messages_result.scalar() or 0

    tool_calls_result = await db.execute(select(func.count()).select_from(ToolCall))
    total_tool_calls = tool_calls_result.scalar() or 0

    return {
        "report_type": "activity",
        "total_threads": total_threads,
        "total_messages": total_messages,
        "agent_messages": agent_messages,
        "user_messages": total_messages - agent_messages,
        "total_tool_calls": total_tool_calls,
    }
