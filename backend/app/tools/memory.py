"""Memory tools: persistent agent state across conversations."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import AgentMemory
from app.tools.registry import tool


@tool(
    id="remember",
    name="Remember",
    description="Store a piece of information for future reference. Use this to save important facts, decisions, preferences, or task results that you may need later.",
    category="memory",
    input_schema={
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "A short label for this memory (e.g., 'preferred_upload_schedule', 'last_revenue_target')"},
            "value": {"description": "The information to store (can be any JSON value: string, number, object, array)"},
            "memory_type": {
                "type": "string",
                "enum": ["fact", "decision", "task_result", "preference"],
                "description": "Category of this memory",
                "default": "fact",
            },
        },
        "required": ["key", "value"],
    },
)
async def remember(
    key: str,
    value,
    memory_type: str = "fact",
    *,
    agent_id: str,
    db: AsyncSession,
    thread_id: str | None = None,
    **kwargs,
) -> dict:
    # Check if this key already exists for this agent — update if so
    result = await db.execute(
        select(AgentMemory).where(
            AgentMemory.agent_id == agent_id,
            AgentMemory.key == key,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.value = value
        existing.memory_type = memory_type
        existing.source_thread_id = thread_id
        existing.updated_at = datetime.now(timezone.utc)
        return {
            "memory_id": existing.id,
            "action": "updated",
            "key": key,
            "message": f"Memory updated: {key}",
        }
    else:
        memory = AgentMemory(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            memory_type=memory_type,
            key=key,
            value=value,
            source_thread_id=thread_id,
        )
        db.add(memory)
        await db.commit()
        return {
            "memory_id": memory.id,
            "action": "created",
            "key": key,
            "message": f"Memory stored: {key}",
        }


@tool(
    id="recall",
    name="Recall",
    description="Retrieve stored memories matching a query. Use this to look up previously saved facts, decisions, or task results.",
    category="memory",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search term to match against memory keys and values"},
            "memory_type": {
                "type": "string",
                "enum": ["fact", "decision", "task_result", "preference"],
                "description": "Filter by memory type (optional)",
            },
        },
        "required": ["query"],
    },
)
async def recall(
    query: str,
    memory_type: str | None = None,
    *,
    agent_id: str,
    db: AsyncSession,
    **kwargs,
) -> dict:
    stmt = select(AgentMemory).where(AgentMemory.agent_id == agent_id)
    if memory_type:
        stmt = stmt.where(AgentMemory.memory_type == memory_type)

    result = await db.execute(stmt)
    memories = list(result.scalars().all())

    # Filter by query substring match on key
    query_lower = query.lower()
    matches = []
    for m in memories:
        if query_lower in m.key.lower() or query_lower in str(m.value).lower():
            matches.append({
                "memory_id": m.id,
                "key": m.key,
                "value": m.value,
                "memory_type": m.memory_type,
                "updated_at": m.updated_at.isoformat() if m.updated_at else None,
            })

    return {
        "query": query,
        "total_matches": len(matches),
        "memories": matches[:20],
    }
