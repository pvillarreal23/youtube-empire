from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.agent import Agent
from app.schemas.agent import AgentOut, AgentDetail

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=list[AgentOut])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent))
    return list(result.scalars().all())


@router.get("/{agent_id}", response_model=AgentDetail)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/org/tree")
async def get_org_tree(db: AsyncSession = Depends(get_db)):
    """Return the full org tree structure for visualization."""
    result = await db.execute(select(Agent))
    agents = list(result.scalars().all())

    nodes = []
    edges = []
    for a in agents:
        nodes.append({
            "id": a.id,
            "name": a.name,
            "role": a.role,
            "department": a.department,
            "color": a.avatar_color,
        })
        if a.reports_to:
            edges.append({"source": a.reports_to, "target": a.id})

    return {"nodes": nodes, "edges": edges}
