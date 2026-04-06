"""
Agent Skill Folder System

Every agent has a "skill folder" — a growing portfolio of capabilities.
Skills are unlocked through real work. As agents pass quality gates,
survive pressure tests, and learn from failures, they level up.

Tracks WHO is producing (output volume) and WHO is growing (skill acquisition).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, JSON
from app.database import Base


class AgentSkill(Base):
    """A single skill in an agent's skill folder."""
    __tablename__ = "agent_skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    skill_name = Column(String, nullable=False)      # e.g. "hook-writing", "data-sourcing"
    category = Column(String, nullable=False)          # e.g. "research", "scripting", "seo"
    level = Column(Integer, default=1)                 # 1-5: Novice, Apprentice, Skilled, Expert, Master
    xp = Column(Integer, default=0)                    # Experience points toward next level
    description = Column(Text, nullable=True)          # What this skill enables
    unlocked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_used_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    times_used = Column(Integer, default=0)
    evidence = Column(JSON, default=list)              # [{episode, score, date}] — proof of skill

    # Growth tracking
    first_try_passes_with_skill = Column(Integer, default=0)  # How often 10/10 first try
    total_uses = Column(Integer, default=0)
    best_score = Column(Integer, default=0)


# XP thresholds for each level
SKILL_LEVELS = {
    1: {"name": "Novice", "xp_needed": 0, "icon": "🟢"},
    2: {"name": "Apprentice", "xp_needed": 50, "icon": "🔵"},
    3: {"name": "Skilled", "xp_needed": 150, "icon": "🟣"},
    4: {"name": "Expert", "xp_needed": 350, "icon": "🟠"},
    5: {"name": "Master", "xp_needed": 700, "icon": "🔴"},
}


class AgentProductionLog(Base):
    """Tracks what each agent produces — volume, quality, growth rate."""
    __tablename__ = "agent_production_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    episode_title = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    action = Column(String, nullable=False)      # "produced", "reviewed", "revised", "pressure_tested"
    quality_score = Column(Integer, nullable=True)
    attempts_needed = Column(Integer, default=1)
    skills_used = Column(JSON, default=list)      # Which skills were exercised
    skills_gained_xp = Column(JSON, default=list) # Which skills leveled up
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AgentGrowthSnapshot(Base):
    """Weekly growth snapshot — tracks trajectory over time."""
    __tablename__ = "agent_growth_snapshots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, index=True)
    snapshot_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    total_skills = Column(Integer, default=0)
    avg_skill_level = Column(Float, default=1.0)
    total_episodes_produced = Column(Integer, default=0)
    first_try_pass_rate = Column(Float, default=0.0)
    pressure_test_pass_rate = Column(Float, default=0.0)
    growth_score = Column(Float, default=0.0)  # Composite metric: skill gains + quality improvement


# ═══════════════════════════════════════════════════════════════════
# STAGE → SKILLS MAPPING: What skills each stage exercises
# ═══════════════════════════════════════════════════════════════════

STAGE_SKILLS = {
    "research": [
        {"name": "trend-analysis", "category": "research", "desc": "Identifying trending topics and angles with data backing"},
        {"name": "data-sourcing", "category": "research", "desc": "Finding credible statistics, studies, and real-world examples"},
        {"name": "competitor-analysis", "category": "research", "desc": "Analyzing what competitors are doing and finding gaps"},
        {"name": "audience-psychology", "category": "research", "desc": "Understanding what the target audience craves"},
    ],
    "scripted": [
        {"name": "hook-writing", "category": "scripting", "desc": "Writing scroll-stopping opening hooks"},
        {"name": "narrative-structure", "category": "scripting", "desc": "Building compelling 3-act story arcs"},
        {"name": "dialogue-craft", "category": "scripting", "desc": "Writing natural, engaging voiceover copy"},
        {"name": "pattern-interrupts", "category": "scripting", "desc": "Inserting retention-boosting surprises every 15-20s"},
        {"name": "emotional-pacing", "category": "scripting", "desc": "Managing tension, revelation, and payoff rhythm"},
    ],
    "voiceover": [
        {"name": "voice-direction", "category": "voiceover", "desc": "Crafting precise delivery instructions for AI voice"},
        {"name": "pacing-design", "category": "voiceover", "desc": "Designing pauses, emphasis, and tempo changes"},
        {"name": "audio-mixing", "category": "voiceover", "desc": "Balancing voice with music and sound design"},
    ],
    "thumbnail": [
        {"name": "visual-composition", "category": "thumbnail", "desc": "Creating eye-catching thumbnail layouts"},
        {"name": "click-psychology", "category": "thumbnail", "desc": "Using curiosity gaps and emotion to drive clicks"},
        {"name": "brand-consistency", "category": "thumbnail", "desc": "Maintaining channel visual identity across thumbnails"},
    ],
    "edited": [
        {"name": "scene-composition", "category": "editing", "desc": "Building dynamic scene-by-scene edit briefs"},
        {"name": "footage-selection", "category": "editing", "desc": "Choosing the right stock footage and B-roll"},
        {"name": "transition-design", "category": "editing", "desc": "Designing smooth, engaging transitions"},
        {"name": "retention-engineering", "category": "editing", "desc": "Keeping no static shot >2s, constant visual movement"},
    ],
    "seo": [
        {"name": "keyword-research", "category": "seo", "desc": "Finding high-volume, low-competition keywords"},
        {"name": "title-optimization", "category": "seo", "desc": "Crafting titles that maximize CTR and search ranking"},
        {"name": "metadata-craft", "category": "seo", "desc": "Writing descriptions, tags, and chapters for discoverability"},
        {"name": "algorithm-awareness", "category": "seo", "desc": "Understanding YouTube recommendation and search systems"},
    ],
}
