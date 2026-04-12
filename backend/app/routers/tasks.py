from __future__ import annotations

from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.tool_data import Task

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(
    status: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Task).order_by(Task.created_at.desc())
    if status:
        stmt = stmt.where(Task.status == status)
    if assigned_to:
        stmt = stmt.where(Task.assigned_to == assigned_to)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "assigned_to": t.assigned_to,
            "due_date": t.due_date,
            "priority": t.priority,
            "status": t.status,
            "project": t.project,
            "created_by_agent": t.created_by_agent,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
        }
        for t in tasks
    ]


@router.get("/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "due_date": task.due_date,
        "priority": task.priority,
        "status": task.status,
        "project": task.project,
        "created_by_agent": task.created_by_agent,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


@router.patch("/{task_id}")
async def update_task(
    task_id: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    allowed_fields = {"title", "description", "assigned_to", "due_date", "priority", "status", "project"}
    for field, value in data.items():
        if field in allowed_fields:
            setattr(task, field, value)

    task.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "due_date": task.due_date,
        "priority": task.priority,
        "status": task.status,
        "project": task.project,
        "created_by_agent": task.created_by_agent,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }
