"""
Agent Skill Growth Engine

Automatically levels up agent skills based on real production work.
Tracks who's producing, who's growing, and generates leaderboards.
"""
from __future__ import annotations

import uuid
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select, func
from app.database import async_session
from app.models.skills import (
    AgentSkill, AgentProductionLog, AgentGrowthSnapshot,
    SKILL_LEVELS, STAGE_SKILLS,
)


# ═══════════════════════════════════════════════════════════════════
# SKILL FOLDER ON DISK — Physical files per agent
# ═══════════════════════════════════════════════════════════════════

SKILLS_BASE_DIR = Path(__file__).parent.parent.parent.parent.parent / "agents" / "vreal-ai"


def get_agent_skill_folder(agent_id: str) -> Path:
    """Get the physical skill folder path for an agent."""
    # Find the agent's tier folder
    for tier_dir in sorted(SKILLS_BASE_DIR.iterdir()):
        if not tier_dir.is_dir() or not tier_dir.name.startswith("tier-"):
            continue
        agent_file = tier_dir / f"{agent_id}.md"
        if agent_file.exists():
            skill_folder = tier_dir / "skills" / agent_id
            skill_folder.mkdir(parents=True, exist_ok=True)
            return skill_folder
    # Fallback — create under a general skills folder
    fallback = SKILLS_BASE_DIR / "skills" / agent_id
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def write_skill_file(agent_id: str, skill_name: str, level: int, xp: int,
                     description: str, evidence: list):
    """Write a physical skill file to the agent's skill folder."""
    folder = get_agent_skill_folder(agent_id)
    level_info = SKILL_LEVELS.get(level, SKILL_LEVELS[1])

    content = f"""# {skill_name.replace('-', ' ').title()}
**Level:** {level_info['icon']} {level_info['name']} (Level {level}/5)
**XP:** {xp}/{SKILL_LEVELS.get(level + 1, {}).get('xp_needed', 'MAX')}
**Category:** {description}

## Evidence
"""
    for e in evidence[-10:]:  # Last 10 pieces of evidence
        content += f"- **{e.get('episode', 'Unknown')}** — Score: {e.get('score', '?')}/10 ({e.get('date', '')})\n"

    if level >= 4:
        content += f"\n## Mastery Notes\nThis agent has demonstrated **expert-level** proficiency in {skill_name.replace('-', ' ')}.\n"
    if level >= 5:
        content += f"🔴 **MASTER LEVEL ACHIEVED** — This agent is a recognized master of {skill_name.replace('-', ' ')}.\n"

    filepath = folder / f"{skill_name}.md"
    filepath.write_text(content)
    return str(filepath)


# ═══════════════════════════════════════════════════════════════════
# SKILL GROWTH — Called after quality gates and pressure tests
# ═══════════════════════════════════════════════════════════════════

async def grant_xp(
    agent_id: str,
    stage: str,
    episode_title: str,
    score: int,
    passed_first_try: bool,
    pressure_test_passed: bool = False,
    attempts: int = 1,
):
    """
    Grant XP to an agent's skills based on work completed.

    XP Formula:
    - Base XP: 10 per quality gate attempt
    - First-try bonus: +20 XP
    - Score bonus: score * 2 XP
    - Pressure test pass: +30 XP
    - Revision penalty: -5 XP per extra attempt (still positive net)
    """
    stage_skills = STAGE_SKILLS.get(stage, [])
    if not stage_skills:
        return []

    base_xp = 10
    first_try_bonus = 20 if passed_first_try else 0
    score_bonus = score * 2
    pressure_bonus = 30 if pressure_test_passed else 0
    revision_penalty = max(0, (attempts - 1) * 5)
    total_xp = base_xp + first_try_bonus + score_bonus + pressure_bonus - revision_penalty
    total_xp = max(5, total_xp)  # Minimum 5 XP even for bad performance (they still learned)

    leveled_up = []

    async with async_session() as db:
        for skill_def in stage_skills:
            skill_name = skill_def["name"]

            # Find or create the skill
            result = await db.execute(
                select(AgentSkill).where(
                    AgentSkill.agent_id == agent_id,
                    AgentSkill.skill_name == skill_name,
                )
            )
            skill = result.scalar_one_or_none()

            if not skill:
                # New skill unlocked!
                skill = AgentSkill(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    skill_name=skill_name,
                    category=skill_def["category"],
                    level=1,
                    xp=0,
                    description=skill_def["desc"],
                    times_used=0,
                    total_uses=0,
                    first_try_passes_with_skill=0,
                    best_score=0,
                    evidence=[],
                )
                db.add(skill)

            # Grant XP
            old_level = skill.level
            skill.xp += total_xp
            skill.times_used += 1
            skill.total_uses += 1
            skill.last_used_at = datetime.now(timezone.utc)
            if score > skill.best_score:
                skill.best_score = score
            if passed_first_try:
                skill.first_try_passes_with_skill += 1

            # Add evidence
            evidence = skill.evidence or []
            evidence.append({
                "episode": episode_title,
                "score": score,
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "first_try": passed_first_try,
            })
            skill.evidence = evidence

            # Check for level up
            for lvl in sorted(SKILL_LEVELS.keys(), reverse=True):
                if skill.xp >= SKILL_LEVELS[lvl]["xp_needed"]:
                    skill.level = lvl
                    break

            if skill.level > old_level:
                leveled_up.append({
                    "skill": skill_name,
                    "old_level": old_level,
                    "new_level": skill.level,
                    "level_name": SKILL_LEVELS[skill.level]["name"],
                })

            # Write physical skill file
            try:
                write_skill_file(
                    agent_id, skill_name, skill.level, skill.xp,
                    skill_def["desc"], skill.evidence or [],
                )
            except Exception as e:
                print(f"[SKILLS] Could not write skill file for {agent_id}/{skill_name}: {e}")

        # Log the production activity
        production_log = AgentProductionLog(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            episode_title=episode_title,
            stage=stage,
            action="produced",
            quality_score=score,
            attempts_needed=attempts,
            skills_used=[s["name"] for s in stage_skills],
            skills_gained_xp=[{"skill": s["name"], "xp": total_xp} for s in stage_skills],
        )
        db.add(production_log)
        await db.commit()

    return leveled_up


# ═══════════════════════════════════════════════════════════════════
# LEADERBOARDS — Who's producing? Who's growing?
# ═══════════════════════════════════════════════════════════════════

async def get_production_leaderboard() -> list[dict]:
    """Rank agents by production output — who's doing the most work."""
    async with async_session() as db:
        result = await db.execute(
            select(
                AgentProductionLog.agent_id,
                func.count(AgentProductionLog.id).label("total_productions"),
                func.avg(AgentProductionLog.quality_score).label("avg_quality"),
                func.avg(AgentProductionLog.attempts_needed).label("avg_attempts"),
            )
            .group_by(AgentProductionLog.agent_id)
            .order_by(func.count(AgentProductionLog.id).desc())
        )
        rows = result.all()
        return [
            {
                "agent_id": r.agent_id,
                "total_productions": r.total_productions,
                "avg_quality": round(float(r.avg_quality or 0), 1),
                "avg_attempts": round(float(r.avg_attempts or 0), 1),
                "efficiency": round(float(r.avg_quality or 0) / max(float(r.avg_attempts or 1), 1), 1),
            }
            for r in rows
        ]


async def get_growth_leaderboard() -> list[dict]:
    """Rank agents by skill growth — who's improving the fastest."""
    async with async_session() as db:
        result = await db.execute(
            select(
                AgentSkill.agent_id,
                func.count(AgentSkill.id).label("total_skills"),
                func.avg(AgentSkill.level).label("avg_level"),
                func.sum(AgentSkill.xp).label("total_xp"),
                func.max(AgentSkill.level).label("highest_level"),
                func.sum(AgentSkill.first_try_passes_with_skill).label("first_try_total"),
                func.sum(AgentSkill.total_uses).label("total_uses"),
            )
            .group_by(AgentSkill.agent_id)
            .order_by(func.sum(AgentSkill.xp).desc())
        )
        rows = result.all()
        return [
            {
                "agent_id": r.agent_id,
                "total_skills": r.total_skills,
                "avg_level": round(float(r.avg_level or 0), 1),
                "total_xp": int(r.total_xp or 0),
                "highest_level": r.highest_level or 1,
                "first_try_rate": f"{(int(r.first_try_total or 0) / max(int(r.total_uses or 1), 1) * 100):.0f}%",
                "growth_velocity": round(float(r.total_xp or 0) / max(int(r.total_uses or 1), 1), 1),
            }
            for r in rows
        ]


async def get_agent_skill_portfolio(agent_id: str) -> dict:
    """Get an agent's full skill folder — all skills with levels, XP, evidence."""
    async with async_session() as db:
        result = await db.execute(
            select(AgentSkill).where(AgentSkill.agent_id == agent_id)
            .order_by(AgentSkill.level.desc(), AgentSkill.xp.desc())
        )
        skills = result.scalars().all()

        # Production stats
        prod_result = await db.execute(
            select(
                func.count(AgentProductionLog.id).label("total"),
                func.avg(AgentProductionLog.quality_score).label("avg_score"),
                func.sum(
                    func.case(
                        (AgentProductionLog.attempts_needed == 1, 1),
                        else_=0,
                    )
                ).label("first_try_passes"),
            ).where(AgentProductionLog.agent_id == agent_id)
        )
        prod_stats = prod_result.one_or_none()

        total = int(prod_stats.total or 0) if prod_stats else 0
        ftp = int(prod_stats.first_try_passes or 0) if prod_stats else 0

        return {
            "agent_id": agent_id,
            "skills": [
                {
                    "name": s.skill_name,
                    "category": s.category,
                    "level": s.level,
                    "level_name": SKILL_LEVELS.get(s.level, SKILL_LEVELS[1])["name"],
                    "level_icon": SKILL_LEVELS.get(s.level, SKILL_LEVELS[1])["icon"],
                    "xp": s.xp,
                    "xp_to_next": SKILL_LEVELS.get(s.level + 1, {}).get("xp_needed", None),
                    "description": s.description,
                    "times_used": s.times_used,
                    "best_score": s.best_score,
                    "first_try_rate": f"{(s.first_try_passes_with_skill / max(s.total_uses, 1) * 100):.0f}%",
                    "evidence_count": len(s.evidence or []),
                    "unlocked_at": s.unlocked_at.isoformat() if s.unlocked_at else None,
                    "last_used_at": s.last_used_at.isoformat() if s.last_used_at else None,
                }
                for s in skills
            ],
            "summary": {
                "total_skills": len(skills),
                "avg_level": round(sum(s.level for s in skills) / len(skills), 1) if skills else 0,
                "total_xp": sum(s.xp for s in skills),
                "master_skills": sum(1 for s in skills if s.level >= 5),
                "expert_skills": sum(1 for s in skills if s.level >= 4),
                "total_productions": total,
                "avg_quality": round(float(prod_stats.avg_score or 0), 1) if prod_stats else 0,
                "first_try_pass_rate": f"{(ftp / max(total, 1) * 100):.0f}%",
            },
            "skill_folder_path": str(get_agent_skill_folder(agent_id)),
        }
