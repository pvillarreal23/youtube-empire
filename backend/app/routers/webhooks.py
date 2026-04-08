from __future__ import annotations

import uuid
import json
import hmac
import hashlib
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db, async_session
from app.models.thread import Thread, Message
from app.models.agent import Agent
from app.services.claude_service import generate_agent_response, analyze_routing
from app.config import WEBHOOK_SECRET, MAX_AGENTS_PER_TURN

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


# --- Schemas ---

class WebhookTrigger(BaseModel):
    """Incoming webhook from Make.com or any external service."""
    action: str  # "run_pipeline", "run_agent", "create_thread"
    topic: Optional[str] = None
    agent_ids: Optional[list[str]] = None
    content: Optional[str] = None
    callback_url: Optional[str] = None  # Make.com will poll or we push here


class PipelineStatus(BaseModel):
    pipeline_id: str
    status: str  # "running", "complete", "failed"
    thread_id: str
    results: Optional[dict] = None


# --- Webhook signature verification ---

def verify_signature(body: bytes, signature: str | None) -> bool:
    if not WEBHOOK_SECRET:
        return True  # No secret configured, allow all
    if not signature:
        return False
    expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


# --- Pipeline agents in order ---

CONTENT_PIPELINE_AGENTS = [
    "trend-researcher-agent",
    "senior-researcher-agent",
    "hook-specialist-agent",
    "scriptwriter-agent",
    "seo-specialist-agent",
    "thumbnail-designer-agent",
    "shorts-clips-agent",
    "social-media-manager-agent",
    "newsletter-strategist-agent",
    "qa-lead-agent",
]


async def _run_pipeline_sequential(thread_id: str, agent_ids: list[str], callback_url: str | None):
    """Run agents sequentially so each builds on the previous output."""
    async with async_session() as db:
        for agent_id in agent_ids:
            agent = await db.get(Agent, agent_id)
            if not agent:
                continue

            # Get all messages so far (includes previous agent outputs)
            result = await db.execute(
                select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
            )
            messages = list(result.scalars().all())
            thread_msgs = []
            for m in messages:
                sender_agent = await db.get(Agent, m.sender_agent_id) if m.sender_agent_id else None
                thread_msgs.append({
                    "id": m.id,
                    "thread_id": m.thread_id,
                    "sender_type": m.sender_type,
                    "sender_agent_id": m.sender_agent_id,
                    "sender_name": sender_agent.name if sender_agent else None,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "status": m.status,
                })

            try:
                response_text = generate_agent_response(
                    system_prompt=agent.system_prompt,
                    thread_messages=thread_msgs,
                    agent_id=agent_id,
                )
            except Exception as e:
                error_msg = Message(
                    id=str(uuid.uuid4()),
                    thread_id=thread_id,
                    sender_type="agent",
                    sender_agent_id=agent_id,
                    content=f"[Error: {str(e)[:200]}]",
                    status="failed",
                )
                db.add(error_msg)
                await db.commit()
                continue

            msg = Message(
                id=str(uuid.uuid4()),
                thread_id=thread_id,
                sender_type="agent",
                sender_agent_id=agent_id,
                content=response_text,
                status="complete",
            )
            db.add(msg)

            thread = await db.get(Thread, thread_id)
            if thread:
                participants = thread.participants or []
                if agent_id not in participants:
                    thread.participants = participants + [agent_id]
                thread.updated_at = datetime.now(timezone.utc)

            await db.commit()

        # Mark thread complete
        thread = await db.get(Thread, thread_id)
        if thread:
            thread.status = "complete"
            thread.updated_at = datetime.now(timezone.utc)
            await db.commit()

        # Push results to callback URL if provided (Make.com webhook response)
        if callback_url:
            import httpx
            result = await db.execute(
                select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
            )
            all_msgs = list(result.scalars().all())
            payload = {
                "pipeline_id": thread_id,
                "status": "complete",
                "thread_id": thread_id,
                "results": {
                    m.sender_agent_id: m.content
                    for m in all_msgs if m.sender_type == "agent" and m.status == "complete"
                },
            }
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(callback_url, json=payload, timeout=30)
            except Exception:
                pass


# --- Endpoints ---

@router.post("/trigger")
async def webhook_trigger(
    data: WebhookTrigger,
    background_tasks: BackgroundTasks,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Main webhook endpoint for Make.com and external services.

    Actions:
    - "run_pipeline": Full content pipeline (topic -> research -> script -> SEO -> everything)
    - "run_agent": Run specific agent(s) with a prompt
    - "create_thread": Create a thread and let agents auto-route
    """
    # Verify webhook signature
    body = await request.body()
    if not verify_signature(body, x_webhook_signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if data.action == "run_pipeline":
        if not data.topic:
            raise HTTPException(status_code=400, detail="topic is required for run_pipeline")

        # Create thread with pipeline prompt
        thread = Thread(
            id=str(uuid.uuid4()),
            subject=f"Pipeline: {data.topic}",
            participants=CONTENT_PIPELINE_AGENTS,
            status="running",
        )
        db.add(thread)

        prompt = (
            f"Create a complete video package for V-Real AI on this topic: {data.topic}\n\n"
            f"Each agent should build on the previous agents' work. "
            f"Trend Researcher: find the angle and timing. "
            f"Senior Researcher: deep research with sources. "
            f"Hook Specialist: 3 hook options. "
            f"Scriptwriter: full script with visual cues. "
            f"SEO Specialist: title, description, tags, chapters. "
            f"Thumbnail Designer: 3 thumbnail concepts. "
            f"Shorts & Clips: 3 shorts scripts. "
            f"Social Media Manager: cross-platform posts. "
            f"Newsletter Strategist: email draft."
        )

        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            sender_type="user",
            sender_agent_id=None,
            content=prompt,
        )
        db.add(msg)
        await db.commit()

        background_tasks.add_task(
            _run_pipeline_sequential,
            thread.id,
            CONTENT_PIPELINE_AGENTS,
            data.callback_url,
        )

        return {
            "status": "running",
            "pipeline_id": thread.id,
            "thread_id": thread.id,
            "agents": CONTENT_PIPELINE_AGENTS,
            "message": f"Pipeline started for: {data.topic}",
        }

    elif data.action == "run_agent":
        if not data.agent_ids or not data.content:
            raise HTTPException(status_code=400, detail="agent_ids and content required for run_agent")

        # Validate agents
        for aid in data.agent_ids:
            agent = await db.get(Agent, aid)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {aid} not found")

        thread = Thread(
            id=str(uuid.uuid4()),
            subject=f"Agent task: {data.content[:50]}",
            participants=data.agent_ids,
        )
        db.add(thread)

        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            sender_type="user",
            sender_agent_id=None,
            content=data.content,
        )
        db.add(msg)
        await db.commit()

        background_tasks.add_task(
            _run_pipeline_sequential,
            thread.id,
            data.agent_ids,
            data.callback_url,
        )

        return {
            "status": "running",
            "thread_id": thread.id,
            "agents": data.agent_ids,
        }

    elif data.action == "create_thread":
        if not data.agent_ids or not data.content:
            raise HTTPException(status_code=400, detail="agent_ids and content required for create_thread")

        # This uses the original auto-routing logic
        for aid in data.agent_ids:
            agent = await db.get(Agent, aid)
            if not agent:
                raise HTTPException(status_code=404, detail=f"Agent {aid} not found")

        thread = Thread(
            id=str(uuid.uuid4()),
            subject=data.topic or data.content[:50],
            participants=data.agent_ids,
        )
        db.add(thread)

        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            sender_type="user",
            sender_agent_id=None,
            content=data.content,
        )
        db.add(msg)
        await db.commit()

        from app.routers.threads import _process_agent_response
        for aid in data.agent_ids:
            background_tasks.add_task(_process_agent_response, thread.id, aid, 0)

        return {
            "status": "running",
            "thread_id": thread.id,
            "agents": data.agent_ids,
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {data.action}")


@router.get("/pipeline/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str, db: AsyncSession = Depends(get_db)):
    """Check the status of a running pipeline. Make.com can poll this."""
    thread = await db.get(Thread, pipeline_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    result = await db.execute(
        select(Message).where(Message.thread_id == pipeline_id).order_by(Message.created_at)
    )
    messages = list(result.scalars().all())

    agent_results = {}
    for m in messages:
        if m.sender_type == "agent" and m.status == "complete":
            agent_results[m.sender_agent_id] = m.content

    completed_agents = list(agent_results.keys())
    pending_agents = [a for a in (thread.participants or []) if a not in completed_agents]

    return {
        "pipeline_id": pipeline_id,
        "status": thread.status,
        "thread_id": pipeline_id,
        "completed_agents": completed_agents,
        "pending_agents": pending_agents,
        "results": agent_results,
    }


@router.get("/agents")
async def list_available_agents(db: AsyncSession = Depends(get_db)):
    """List agents available for webhook triggers. Useful for Make.com dropdowns."""
    result = await db.execute(select(Agent))
    agents = list(result.scalars().all())
    return [
        {"id": a.id, "name": a.name, "role": a.role, "department": a.department}
        for a in agents
    ]
