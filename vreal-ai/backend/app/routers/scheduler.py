from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.scheduler import ScheduledTask, TaskRun, Escalation
from app.models.agent import Agent
from app.services.scheduler import run_scheduled_task

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/tasks")
async def list_tasks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ScheduledTask).order_by(ScheduledTask.category))
    tasks = result.scalars().all()
    out = []
    for t in tasks:
        agent = await db.get(Agent, t.agent_id)
        out.append({
            "id": t.id,
            "agent_id": t.agent_id,
            "agent_name": agent.name if agent else t.agent_id,
            "name": t.name,
            "description": t.description,
            "prompt": t.prompt,
            "cron_expression": t.cron_expression,
            "enabled": t.enabled,
            "last_run": t.last_run.isoformat() if t.last_run else None,
            "category": t.category,
        })
    return out


@router.post("/tasks/{task_id}/toggle")
async def toggle_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await db.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.enabled = not task.enabled
    await db.commit()
    return {"id": task.id, "enabled": task.enabled}


@router.post("/tasks/{task_id}/run")
async def run_task_now(task_id: str, db: AsyncSession = Depends(get_db)):
    """Manually trigger a scheduled task immediately."""
    task = await db.get(ScheduledTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    # Run in background
    import asyncio
    asyncio.create_task(run_scheduled_task(task_id))
    return {"status": "triggered", "task": task.name}


@router.get("/runs")
async def list_runs(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TaskRun).order_by(TaskRun.started_at.desc()).limit(limit)
    )
    runs = result.scalars().all()
    out = []
    for r in runs:
        agent = await db.get(Agent, r.agent_id)
        out.append({
            "id": r.id,
            "scheduled_task_id": r.scheduled_task_id,
            "agent_id": r.agent_id,
            "agent_name": agent.name if agent else r.agent_id,
            "task_name": r.task_name,
            "status": r.status,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "summary": r.summary,
            "error": r.error,
            "thread_id": r.thread_id,
        })
    return out


@router.get("/activity")
async def get_activity(db: AsyncSession = Depends(get_db)):
    """Dashboard-friendly activity summary."""
    # Running tasks
    running_result = await db.execute(
        select(TaskRun).where(TaskRun.status == "running")
    )
    running = running_result.scalars().all()

    # Recent completed (last 20)
    recent_result = await db.execute(
        select(TaskRun).where(TaskRun.status.in_(["complete", "escalated", "failed"]))
        .order_by(TaskRun.completed_at.desc()).limit(20)
    )
    recent = recent_result.scalars().all()

    # Pending escalations
    esc_result = await db.execute(
        select(Escalation).where(Escalation.status == "pending")
    )
    escalations = esc_result.scalars().all()

    # Build agent status map
    all_agents_result = await db.execute(select(Agent))
    all_agents = all_agents_result.scalars().all()

    running_agent_ids = {r.agent_id for r in running}
    recent_agent_ids = {r.agent_id: r for r in recent}

    agent_statuses = []
    for a in all_agents:
        if a.id in running_agent_ids:
            run = next(r for r in running if r.agent_id == a.id)
            status = "working"
            task = run.task_name
        elif a.id in recent_agent_ids:
            run = recent_agent_ids[a.id]
            status = "idle"
            task = f"Last: {run.task_name}"
        else:
            status = "idle"
            task = "Awaiting tasks"

        agent_statuses.append({
            "id": a.id, "name": a.name, "role": a.role,
            "department": a.department, "avatar_color": a.avatar_color,
            "status": status, "current_task": task,
        })

    return {
        "running_count": len(running),
        "completed_today": len([r for r in recent if r.completed_at and r.completed_at.date() == datetime.now(timezone.utc).date()]),
        "pending_escalations": len(escalations),
        "total_agents": len(all_agents),
        "agent_statuses": agent_statuses,
        "recent_runs": [{
            "id": r.id, "agent_id": r.agent_id, "task_name": r.task_name,
            "status": r.status, "summary": r.summary,
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "thread_id": r.thread_id,
        } for r in recent[:10]],
        "escalations": [{
            "id": e.id, "agent_id": e.agent_id, "reason": e.reason,
            "severity": e.severity, "thread_id": e.thread_id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        } for e in escalations],
    }


# Escalation endpoints
@router.get("/escalations")
async def list_escalations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Escalation).order_by(Escalation.created_at.desc()).limit(50)
    )
    escalations = result.scalars().all()
    out = []
    for e in escalations:
        agent = await db.get(Agent, e.agent_id)
        out.append({
            "id": e.id, "thread_id": e.thread_id,
            "agent_id": e.agent_id, "agent_name": agent.name if agent else e.agent_id,
            "reason": e.reason, "severity": e.severity, "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
            "resolution_note": e.resolution_note,
        })
    return out


@router.post("/escalations/{escalation_id}/resolve")
async def resolve_escalation(escalation_id: str, db: AsyncSession = Depends(get_db)):
    esc = await db.get(Escalation, escalation_id)
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    esc.status = "resolved"
    esc.resolved_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": esc.id, "status": "resolved"}
