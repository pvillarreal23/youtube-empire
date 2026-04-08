from __future__ import annotations

import asyncio
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from app.services.team_collab import start_collaboration, COLLAB_TYPES, TEAM_MEETINGS

router = APIRouter(prefix="/api/collab", tags=["collaboration"])


class CollabRequest(BaseModel):
    collab_type: str  # brainstorm, review, handoff, standup, strategy
    initiator_id: str
    participant_ids: list
    topic: str
    context: str = ""


@router.get("/types")
async def list_types():
    return {k: {"desc": v["desc"], "max_rounds": v["max_rounds"]} for k, v in COLLAB_TYPES.items()}


@router.get("/meetings")
async def list_meetings():
    return TEAM_MEETINGS


@router.post("/start")
async def start_collab(data: CollabRequest, background_tasks: BackgroundTasks):
    """Start a collaboration session between agents."""
    async def _run():
        await start_collaboration(
            collab_type=data.collab_type,
            initiator_id=data.initiator_id,
            participant_ids=data.participant_ids,
            topic=data.topic,
            context=data.context,
        )
    background_tasks.add_task(_run)
    return {"status": "started", "type": data.collab_type, "topic": data.topic}


@router.post("/meetings/{meeting_id}/run")
async def run_meeting(meeting_id: str, background_tasks: BackgroundTasks):
    """Trigger a pre-defined team meeting."""
    meeting = TEAM_MEETINGS.get(meeting_id)
    if not meeting:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Meeting not found: {meeting_id}")

    async def _run():
        await start_collaboration(
            collab_type=meeting["type"],
            initiator_id=meeting["initiator"],
            participant_ids=meeting["participants"],
            topic=meeting["topic"],
        )
    background_tasks.add_task(_run)
    return {"status": "started", "meeting": meeting_id, "topic": meeting["topic"]}
