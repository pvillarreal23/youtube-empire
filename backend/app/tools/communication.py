"""Communication tools: notifications and inter-agent messaging."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.thread import Thread, Message
from app.tools.registry import tool


@tool(
    id="send_notification",
    name="Send Notification",
    description="Send a structured notification to one or more agents by creating a new thread or adding to an existing one. Use this for formal communications, escalations, or delegations.",
    category="communication",
    input_schema={
        "type": "object",
        "properties": {
            "recipient_agent_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of agent IDs to notify",
            },
            "subject": {"type": "string", "description": "Subject of the notification"},
            "message": {"type": "string", "description": "The notification message content"},
            "priority": {
                "type": "string",
                "enum": ["normal", "urgent"],
                "description": "Priority level of the notification",
                "default": "normal",
            },
            "thread_id": {
                "type": "string",
                "description": "Optional existing thread ID to add the notification to. If omitted, creates a new thread.",
            },
        },
        "required": ["recipient_agent_ids", "subject", "message"],
    },
)
async def send_notification(
    recipient_agent_ids: list[str],
    subject: str,
    message: str,
    priority: str = "normal",
    thread_id: str | None = None,
    *,
    agent_id: str,
    db: AsyncSession,
    **kwargs,
) -> dict:
    if priority == "urgent":
        subject = f"[URGENT] {subject}"

    if thread_id:
        # Add to existing thread
        thread = await db.get(Thread, thread_id)
        if not thread:
            return {"error": f"Thread {thread_id} not found", "success": False}
        # Update participants
        participants = thread.participants or []
        for rid in recipient_agent_ids:
            if rid not in participants:
                participants.append(rid)
        thread.participants = participants
        thread.updated_at = datetime.now(timezone.utc)
    else:
        # Create new thread
        thread_id = str(uuid.uuid4())
        thread = Thread(
            id=thread_id,
            subject=subject,
            participants=recipient_agent_ids,
        )
        db.add(thread)

    msg = Message(
        id=str(uuid.uuid4()),
        thread_id=thread_id,
        sender_type="agent",
        sender_agent_id=agent_id,
        content=message,
        status="complete",
    )
    db.add(msg)
    await db.commit()

    return {
        "thread_id": thread_id,
        "message_id": msg.id,
        "recipients": recipient_agent_ids,
        "priority": priority,
        "success": True,
        "message": f"Notification sent to {len(recipient_agent_ids)} agent(s): {subject}",
    }
