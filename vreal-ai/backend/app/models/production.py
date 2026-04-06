from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON
from app.database import Base


class ProductionJob(Base):
    """A piece of content moving through the production pipeline.

    Lifecycle: research → scripted → voiceover → thumbnail → edited → seo → review → approved → published

    Each stage is owned by a specific agent. When an agent completes their stage,
    it auto-advances to the next agent in the pipeline.
    """
    __tablename__ = "production_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    channel = Column(String, nullable=False)  # "V-Real AI", "Cash Flow Code", "Mind Shift"
    stage = Column(String, default="research")  # research, scripted, voiceover, thumbnail, edited, seo, review, approved, published
    current_agent_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    target_date = Column(String, default="")
    thread_id = Column(String, nullable=True)  # Links to the agent conversation thread

    # Content produced at each stage
    research_data = Column(Text, nullable=True)
    script = Column(Text, nullable=True)
    voiceover_url = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    seo_metadata = Column(Text, nullable=True)

    # Review chain
    reviewed_by = Column(JSON, default=list)  # list of agent_ids who reviewed
    approved_by = Column(String, nullable=True)  # "pedro" or VP agent_id
    rejection_notes = Column(Text, nullable=True)

    # Make.com execution tracking
    make_executions = Column(JSON, default=list)  # [{scenario, status, timestamp}]


# Pipeline stage → responsible agent mapping
PIPELINE_STAGES = {
    "research": {"agent": "trend-researcher", "make_scenario": "research", "next": "scripted"},
    "scripted": {"agent": "scriptwriter", "make_scenario": "script_generation", "next": "voiceover"},
    "voiceover": {"agent": "voice-director", "make_scenario": "voiceover", "next": "thumbnail"},
    "thumbnail": {"agent": "thumbnail-designer", "make_scenario": "thumbnail", "next": "edited"},
    "edited": {"agent": "video-editor", "make_scenario": "video_assembly", "next": "seo"},
    "seo": {"agent": "seo-specialist", "make_scenario": "seo_optimization", "next": "review"},
    "review": {"agent": "quality-assurance-lead", "make_scenario": None, "next": "approved"},
    "approved": {"agent": "ceo-agent", "make_scenario": "upload_schedule", "next": "published"},
    "published": {"agent": None, "make_scenario": None, "next": None},
}

# Channel → Channel Manager mapping
CHANNEL_MANAGERS = {
    "V-Real AI": "ai-and-tech-channel-manager",
    "Cash Flow Code": "finance-and-business-channel-manager",
    "Mind Shift": "psychology-and-behavior-channel-manager",
}
