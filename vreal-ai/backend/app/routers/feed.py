from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, async_session
from app.models.feed import FeedMessage, FEED_CHANNELS
from app.models.agent import Agent

router = APIRouter(prefix="/api/feed", tags=["feed"])


class PostMessage(BaseModel):
    content: str
    channel: str = "general"
    message_type: str = "update"
    severity: str = "info"


@router.get("/channels")
async def list_channels():
    return FEED_CHANNELS


@router.get("/messages")
async def get_messages(
    channel: str = "all",
    limit: int = 50,
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = select(FeedMessage).order_by(FeedMessage.created_at.desc()).limit(limit)
    if channel != "all":
        query = query.where(FeedMessage.channel == channel)
    if unread_only:
        query = query.where(FeedMessage.read == False)

    result = await db.execute(query)
    messages = result.scalars().all()

    out = []
    for m in messages:
        agent = await db.get(Agent, m.agent_id)
        out.append({
            "id": m.id,
            "agent_id": m.agent_id,
            "agent_name": agent.name if agent else m.agent_id,
            "agent_color": agent.avatar_color if agent else "#6366f1",
            "channel": m.channel,
            "content": m.content,
            "message_type": m.message_type,
            "severity": m.severity,
            "thread_id": m.thread_id,
            "pinned": m.pinned,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "read": m.read,
        })
    return out


@router.get("/unread_count")
async def unread_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(func.count()).select_from(FeedMessage).where(FeedMessage.read == False)
    )
    count = result.scalar() or 0

    # Per channel counts
    channel_counts = {}
    for ch in FEED_CHANNELS:
        r = await db.execute(
            select(func.count()).select_from(FeedMessage)
            .where(FeedMessage.read == False, FeedMessage.channel == ch)
        )
        c = r.scalar() or 0
        if c > 0:
            channel_counts[ch] = c

    return {"total": count, "channels": channel_counts}


@router.post("/messages/{message_id}/read")
async def mark_read(message_id: str, db: AsyncSession = Depends(get_db)):
    msg = await db.get(FeedMessage, message_id)
    if msg:
        msg.read = True
        await db.commit()
    return {"status": "ok"}


@router.post("/mark_all_read")
async def mark_all_read(channel: str = "all", db: AsyncSession = Depends(get_db)):
    query = select(FeedMessage).where(FeedMessage.read == False)
    if channel != "all":
        query = query.where(FeedMessage.channel == channel)
    result = await db.execute(query)
    for msg in result.scalars().all():
        msg.read = True
    await db.commit()
    return {"status": "ok"}


@router.post("/send")
async def post_to_feed(data: PostMessage, db: AsyncSession = Depends(get_db)):
    """Pedro can post messages to the feed for agents to see."""
    msg = FeedMessage(
        id=str(uuid.uuid4()),
        agent_id="pedro",
        channel=data.channel,
        content=data.content,
        message_type=data.message_type,
        severity=data.severity,
    )
    db.add(msg)
    await db.commit()
    return {"id": msg.id, "status": "posted"}


# === Helper function for agents to post to the feed ===
async def agent_post(
    agent_id: str,
    content: str,
    channel: str = "general",
    message_type: str = "update",
    severity: str = "info",
    thread_id: Optional[str] = None,
):
    """Called by the scheduler/pipeline to post agent updates to the feed."""
    async with async_session() as db:
        msg = FeedMessage(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            channel=channel,
            content=content,
            message_type=message_type,
            severity=severity,
            thread_id=thread_id,
        )
        db.add(msg)
        await db.commit()
