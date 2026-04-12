"""Sync registered tools to the database at startup."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.models.tool import ToolDefinition, AgentToolPermission
from app.models.agent import Agent
from app.tools import get_all_tools


async def sync_tools_to_db(session: AsyncSession) -> None:
    """Upsert all registered tools and sync agent-tool permissions."""
    for handler in get_all_tools():
        existing = await session.get(ToolDefinition, handler.id)
        if existing:
            existing.name = handler.name
            existing.description = handler.description
            existing.category = handler.category
            existing.input_schema = handler.input_schema
            existing.handler_module = f"{handler.handler.__module__}.{handler.handler.__qualname__}"
            existing.requires_approval = handler.requires_approval
            existing.enabled = True
        else:
            session.add(ToolDefinition(
                id=handler.id,
                name=handler.name,
                description=handler.description,
                category=handler.category,
                input_schema=handler.input_schema,
                handler_module=f"{handler.handler.__module__}.{handler.handler.__qualname__}",
                requires_approval=handler.requires_approval,
            ))

    # Sync agent-tool permissions from Agent.tools field
    await session.execute(delete(AgentToolPermission))
    result = await session.execute(select(Agent))
    for agent in result.scalars().all():
        for tool_id in (agent.tools or []):
            session.add(AgentToolPermission(
                agent_id=agent.id,
                tool_id=tool_id,
            ))

    await session.commit()
