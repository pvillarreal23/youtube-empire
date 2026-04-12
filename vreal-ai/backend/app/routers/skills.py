"""
Agent Skills & Growth API

Endpoints for viewing agent skill portfolios, leaderboards,
and tracking who's producing vs who's growing.
"""
from __future__ import annotations

from fastapi import APIRouter
from app.services.skill_growth import (
    get_agent_skill_portfolio,
    get_production_leaderboard,
    get_growth_leaderboard,
)

router = APIRouter(prefix="/api/skills", tags=["skills"])


@router.get("/agent/{agent_id}")
async def agent_skills(agent_id: str):
    """Get an agent's full skill portfolio — levels, XP, evidence, growth."""
    return await get_agent_skill_portfolio(agent_id)


@router.get("/leaderboard/production")
async def production_leaderboard():
    """Who's producing the most? Ranked by output volume and quality."""
    return await get_production_leaderboard()


@router.get("/leaderboard/growth")
async def growth_leaderboard():
    """Who's growing the fastest? Ranked by XP, skill levels, and improvement velocity."""
    return await get_growth_leaderboard()


@router.get("/leaderboard/combined")
async def combined_leaderboard():
    """Combined view: production output + skill growth for every agent."""
    production = await get_production_leaderboard()
    growth = await get_growth_leaderboard()

    # Merge by agent_id
    combined = {}
    for p in production:
        combined[p["agent_id"]] = {"production": p, "growth": None}
    for g in growth:
        if g["agent_id"] in combined:
            combined[g["agent_id"]]["growth"] = g
        else:
            combined[g["agent_id"]] = {"production": None, "growth": g}

    # Sort by total XP (growth) as primary, productions as secondary
    ranked = sorted(
        combined.items(),
        key=lambda x: (
            (x[1]["growth"] or {}).get("total_xp", 0),
            (x[1]["production"] or {}).get("total_productions", 0),
        ),
        reverse=True,
    )

    return [
        {
            "rank": i + 1,
            "agent_id": agent_id,
            **data,
        }
        for i, (agent_id, data) in enumerate(ranked)
    ]
