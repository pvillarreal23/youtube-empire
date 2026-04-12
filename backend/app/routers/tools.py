from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.tool import ToolDefinition, ToolCall

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
async def list_tools(
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ToolDefinition).where(ToolDefinition.enabled == True)
    if category:
        stmt = stmt.where(ToolDefinition.category == category)
    result = await db.execute(stmt)
    tools = result.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "input_schema": t.input_schema,
            "requires_approval": t.requires_approval,
            "enabled": t.enabled,
        }
        for t in tools
    ]


@router.get("/calls")
async def list_tool_calls(
    agent_id: Optional[str] = Query(None),
    thread_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ToolCall).order_by(ToolCall.created_at.desc())
    if agent_id:
        stmt = stmt.where(ToolCall.agent_id == agent_id)
    if thread_id:
        stmt = stmt.where(ToolCall.thread_id == thread_id)
    if status:
        stmt = stmt.where(ToolCall.status == status)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    calls = result.scalars().all()
    return [
        {
            "id": c.id,
            "message_id": c.message_id,
            "thread_id": c.thread_id,
            "agent_id": c.agent_id,
            "tool_id": c.tool_id,
            "tool_name": c.tool_name,
            "input_data": c.input_data,
            "output_data": c.output_data,
            "status": c.status,
            "error_message": c.error_message,
            "created_at": c.created_at,
            "completed_at": c.completed_at,
        }
        for c in calls
    ]


@router.get("/calls/{call_id}")
async def get_tool_call(call_id: str, db: AsyncSession = Depends(get_db)):
    tc = await db.get(ToolCall, call_id)
    if not tc:
        raise HTTPException(status_code=404, detail="Tool call not found")
    return {
        "id": tc.id,
        "message_id": tc.message_id,
        "thread_id": tc.thread_id,
        "agent_id": tc.agent_id,
        "tool_id": tc.tool_id,
        "tool_name": tc.tool_name,
        "input_data": tc.input_data,
        "output_data": tc.output_data,
        "status": tc.status,
        "error_message": tc.error_message,
        "created_at": tc.created_at,
        "started_at": tc.started_at,
        "completed_at": tc.completed_at,
    }


@router.get("/{tool_id}")
async def get_tool(tool_id: str, db: AsyncSession = Depends(get_db)):
    tool = await db.get(ToolDefinition, tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {
        "id": tool.id,
        "name": tool.name,
        "description": tool.description,
        "category": tool.category,
        "input_schema": tool.input_schema,
        "requires_approval": tool.requires_approval,
        "enabled": tool.enabled,
    }
