from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.thread import Thread, Message
from app.models.agent import Agent
from app.models.tool import ToolCall
from app.schemas.thread import ThreadOut, ThreadWithMessages, CreateThread, SendMessage, MessageOut, ToolCallOut
from app.services.claude_service import generate_agent_response, analyze_routing
from app.config import MAX_AGENTS_PER_TURN

router = APIRouter(prefix="/api/threads", tags=["threads"])


async def _get_thread_messages(db: AsyncSession, thread_id: str) -> list[dict]:
    result = await db.execute(
        select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
    )
    messages = list(result.scalars().all())
    out = []
    for m in messages:
        agent = await db.get(Agent, m.sender_agent_id) if m.sender_agent_id else None

        # Load tool call details if present
        tool_calls_data = None
        if m.tool_calls:
            tool_calls_data = []
            for tc_id in m.tool_calls:
                tc = await db.get(ToolCall, tc_id)
                if tc:
                    tool_calls_data.append({
                        "id": tc.id,
                        "tool_name": tc.tool_name,
                        "input_data": tc.input_data or {},
                        "output_data": tc.output_data,
                        "status": tc.status,
                        "error_message": tc.error_message,
                        "created_at": tc.created_at.isoformat() if tc.created_at else None,
                        "completed_at": tc.completed_at.isoformat() if tc.completed_at else None,
                    })

        out.append({
            "id": m.id,
            "thread_id": m.thread_id,
            "sender_type": m.sender_type,
            "sender_agent_id": m.sender_agent_id,
            "sender_name": agent.name if agent else None,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "status": m.status,
            "message_type": m.message_type or "text",
            "tool_calls": tool_calls_data,
        })
    return out


async def _process_agent_response(thread_id: str, agent_id: str, depth: int = 0):
    """Generate an agent response and optionally route to other agents."""
    from app.database import async_session

    async with async_session() as db:
        agent = await db.get(Agent, agent_id)
        if not agent:
            return

        thread_msgs = await _get_thread_messages(db, thread_id)

        try:
            response = await generate_agent_response(
                system_prompt=agent.system_prompt,
                thread_messages=thread_msgs,
                agent_id=agent_id,
                agent_tools=agent.tools or None,
                thread_id=thread_id,
                db=db,
            )
        except Exception as e:
            # Save error message
            error_msg = Message(
                id=str(uuid.uuid4()),
                thread_id=thread_id,
                sender_type="agent",
                sender_agent_id=agent_id,
                content=f"[Error generating response: {str(e)[:200]}]",
                status="failed",
            )
            db.add(error_msg)
            await db.commit()
            return

        # Collect tool call IDs
        tool_call_ids = [tc["tool_call_id"] for tc in response.tool_calls] if response.tool_calls else None

        # Save agent response
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread_id,
            sender_type="agent",
            sender_agent_id=agent_id,
            content=response.text,
            status="complete",
            tool_calls=tool_call_ids,
        )
        db.add(msg)

        # Update tool call records with the message_id
        if tool_call_ids:
            for tc_id in tool_call_ids:
                tc = await db.get(ToolCall, tc_id)
                if tc:
                    tc.message_id = msg.id

        # Update thread
        thread = await db.get(Thread, thread_id)
        if thread:
            participants = thread.participants or []
            if agent_id not in participants:
                thread.participants = participants + [agent_id]
            thread.updated_at = datetime.now(timezone.utc)

        await db.commit()

        # Route to other agents if within depth limit
        if depth < MAX_AGENTS_PER_TURN:
            all_agents_result = await db.execute(select(Agent))
            all_agents = {a.id: a.name for a in all_agents_result.scalars().all()}

            routed = await analyze_routing(
                agent_name=agent.name,
                agent_role=agent.role,
                response_text=response.text,
                reports_to=agent.reports_to,
                direct_reports=agent.direct_reports or [],
                collaborates_with=agent.collaborates_with or [],
                all_agent_names=all_agents,
            )

            # Filter out agents that already responded in this thread
            existing_senders = {m["sender_agent_id"] for m in thread_msgs if m["sender_agent_id"]}
            routed = [r for r in routed if r not in existing_senders and r != agent_id]

            for next_agent_id in routed[:2]:  # Max 2 routed agents per hop
                await _process_agent_response(thread_id, next_agent_id, depth + 1)


@router.get("", response_model=list[ThreadOut])
async def list_threads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Thread).order_by(Thread.updated_at.desc()))
    return list(result.scalars().all())


@router.get("/{thread_id}")
async def get_thread(thread_id: str, db: AsyncSession = Depends(get_db)):
    thread = await db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    messages = await _get_thread_messages(db, thread_id)

    return {
        "id": thread.id,
        "subject": thread.subject,
        "created_at": thread.created_at,
        "updated_at": thread.updated_at,
        "status": thread.status,
        "participants": thread.participants or [],
        "messages": messages,
    }


@router.post("", response_model=ThreadOut)
async def create_thread(
    data: CreateThread,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Validate agents exist
    for aid in data.recipient_agent_ids:
        agent = await db.get(Agent, aid)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {aid} not found")

    thread = Thread(
        id=str(uuid.uuid4()),
        subject=data.subject,
        participants=data.recipient_agent_ids,
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

    # Queue agent responses
    for aid in data.recipient_agent_ids:
        background_tasks.add_task(_process_agent_response, thread.id, aid, 0)

    return thread


@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: str,
    data: SendMessage,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    thread = await db.get(Thread, thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    msg = Message(
        id=str(uuid.uuid4()),
        thread_id=thread_id,
        sender_type="user",
        sender_agent_id=None,
        content=data.content,
    )
    db.add(msg)
    thread.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Determine which agents should respond
    recipients = data.recipient_agent_ids or thread.participants or []
    for aid in recipients:
        background_tasks.add_task(_process_agent_response, thread_id, aid, 0)

    return {"status": "sent", "message_id": msg.id}
