"""API endpoints for dispatching agents to the Anthropic Managed Agents sandbox."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.config import MANAGED_AGENTS_ENABLED
from app.models.agent import Agent
from app.models.sandbox_task import SandboxTask
from app.schemas.sandbox_task import DispatchTask, SandboxTaskOut, SandboxTaskEvents

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])


async def _run_sandbox_task(task_id: str):
    """Background worker that dispatches an agent to the managed sandbox."""
    from app.database import async_session
    from app.services.managed_agents_service import dispatch_agent_task

    async with async_session() as db:
        task = await db.get(SandboxTask, task_id)
        if not task:
            return

        agent = await db.get(Agent, task.agent_id)
        if not agent:
            task.status = "failed"
            task.result = "Agent not found"
            await db.commit()
            return

        try:
            result = dispatch_agent_task(
                agent_name=agent.name,
                system_prompt=agent.system_prompt,
                task=task.task,
            )
            task.managed_agent_id = result["managed_agent_id"]
            task.environment_id = result["environment_id"]
            task.session_id = result["session_id"]
            task.status = "running"
            task.updated_at = datetime.now(timezone.utc)
            await db.commit()
        except Exception as e:
            task.status = "failed"
            task.result = str(e)[:500]
            task.updated_at = datetime.now(timezone.utc)
            await db.commit()


@router.post("/dispatch", response_model=SandboxTaskOut)
async def dispatch_to_sandbox(
    data: DispatchTask,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Dispatch an agent to the Anthropic sandbox for an autonomous task."""
    if not MANAGED_AGENTS_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Managed Agents sandbox is not enabled. Set MANAGED_AGENTS_ENABLED=true.",
        )

    # Verify the agent exists locally
    agent = await db.get(Agent, data.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {data.agent_id} not found")

    # Create the task record
    task = SandboxTask(
        id=str(uuid.uuid4()),
        agent_id=data.agent_id,
        task=data.task,
        status="pending",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Dispatch in background so the API responds immediately
    background_tasks.add_task(_run_sandbox_task, task.id)

    return task


@router.get("/tasks", response_model=list[SandboxTaskOut])
async def list_sandbox_tasks(db: AsyncSession = Depends(get_db)):
    """List all sandbox tasks, newest first."""
    result = await db.execute(
        select(SandboxTask).order_by(SandboxTask.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/tasks/{task_id}", response_model=SandboxTaskOut)
async def get_sandbox_task(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific sandbox task by ID."""
    task = await db.get(SandboxTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Sandbox task not found")
    return task


@router.get("/tasks/{task_id}/events", response_model=SandboxTaskEvents)
async def get_sandbox_task_events(task_id: str, db: AsyncSession = Depends(get_db)):
    """Get live events from a running sandbox session."""
    task = await db.get(SandboxTask, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Sandbox task not found")

    if not task.session_id:
        raise HTTPException(status_code=400, detail="Task has no active session yet")

    from app.services.managed_agents_service import get_session_events, get_session_status

    try:
        status = get_session_status(task.session_id)
        events = get_session_events(task.session_id)

        # Update local status if session is done
        if status in ("idle", "terminated") and task.status == "running":
            task.status = "completed"
            # Collect agent message texts as result
            texts = [e["text"] for e in events if e.get("text") and e["type"] == "agent.message"]
            if texts:
                task.result = "\n\n".join(texts)
            task.updated_at = datetime.now(timezone.utc)
            await db.commit()

        return {"session_id": task.session_id, "status": status, "events": events}
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error fetching session events: {str(e)[:300]}")


@router.get("/tasks/agent/{agent_id}", response_model=list[SandboxTaskOut])
async def list_agent_sandbox_tasks(agent_id: str, db: AsyncSession = Depends(get_db)):
    """List all sandbox tasks for a specific agent."""
    result = await db.execute(
        select(SandboxTask)
        .where(SandboxTask.agent_id == agent_id)
        .order_by(SandboxTask.created_at.desc())
    )
    return list(result.scalars().all())
