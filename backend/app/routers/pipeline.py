from __future__ import annotations

import uuid
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db, async_session
from app.models.thread import Thread, Message
from app.models.agent import Agent
from app.services.claude_service import generate_agent_response
from app.routers.webhooks import _run_pipeline_sequential, CONTENT_PIPELINE_AGENTS

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class AutopilotConfig(BaseModel):
    channel: str = "V-Real AI"
    niche: str = "AI agents, automation, and building income with AI"
    num_ideas: int = 3


# --- Autopilot: Trend Research -> Pick Best -> Run Full Pipeline ---

async def _run_autopilot(config: AutopilotConfig, callback_url: str | None = None):
    """
    Full autopilot pipeline:
    1. Trend Researcher finds top ideas
    2. Content VP picks the best one
    3. Full content pipeline runs on the winning topic
    """
    async with async_session() as db:
        # Step 1: Trend Researcher finds ideas
        thread = Thread(
            id=str(uuid.uuid4()),
            subject=f"Autopilot: {config.channel} — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            participants=["trend-researcher-agent", "content-vp-agent"] + CONTENT_PIPELINE_AGENTS,
            status="running",
        )
        db.add(thread)

        discovery_prompt = (
            f"You are scanning for the next video topic for {config.channel}.\n\n"
            f"Channel niche: {config.niche}\n\n"
            f"Find the top {config.num_ideas} video opportunities right now. For each:\n"
            f"1. Topic/title idea\n"
            f"2. Why NOW (what's trending, what just happened, what's about to change)\n"
            f"3. Target keyword and estimated search demand\n"
            f"4. Urgency score (1-10)\n"
            f"5. Unique angle competitors haven't covered\n\n"
            f"Focus on topics that are timely, searchable, and would resonate with people "
            f"who want to use AI to build income and escape the 9-to-5."
        )

        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            sender_type="user",
            sender_agent_id=None,
            content=discovery_prompt,
        )
        db.add(msg)
        await db.commit()

        # Run Trend Researcher
        trend_agent = await db.get(Agent, "trend-researcher-agent")
        if not trend_agent:
            return

        try:
            trend_response = generate_agent_response(
                system_prompt=trend_agent.system_prompt,
                thread_messages=[{
                    "id": msg.id, "thread_id": thread.id, "sender_type": "user",
                    "sender_agent_id": None, "sender_name": None,
                    "content": discovery_prompt, "created_at": msg.created_at.isoformat(),
                    "status": "sent",
                }],
                agent_id="trend-researcher-agent",
            )
        except Exception as e:
            error = Message(
                id=str(uuid.uuid4()), thread_id=thread.id, sender_type="agent",
                sender_agent_id="trend-researcher-agent",
                content=f"[Error: {str(e)[:200]}]", status="failed",
            )
            db.add(error)
            thread.status = "failed"
            await db.commit()
            return

        trend_msg = Message(
            id=str(uuid.uuid4()), thread_id=thread.id, sender_type="agent",
            sender_agent_id="trend-researcher-agent",
            content=trend_response, status="complete",
        )
        db.add(trend_msg)
        thread.updated_at = datetime.now(timezone.utc)
        await db.commit()

        # Step 2: Content VP picks the best topic
        content_vp = await db.get(Agent, "content-vp-agent")
        if not content_vp:
            return

        pick_prompt = (
            f"The Trend Researcher found these opportunities:\n\n{trend_response}\n\n"
            f"Pick the BEST one for this week's video. Consider:\n"
            f"- Urgency (will this still be relevant next week?)\n"
            f"- Search demand\n"
            f"- Fit for {config.channel}\n"
            f"- Unique angle potential\n\n"
            f"Respond with ONLY:\n"
            f"SELECTED TOPIC: [the exact topic]\n"
            f"REASON: [one sentence why]\n"
            f"ANGLE: [the specific angle to take]"
        )

        thread_msgs = [
            {
                "id": msg.id, "thread_id": thread.id, "sender_type": "user",
                "sender_agent_id": None, "sender_name": None,
                "content": discovery_prompt, "created_at": msg.created_at.isoformat(),
                "status": "sent",
            },
            {
                "id": trend_msg.id, "thread_id": thread.id, "sender_type": "agent",
                "sender_agent_id": "trend-researcher-agent", "sender_name": "Trend Researcher Agent",
                "content": trend_response, "created_at": trend_msg.created_at.isoformat(),
                "status": "complete",
            },
            {
                "id": str(uuid.uuid4()), "thread_id": thread.id, "sender_type": "user",
                "sender_agent_id": None, "sender_name": None,
                "content": pick_prompt, "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "sent",
            },
        ]

        # Save the pick prompt as a message
        pick_msg = Message(
            id=str(uuid.uuid4()), thread_id=thread.id, sender_type="user",
            sender_agent_id=None, content=pick_prompt,
        )
        db.add(pick_msg)
        await db.commit()

        try:
            vp_response = generate_agent_response(
                system_prompt=content_vp.system_prompt,
                thread_messages=thread_msgs,
                agent_id="content-vp-agent",
            )
        except Exception as e:
            error = Message(
                id=str(uuid.uuid4()), thread_id=thread.id, sender_type="agent",
                sender_agent_id="content-vp-agent",
                content=f"[Error: {str(e)[:200]}]", status="failed",
            )
            db.add(error)
            thread.status = "failed"
            await db.commit()
            return

        vp_msg = Message(
            id=str(uuid.uuid4()), thread_id=thread.id, sender_type="agent",
            sender_agent_id="content-vp-agent",
            content=vp_response, status="complete",
        )
        db.add(vp_msg)
        await db.commit()

        # Step 3: Run the full content pipeline with the selected topic
        pipeline_prompt = (
            f"Content VP has selected this topic for V-Real AI:\n\n{vp_response}\n\n"
            f"Trend Researcher's full research:\n{trend_response}\n\n"
            f"Each agent should now do their part to create a complete video package. "
            f"Build on each other's work."
        )

        pipeline_msg = Message(
            id=str(uuid.uuid4()), thread_id=thread.id, sender_type="user",
            sender_agent_id=None, content=pipeline_prompt,
        )
        db.add(pipeline_msg)
        await db.commit()

    # Run remaining pipeline agents (skip trend researcher, already done)
    remaining_agents = [a for a in CONTENT_PIPELINE_AGENTS if a not in ("trend-researcher-agent",)]
    await _run_pipeline_sequential(thread.id, remaining_agents, callback_url)


@router.post("/autopilot")
async def start_autopilot(
    config: AutopilotConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Start the full autopilot pipeline.
    Trend Researcher finds topics -> Content VP picks best -> Full pipeline runs.

    Call this from Make.com on a daily schedule, or manually from the dashboard.
    """
    background_tasks.add_task(_run_autopilot, config)
    return {
        "status": "started",
        "message": f"Autopilot pipeline started for {config.channel}",
    }


@router.get("/history")
async def pipeline_history(db: AsyncSession = Depends(get_db)):
    """List all pipeline runs."""
    result = await db.execute(
        select(Thread)
        .where(Thread.subject.like("Pipeline:%") | Thread.subject.like("Autopilot:%"))
        .order_by(Thread.created_at.desc())
    )
    threads = list(result.scalars().all())
    return [
        {
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "agents_involved": t.participants or [],
        }
        for t in threads
    ]
