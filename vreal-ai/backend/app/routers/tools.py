from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db, async_session
from app.models.tools import AITool, DEFAULT_TOOLS, MAKE_SCENARIOS
from app.models.agent import Agent

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
async def list_tools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AITool).order_by(AITool.category, AITool.name))
    tools = result.scalars().all()
    out = []
    for t in tools:
        agent = await db.get(Agent, t.managed_by) if t.managed_by else None
        out.append({
            "id": t.id, "name": t.name, "category": t.category,
            "description": t.description, "website": t.website,
            "icon": t.icon, "status": t.status,
            "managed_by": t.managed_by,
            "managed_by_name": agent.name if agent else "",
            "api_key_env": t.api_key_env,
            "make_webhook": t.make_webhook,
            "config": t.config,
        })
    return out


@router.get("/scenarios")
async def list_scenarios():
    return MAKE_SCENARIOS


@router.get("/by-category")
async def tools_by_category(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AITool).order_by(AITool.name))
    tools = result.scalars().all()
    categories = {}
    for t in tools:
        if t.category not in categories:
            categories[t.category] = []
        categories[t.category].append({
            "id": t.id, "name": t.name, "icon": t.icon,
            "description": t.description, "status": t.status,
            "website": t.website, "managed_by": t.managed_by,
        })
    return categories


async def init_tools():
    """Seed default AI tools into the database."""
    async with async_session() as db:
        result = await db.execute(select(AITool))
        existing = {t.name for t in result.scalars().all()}

        for tool_def in DEFAULT_TOOLS:
            if tool_def["name"] not in existing:
                db.add(AITool(
                    id=str(uuid.uuid4()),
                    name=tool_def["name"],
                    category=tool_def["category"],
                    description=tool_def.get("description", ""),
                    website=tool_def.get("website", ""),
                    api_key_env=tool_def.get("api_key_env", ""),
                    icon=tool_def.get("icon", ""),
                    status=tool_def.get("status", "pending_setup"),
                    managed_by=tool_def.get("managed_by", ""),
                    config=tool_def.get("config", {}),
                ))

        await db.commit()
        total = (await db.execute(select(AITool))).scalars().all()
        print(f"[TOOLS] {len(total)} AI tools registered")
