from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, async_session
from app.models.automation import WorkflowRun
from app.schemas.automation import WorkflowInfo, RunWorkflowRequest, WorkflowRunOut
from app.services.managed_agents import (
    list_workflows,
    list_channels,
    run_workflow_session,
    stream_session_events,
    WORKFLOWS,
)

router = APIRouter(prefix="/api/automation", tags=["automation"])


# ---------------------------------------------------------------------------
# Workflow metadata
# ---------------------------------------------------------------------------

@router.get("/workflows", response_model=list[WorkflowInfo])
async def get_workflows():
    """List all available automation workflows."""
    return list_workflows()


@router.get("/channels")
async def get_channels():
    """List available YouTube channels."""
    return list_channels()


# ---------------------------------------------------------------------------
# Run a workflow
# ---------------------------------------------------------------------------

async def _execute_workflow(run_id: str, workflow_id: str, channel: str | None):
    """Background task: run the managed agent session and collect output."""
    async with async_session() as db:
        run = await db.get(WorkflowRun, run_id)
        if not run:
            return

        try:
            session_id, agent_name = run_workflow_session(workflow_id, channel)
            run.session_id = session_id
            await db.commit()

            output_parts: list[str] = []
            for event in stream_session_events(session_id):
                text = event.get("text", "")
                if text:
                    output_parts.append(text)

                # Periodically save progress
                if len(output_parts) % 10 == 0:
                    run.output = "".join(output_parts)
                    await db.commit()

            run.output = "".join(output_parts)
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)

        except Exception as e:
            run.status = "failed"
            run.output = f"Error: {str(e)}"
            run.completed_at = datetime.now(timezone.utc)

        await db.commit()


@router.post("/run/{workflow_id}")
async def run_workflow(
    workflow_id: str,
    data: RunWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a workflow. Returns the run ID immediately; work happens in background."""
    if workflow_id not in WORKFLOWS:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")

    wf = WORKFLOWS[workflow_id]
    channel = data.channel

    # Validate channel for channel-specific workflows
    if wf["channel_specific"] and not channel:
        channel = "ai-tech"  # default to first channel

    run = WorkflowRun(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        channel=channel,
        status="running",
    )
    db.add(run)
    await db.commit()

    background_tasks.add_task(_execute_workflow, run.id, workflow_id, channel)

    return {
        "id": run.id,
        "workflow_id": workflow_id,
        "channel": channel,
        "status": "running",
    }


# ---------------------------------------------------------------------------
# Stream a running session
# ---------------------------------------------------------------------------

@router.get("/stream/{run_id}")
async def stream_run(run_id: str, db: AsyncSession = Depends(get_db)):
    """SSE stream of a running workflow's agent output."""
    run = await db.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if not run.session_id:
        raise HTTPException(status_code=400, detail="Session not started yet")

    def event_generator():
        try:
            for event in stream_session_events(run.session_id):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

@router.get("/history", response_model=list[WorkflowRunOut])
async def get_history(db: AsyncSession = Depends(get_db)):
    """List all workflow runs, newest first."""
    result = await db.execute(
        select(WorkflowRun).order_by(WorkflowRun.created_at.desc()).limit(50)
    )
    return list(result.scalars().all())


@router.get("/history/{run_id}", response_model=WorkflowRunOut)
async def get_run_detail(run_id: str, db: AsyncSession = Depends(get_db)):
    """Get full details of a workflow run including output."""
    run = await db.get(WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run
