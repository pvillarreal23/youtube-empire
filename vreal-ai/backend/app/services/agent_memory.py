"""
Agent Memory & Continuous Learning System

PHILOSOPHY: Every agent learns from EVERYTHING.
- Every quality gate → lesson stored
- Every pressure test → feedback absorbed
- Every interaction with other agents → patterns recognized
- Every success → winning formula recorded
- Every failure → mistake never repeated
- Every episode → cumulative mastery grows

Agents don't just do work and forget. They compound knowledge.
By episode 10, they're significantly better than episode 1.
By episode 50, they're masters.

Memory is persistent (SQLite), injected into every prompt,
and weighted by importance so the most critical lessons
are always top of mind.
"""
from __future__ import annotations

import uuid
import json
import re
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, JSON, select, func
from app.database import Base, async_session


class AgentMemory(Base):
    """A single memory entry — something an agent learned."""
    __tablename__ = "agent_memories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    memory_type = Column(String, nullable=False)
    # Types: "failure", "success", "pressure_test", "collaboration",
    #        "insight", "pattern", "reviewer_feedback", "pedro_feedback"
    stage = Column(String, nullable=True)
    episode_title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    score_before = Column(Integer, nullable=True)
    score_after = Column(Integer, nullable=True)
    importance = Column(Float, default=1.0)  # Higher = more critical. Boosted when pattern repeats.
    times_referenced = Column(Integer, default=0)  # How often this memory was used in prompts
    source_agent = Column(String, nullable=True)  # Who gave this feedback
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tags = Column(JSON, default=list)


class AgentSkillScore(Base):
    """Tracks an agent's mastery level over time."""
    __tablename__ = "agent_skill_scores"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    skill = Column(String, nullable=False)
    score = Column(Float, default=5.0)  # 1-10 running mastery level
    total_attempts = Column(Integer, default=0)
    successful_attempts = Column(Integer, default=0)
    first_try_passes = Column(Integer, default=0)  # Passed quality gate on attempt #1
    total_revisions = Column(Integer, default=0)  # Total revision loops across all episodes
    best_streak = Column(Integer, default=0)  # Longest streak of first-try passes
    current_streak = Column(Integer, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AgentMasteryLog(Base):
    """Episode-by-episode performance tracking for mastery visualization."""
    __tablename__ = "agent_mastery_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    episode_title = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    attempts_needed = Column(Integer, default=1)  # How many loops before passing
    final_score = Column(Integer, nullable=True)
    pressure_test_scores = Column(JSON, default=dict)  # {"claude": 9, "chatgpt": 10, ...}
    lessons_learned = Column(Integer, default=0)  # How many failure lessons this episode
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# ═══════════════════════════════════════════════════════════════════════════
# RECORDING MEMORIES — Every interaction teaches something
# ═══════════════════════════════════════════════════════════════════════════

async def record_memory(
    agent_id: str,
    memory_type: str,
    content: str,
    stage: str = None,
    episode_title: str = None,
    score_before: int = None,
    score_after: int = None,
    source_agent: str = None,
    importance: float = 1.0,
    tags: list[str] = None,
):
    """Record a new memory. Check for duplicates and boost importance if pattern repeats."""
    async with async_session() as db:
        # Check if a similar lesson already exists (pattern detection)
        existing = await db.execute(
            select(AgentMemory).where(
                AgentMemory.agent_id == agent_id,
                AgentMemory.memory_type == memory_type,
                AgentMemory.stage == stage,
            ).order_by(AgentMemory.created_at.desc()).limit(5)
        )
        similar = existing.scalars().all()

        # If same type of feedback keeps coming, boost importance
        # This means the agent keeps making the same mistake → CRITICAL to remember
        repeated_pattern = False
        for mem in similar:
            if _content_similarity(mem.content, content) > 0.5:
                mem.importance = min(mem.importance + 0.5, 5.0)  # Cap at 5x importance
                mem.times_referenced += 1
                repeated_pattern = True
                break

        # Record the new memory
        memory = AgentMemory(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            memory_type=memory_type,
            stage=stage,
            episode_title=episode_title,
            content=content,
            score_before=score_before,
            score_after=score_after,
            source_agent=source_agent,
            importance=importance + (1.0 if repeated_pattern else 0.0),
            tags=tags or [],
        )
        db.add(memory)
        await db.commit()
        return memory.id


def _content_similarity(a: str, b: str) -> float:
    """Simple keyword overlap similarity (0-1). Detects repeated feedback patterns."""
    words_a = set(a.lower().split()[:50])
    words_b = set(b.lower().split()[:50])
    if not words_a or not words_b:
        return 0.0
    overlap = words_a & words_b
    return len(overlap) / max(len(words_a), len(words_b))


async def record_failure_lesson(
    agent_id: str,
    stage: str,
    episode_title: str,
    score: int,
    feedback: str,
    revision_number: int,
):
    """Record a lesson from a failed quality gate. Extract the key takeaway."""
    # Extract the most actionable part of the feedback
    key_issues = _extract_key_issues(feedback)

    content = (
        f"FAILURE — {stage} stage, EP: '{episode_title}', Score: {score}/10, Attempt #{revision_number}\n"
        f"KEY ISSUES: {key_issues}\n"
        f"RULE: Never submit {stage} work without checking for these issues first."
    )
    return await record_memory(
        agent_id=agent_id,
        memory_type="failure",
        content=content,
        stage=stage,
        episode_title=episode_title,
        score_before=score,
        importance=1.5,  # Failures are more important than successes to remember
        tags=["quality-gate", "lesson-learned", stage, f"score-{score}"],
    )


async def record_success(
    agent_id: str,
    stage: str,
    episode_title: str,
    score: int,
    attempts: int,
    work_summary: str,
):
    """Record what worked when passing a quality gate."""
    content = (
        f"SUCCESS — {stage} stage, EP: '{episode_title}', Score: {score}/10, "
        f"{'First try!' if attempts == 1 else f'Passed on attempt #{attempts}'}\n"
        f"WINNING APPROACH: {work_summary[:400]}\n"
        f"{'PATTERN: This approach works. Repeat it.' if attempts == 1 else f'NOTE: Took {attempts} attempts. Review failure lessons to do better next time.'}"
    )
    importance = 2.0 if attempts == 1 else 1.0  # First-try successes are gold

    await record_memory(
        agent_id=agent_id,
        memory_type="success",
        content=content,
        stage=stage,
        episode_title=episode_title,
        score_after=score,
        importance=importance,
        tags=["quality-gate", "success", stage, f"attempts-{attempts}"],
    )

    # Log mastery
    await _log_mastery(agent_id, episode_title, stage, attempts, score)


async def record_pressure_test_lesson(
    agent_id: str,
    stage: str,
    episode_title: str,
    model_scores: dict,  # {"claude": 9, "chatgpt": 8, ...}
    synthesized_feedback: str,
    passed: bool,
):
    """Record lessons from multi-model pressure testing."""
    scores_str = ", ".join(f"{k}: {v}/10" for k, v in model_scores.items())
    avg = sum(model_scores.values()) / len(model_scores) if model_scores else 0

    if passed:
        content = (
            f"PRESSURE TEST PASSED — {stage}, EP: '{episode_title}'\n"
            f"Scores: {scores_str} (avg: {avg:.1f})\n"
            f"ALL MODELS AGREED — this quality level is the standard to maintain."
        )
    else:
        content = (
            f"PRESSURE TEST FAILED — {stage}, EP: '{episode_title}'\n"
            f"Scores: {scores_str} (avg: {avg:.1f})\n"
            f"COMBINED FEEDBACK: {synthesized_feedback[:500]}\n"
            f"RULE: Address ALL model feedback before resubmitting."
        )

    await record_memory(
        agent_id=agent_id,
        memory_type="pressure_test",
        content=content,
        stage=stage,
        episode_title=episode_title,
        score_before=int(avg),
        importance=2.0 if not passed else 1.5,
        tags=["pressure-test", stage, "passed" if passed else "failed"],
    )

    # Log mastery with pressure test scores
    async with async_session() as db:
        result = await db.execute(
            select(AgentMasteryLog).where(
                AgentMasteryLog.agent_id == agent_id,
                AgentMasteryLog.episode_title == episode_title,
                AgentMasteryLog.stage == stage,
            ).order_by(AgentMasteryLog.created_at.desc()).limit(1)
        )
        log = result.scalar_one_or_none()
        if log:
            log.pressure_test_scores = model_scores
            await db.commit()


async def record_collaboration_lesson(
    agent_id: str,
    other_agent_id: str,
    lesson: str,
    episode_title: str = None,
):
    """Record something learned from working with another agent."""
    content = (
        f"COLLABORATION with {other_agent_id}: {lesson}\n"
        f"TAKEAWAY: Apply this when working with {other_agent_id} in the future."
    )
    await record_memory(
        agent_id=agent_id,
        memory_type="collaboration",
        content=content,
        episode_title=episode_title,
        source_agent=other_agent_id,
        tags=["collaboration", other_agent_id],
    )


async def record_pedro_feedback(
    agent_id: str,
    feedback: str,
    episode_title: str = None,
    stage: str = None,
):
    """Record feedback directly from Pedro (the human). Highest importance."""
    content = (
        f"PEDRO FEEDBACK (HIGHEST PRIORITY): {feedback}\n"
        f"RULE: Pedro's feedback overrides all other guidance. Always apply this."
    )
    await record_memory(
        agent_id=agent_id,
        memory_type="pedro_feedback",
        content=content,
        stage=stage,
        episode_title=episode_title,
        source_agent="pedro",
        importance=5.0,  # Maximum importance — Pedro is the boss
        tags=["pedro", "human-feedback", "critical"],
    )


async def record_insight(
    agent_id: str,
    content: str,
    tags: list[str] = None,
):
    """Record a general insight or pattern discovered."""
    return await record_memory(
        agent_id=agent_id,
        memory_type="insight",
        content=content,
        importance=1.5,
        tags=tags or ["insight"],
    )


async def record_reviewer_feedback(
    agent_id: str,
    reviewer_id: str,
    feedback: str,
    score: int,
    stage: str,
    episode_title: str = None,
):
    """Record specific feedback from a reviewer agent."""
    key_issues = _extract_key_issues(feedback)
    content = (
        f"REVIEWER ({reviewer_id}) FEEDBACK — Score: {score}/10\n"
        f"ISSUES: {key_issues}\n"
        f"REMEMBER: Check for these issues BEFORE submitting next time."
    )
    await record_memory(
        agent_id=agent_id,
        memory_type="reviewer_feedback",
        content=content,
        stage=stage,
        episode_title=episode_title,
        score_before=score,
        source_agent=reviewer_id,
        importance=1.5,
        tags=["reviewer-feedback", stage, reviewer_id],
    )


# ═══════════════════════════════════════════════════════════════════════════
# MEMORY RETRIEVAL — Building the learning prompt
# ═══════════════════════════════════════════════════════════════════════════

async def get_agent_memories(
    agent_id: str,
    memory_type: Optional[str] = None,
    stage: Optional[str] = None,
    limit: int = 20,
) -> list[dict]:
    """Retrieve memories, weighted by importance and recency."""
    async with async_session() as db:
        query = select(AgentMemory).where(AgentMemory.agent_id == agent_id)
        if memory_type:
            query = query.where(AgentMemory.memory_type == memory_type)
        if stage:
            query = query.where(AgentMemory.stage == stage)
        # Sort by importance (highest first), then recency
        query = query.order_by(
            AgentMemory.importance.desc(),
            AgentMemory.created_at.desc(),
        ).limit(limit)

        result = await db.execute(query)
        memories = result.scalars().all()

        # Mark as referenced
        for m in memories:
            m.times_referenced += 1
        await db.commit()

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
                "source_agent": m.source_agent,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "tags": m.tags or [],
            }
            for m in memories
        ]


async def build_memory_prompt(agent_id: str, stage: str = None) -> str:
    """
    Build a comprehensive memory injection for an agent's prompt.

    This is THE key function — it turns past experience into better future work.
    The agent receives their accumulated wisdom before every task.
    """
    # Get all memory types, prioritized
    all_memories = await get_agent_memories(agent_id, limit=30)

    if not all_memories:
        return ""

    # Categorize
    pedro_feedback = [m for m in all_memories if m["type"] == "pedro_feedback"]
    failures = [m for m in all_memories if m["type"] == "failure"]
    pressure_tests = [m for m in all_memories if m["type"] == "pressure_test"]
    successes = [m for m in all_memories if m["type"] == "success"]
    reviewer_fb = [m for m in all_memories if m["type"] == "reviewer_feedback"]
    collaborations = [m for m in all_memories if m["type"] == "collaboration"]
    insights = [m for m in all_memories if m["type"] == "insight"]

    # Filter for current stage if relevant
    if stage:
        stage_failures = [m for m in failures if m.get("stage") == stage]
        stage_reviewer = [m for m in reviewer_fb if m.get("stage") == stage]
        if stage_failures:
            failures = stage_failures
        if stage_reviewer:
            reviewer_fb = stage_reviewer

    # Get mastery stats
    skills = await get_agent_skills(agent_id)

    # Build the prompt
    sections = []
    sections.append("\n\n" + "=" * 60)
    sections.append("YOUR ACCUMULATED KNOWLEDGE (from past episodes)")
    sections.append("You have a growing memory. Use it. Never repeat past mistakes.")
    sections.append("=" * 60)

    # Pedro feedback ALWAYS first (highest priority)
    if pedro_feedback:
        sections.append("\n### PEDRO'S DIRECT FEEDBACK (highest priority — always follow):")
        for m in pedro_feedback[:3]:
            sections.append(f"  ★ {m['content']}")

    # Mastery level
    if skills:
        sections.append("\n### YOUR MASTERY LEVELS:")
        for s in skills:
            bar = "█" * int(s["score"]) + "░" * (10 - int(s["score"]))
            sections.append(f"  {s['skill']}: [{bar}] {s['score']}/10 ({s['success_rate']} first-try pass rate)")

    # Critical failures (MUST AVOID)
    if failures:
        sections.append("\n### MISTAKES YOU'VE MADE BEFORE (do NOT repeat):")
        for f in failures[:5]:
            sections.append(f"  ✗ {f['content'][:250]}")

    # Reviewer patterns
    if reviewer_fb:
        sections.append("\n### WHAT REVIEWERS KEEP FLAGGING:")
        for r in reviewer_fb[:3]:
            sections.append(f"  → {r['content'][:250]}")

    # Pressure test lessons
    if pressure_tests:
        sections.append("\n### PRESSURE TEST LESSONS (multi-model feedback):")
        for p in pressure_tests[:3]:
            sections.append(f"  ◆ {p['content'][:250]}")

    # Winning patterns
    if successes:
        sections.append("\n### WHAT WORKED (repeat these patterns):")
        for s in successes[:3]:
            sections.append(f"  ✓ {s['content'][:250]}")

    # Collaboration insights
    if collaborations:
        sections.append("\n### TEAM INSIGHTS:")
        for c in collaborations[:2]:
            sections.append(f"  ↔ {c['content'][:200]}")

    # General insights
    if insights:
        sections.append("\n### KEY INSIGHTS:")
        for i in insights[:3]:
            sections.append(f"  💡 {i['content'][:200]}")

    # META-PROMPTING: Self-generated improvement rules
    # Agents create their own rules based on patterns they've seen
    meta_rules = _generate_meta_prompt_rules(failures, successes, pressure_tests, reviewer_fb)
    if meta_rules:
        sections.append("\n### YOUR SELF-GENERATED RULES (meta-prompting — rules you wrote for yourself):")
        for rule in meta_rules:
            sections.append(f"  📌 {rule}")

    sections.append("\n" + "=" * 60)
    sections.append("Apply ALL of this knowledge. You are getting better every episode.")
    sections.append("Use meta-prompting: before submitting, re-read your rules above and verify compliance.")
    sections.append("=" * 60 + "\n")

    return "\n".join(sections)


# ═══════════════════════════════════════════════════════════════════════════
# SKILL & MASTERY TRACKING
# ═══════════════════════════════════════════════════════════════════════════

async def update_skill_score(
    agent_id: str,
    skill: str,
    passed_first_try: bool,
    revisions_needed: int = 0,
):
    """Update an agent's mastery score for a skill."""
    async with async_session() as db:
        result = await db.execute(
            select(AgentSkillScore).where(
                AgentSkillScore.agent_id == agent_id,
                AgentSkillScore.skill == skill,
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            record = AgentSkillScore(
                id=str(uuid.uuid4()),
                agent_id=agent_id,
                skill=skill,
                score=10.0 if passed_first_try else 5.0,
                total_attempts=1,
                successful_attempts=1,
                first_try_passes=1 if passed_first_try else 0,
                total_revisions=revisions_needed,
                best_streak=1 if passed_first_try else 0,
                current_streak=1 if passed_first_try else 0,
            )
            db.add(record)
        else:
            record.total_attempts += 1
            record.successful_attempts += 1  # They all eventually pass
            record.total_revisions += revisions_needed

            if passed_first_try:
                record.first_try_passes += 1
                record.current_streak += 1
                if record.current_streak > record.best_streak:
                    record.best_streak = record.current_streak
            else:
                record.current_streak = 0

            # Mastery score = weighted combination of:
            # - First-try pass rate (60% weight)
            # - Improvement trend (20% weight)
            # - Low revision count (20% weight)
            ftp_rate = record.first_try_passes / record.total_attempts
            avg_revisions = record.total_revisions / record.total_attempts
            revision_score = max(0, 1 - (avg_revisions / 5))  # 0 revisions = 1.0, 5+ = 0.0

            record.score = round(
                (ftp_rate * 6.0 + revision_score * 2.0 + (record.current_streak / max(record.total_attempts, 1)) * 2.0),
                1
            )
            record.score = min(record.score, 10.0)
            record.updated_at = datetime.now(timezone.utc)

        await db.commit()


async def get_agent_skills(agent_id: str) -> list[dict]:
    """Get all skill mastery levels for an agent."""
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
                "first_try_passes": s.first_try_passes,
                "successful_attempts": s.successful_attempts,
                "total_revisions": s.total_revisions,
                "best_streak": s.best_streak,
                "current_streak": s.current_streak,
                "success_rate": f"{(s.first_try_passes / s.total_attempts * 100):.0f}%" if s.total_attempts > 0 else "0%",
            }
            for s in skills
        ]


async def _log_mastery(
    agent_id: str,
    episode_title: str,
    stage: str,
    attempts: int,
    final_score: int,
):
    """Log episode performance for mastery tracking."""
    async with async_session() as db:
        log = AgentMasteryLog(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            episode_title=episode_title,
            stage=stage,
            attempts_needed=attempts,
            final_score=final_score,
            lessons_learned=attempts - 1,  # Each failed attempt = 1 lesson
        )
        db.add(log)
        await db.commit()


async def get_mastery_timeline(agent_id: str) -> list[dict]:
    """Get an agent's performance over time — shows learning curve."""
    async with async_session() as db:
        result = await db.execute(
            select(AgentMasteryLog).where(
                AgentMasteryLog.agent_id == agent_id,
            ).order_by(AgentMasteryLog.created_at)
        )
        logs = result.scalars().all()
        return [
            {
                "episode": l.episode_title,
                "stage": l.stage,
                "attempts": l.attempts_needed,
                "final_score": l.final_score,
                "pressure_test": l.pressure_test_scores or {},
                "lessons": l.lessons_learned,
                "date": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def _generate_meta_prompt_rules(
    failures: list[dict],
    successes: list[dict],
    pressure_tests: list[dict],
    reviewer_fb: list[dict],
) -> list[str]:
    """
    META-PROMPTING ENGINE: Generate self-improvement rules from patterns.

    Instead of just remembering "I failed because X", the agent creates
    an explicit RULE for itself: "ALWAYS do Y before submitting."

    This turns scattered feedback into a personal checklist that grows
    with every episode. By episode 20, the agent has a robust set of
    self-generated instructions that prevent all known failure modes.
    """
    rules = []

    # Rule from repeated failures: "I keep failing at X → RULE: always check X"
    failure_keywords = {}
    for f in failures[:10]:
        content = f.get("content", "").lower()
        for keyword in ["missing", "weak", "incomplete", "no source", "no data",
                       "generic", "vague", "shallow", "repetitive", "boring",
                       "no hook", "no structure", "too long", "too short",
                       "no emotion", "no story", "no evidence", "no examples"]:
            if keyword in content:
                failure_keywords[keyword] = failure_keywords.get(keyword, 0) + 1

    for keyword, count in sorted(failure_keywords.items(), key=lambda x: -x[1]):
        if count >= 2:
            rules.append(
                f"RULE (from {count} past failures): ALWAYS check for '{keyword}' issues before submitting. "
                f"This has been flagged {count} times — make it a non-negotiable checklist item."
            )
        if len(rules) >= 3:
            break

    # Rule from successes: "When I did X, I got 10/10 → RULE: always do X"
    for s in successes[:3]:
        content = s.get("content", "")
        if "First try!" in content:
            # Extract what worked
            if "WINNING APPROACH:" in content:
                approach = content.split("WINNING APPROACH:")[1].split("\n")[0].strip()[:150]
                rules.append(f"WINNING RULE: {approach} — this approach got 10/10 first try. Repeat it.")
                break

    # Rule from pressure tests: "Multiple models flagged X → RULE: X is critical"
    for pt in pressure_tests[:3]:
        content = pt.get("content", "")
        if "FAILED" in content and "COMBINED FEEDBACK:" in content:
            feedback = content.split("COMBINED FEEDBACK:")[1].strip()[:150]
            rules.append(f"PRESSURE TEST RULE: Multi-model consensus says: {feedback}")
            break

    # Rule from reviewer patterns: "Reviewer keeps saying X → RULE: pre-check X"
    reviewer_patterns = {}
    for r in reviewer_fb[:5]:
        content = r.get("content", "").lower()
        source = r.get("source_agent", "reviewer")
        for keyword in ["missing", "needs", "add", "include", "improve", "strengthen",
                       "more detail", "more specific", "more examples", "cite sources"]:
            if keyword in content:
                reviewer_patterns[keyword] = reviewer_patterns.get(keyword, 0) + 1

    for keyword, count in sorted(reviewer_patterns.items(), key=lambda x: -x[1]):
        if count >= 2:
            rules.append(
                f"REVIEWER RULE: Reviewers flag '{keyword}' repeatedly ({count}x). "
                f"Pre-check this BEFORE submitting to avoid revision loops."
            )
            break

    return rules[:5]  # Max 5 meta-prompting rules — keep it focused


def _extract_key_issues(feedback: str) -> str:
    """Extract the most actionable points from feedback text."""
    # Look for numbered items, bullet points, or key phrases
    lines = feedback.split("\n")
    key_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Capture numbered items, bullets, or lines with strong keywords
        if re.match(r"^[\d\-\*•→]", stripped) or any(
            kw in stripped.lower() for kw in [
                "missing", "need", "must", "should", "fix", "add",
                "critical", "gap", "flaw", "incomplete", "weak",
            ]
        ):
            key_lines.append(stripped)

    if key_lines:
        return " | ".join(key_lines[:5])
    return feedback[:300]
