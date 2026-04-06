"""
Agent Memory & Learning System

Every agent learns from every interaction:
  - Successful outputs get stored as "what worked"
  - Failed quality gates get stored as "lessons learned"
  - Feedback patterns get tracked to avoid repeating mistakes
  - Skills improve over time based on accumulated knowledge

Memory is persistent (SQLite) and injected into agent prompts
so they get better with every episode they produce.
"""
from __future__ import annotations

import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, JSON, select
from app.database import Base, async_session


class AgentMemory(Base):
    """A single memory entry for an agent — something they learned."""
    __tablename__ = "agent_memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    memory_type = Column(String, nullable=False)  # "success", "failure", "feedback", "insight", "pattern"
    stage = Column(String, nullable=True)  # Which pipeline stage this relates to
    episode_title = Column(String, nullable=True)  # Which episode
    content = Column(Text, nullable=False)  # The actual memory/lesson
    score_before = Column(Integer, nullable=True)  # Score that triggered this memory
    score_after = Column(Integer, nullable=True)  # Score after applying the lesson
    importance = Column(Float, default=1.0)  # How important this memory is (boosted if repeated)
    times_referenced = Column(Integer, default=0)  # How many times this memory was used
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tags = Column(JSON, default=list)  # ["research", "wake-strategy", "storytelling"]


class AgentSkillScore(Base):
    """Tracks an agent's skill level over time."""
    __tablename__ = "agent_skill_scores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    skill = Column(String, nullable=False)  # "research_depth", "story_structure", "seo_optimization"
    score = Column(Float, default=5.0)  # 1-10 running average
    total_attempts = Column(Integer, default=0)
    successful_attempts = Column(Integer, default=0)  # Passed quality gate first try
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ── Memory Operations ────────────────────────────────────────────────────────

async def record_memory(
    agent_id: str,
    memory_type: str,
    content: str,
    stage: str = None,
    episode_title: str = None,
    score_before: int = None,
    score_after: int = None,
    tags: list[str] = None,
):
    """Record a new memory for an agent."""
    async with async_session() as db:
        memory = AgentMemory(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            memory_type=memory_type,
            stage=stage,
            episode_title=episode_title,
            content=content,
            score_before=score_before,
            score_after=score_after,
            tags=tags or [],
        )
        db.add(memory)
        await db.commit()
        return memory.id


async def record_failure_lesson(
    agent_id: str,
    stage: str,
    episode_title: str,
    score: int,
    feedback: str,
    revision_number: int,
):
    """Record a lesson from a failed quality gate."""
    content = (
        f"LESSON FROM FAILURE (Revision #{revision_number}):\n"
        f"Score: {score}/10\n"
        f"What went wrong: {feedback}\n"
        f"Key takeaway: Always check for these issues before submitting."
    )
    return await record_memory(
        agent_id=agent_id,
        memory_type="failure",
        content=content,
        stage=stage,
        episode_title=episode_title,
        score_before=score,
        tags=["quality-gate", "lesson-learned", stage],
    )


async def record_success(
    agent_id: str,
    stage: str,
    episode_title: str,
    score: int,
    attempts: int,
    work_summary: str,
):
    """Record what worked when a quality gate was passed."""
    content = (
        f"SUCCESS (passed on attempt #{attempts}):\n"
        f"Score: {score}/10\n"
        f"What worked: {work_summary[:500]}\n"
        f"Key patterns to repeat: Achieved 10/10 quality."
    )
    if attempts > 1:
        content += f"\nNote: Took {attempts} attempts. Review failure lessons to avoid extra loops next time."

    return await record_memory(
        agent_id=agent_id,
        memory_type="success",
        content=content,
        stage=stage,
        episode_title=episode_title,
        score_after=score,
        tags=["quality-gate", "success", stage],
    )


async def record_insight(
    agent_id: str,
    content: str,
    tags: list[str] = None,
):
    """Record a general insight or pattern the agent discovered."""
    return await record_memory(
        agent_id=agent_id,
        memory_type="insight",
        content=content,
        tags=tags or ["insight"],
    )


async def get_agent_memories(
    agent_id: str,
    memory_type: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """Retrieve memories for an agent, most recent first."""
    async with async_session() as db:
        query = select(AgentMemory).where(AgentMemory.agent_id == agent_id)
        if memory_type:
            query = query.where(AgentMemory.memory_type == memory_type)
        if stage:
            query = query.where(AgentMemory.stage == stage)
        query = query.order_by(AgentMemory.importance.desc(), AgentMemory.created_at.desc()).limit(limit)

        result = await db.execute(query)
        memories = result.scalars().all()
        return [
            {
                "id": m.id,
                "type": m.memory_type,
                "stage": m.stage,
                "episode": m.episode_title,
                "content": m.content,
                "score_before": m.score_before,
                "score_after": m.score_after,
                "importance": m.importance,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "tags": m.tags or [],
            }
            for m in memories
        ]


async def build_memory_prompt(agent_id: str, stage: str = None) -> str:
    """
    Build a memory injection prompt for an agent.
    This gets prepended to their system prompt so they learn from past work.
    """
    memories = await get_agent_memories(agent_id, limit=15)
    if not memories:
        return ""

    # Separate by type
    failures = [m for m in memories if m["type"] == "failure"]
    successes = [m for m in memories if m["type"] == "success"]
    insights = [m for m in memories if m["type"] == "insight"]

    # Filter for relevant stage if specified
    if stage:
        stage_failures = [m for m in failures if m.get("stage") == stage]
        if stage_failures:
            failures = stage_failures

    prompt_parts = ["\n\n---\n## YOUR MEMORY (Lessons from past work)\n"]

    if failures:
        prompt_parts.append("### Mistakes to AVOID (learned from past quality gate failures):")
        for f in failures[:5]:
            prompt_parts.append(f"- {f['content'][:300]}")

    if successes:
        prompt_parts.append("\n### What WORKED (patterns that scored 10/10):")
        for s in successes[:5]:
            prompt_parts.append(f"- {s['content'][:300]}")

    if insights:
        prompt_parts.append("\n### Key insights:")
        for i in insights[:5]:
            prompt_parts.append(f"- {i['content'][:200]}")

    prompt_parts.append("\nApply these lessons to your current work. Do NOT repeat past mistakes.\n---\n")

    return "\n".join(prompt_parts)


async def update_skill_score(
    agent_id: str,
    skill: str,
    passed_first_try: bool,
):
    """Update an agent's running skill score."""
    async with async_session() as db:
        result = await db.execute(
            select(AgentSkillScore).where(
                AgentSkillScore.agent_id == agent_id,
                AgentSkillScore.skill == skill,
            )
        )
        skill_record = result.scalar_one_or_none()

        if not skill_record:
            skill_record = AgentSkillScore(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                skill=skill,
                score=10.0 if passed_first_try else 5.0,
                total_attempts=1,
                successful_attempts=1 if passed_first_try else 0,
            )
            db.add(skill_record)
        else:
            skill_record.total_attempts += 1
            if passed_first_try:
                skill_record.successful_attempts += 1
            # Running average: weight recent performance more
            success_rate = skill_record.successful_attempts / skill_record.total_attempts
            skill_record.score = round(success_rate * 10, 1)
            skill_record.updated_at = datetime.now(timezone.utc)

        await db.commit()


async def get_agent_skills(agent_id: str) -> list[dict]:
    """Get all skill scores for an agent."""
    async with async_session() as db:
        result = await db.execute(
            select(AgentSkillScore).where(AgentSkillScore.agent_id == agent_id)
        )
        skills = result.scalars().all()
        return [
            {
                "skill": s.skill,
                "score": s.score,
                "total_attempts": s.total_attempts,
                "successful_attempts": s.successful_attempts,
                "success_rate": f"{(s.successful_attempts / s.total_attempts * 100):.0f}%" if s.total_attempts > 0 else "0%",
            }
            for s in skills
        ]
