from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from app.database import Base


class AgentWorkspace(Base):
    """Each agent has their own workspace to create, store, and push content."""
    __tablename__ = "agent_workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # Agent's personal settings and preferences
    settings = Column(JSON, default=dict)
    # Make.com webhooks this agent has created
    custom_webhooks = Column(JSON, default=list)
    # Agent's personal notes/scratchpad
    notes = Column(Text, default="")


class ContentArtifact(Base):
    """Any content an agent creates — scripts, topics, briefs, plans, etc."""
    __tablename__ = "content_artifacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)  # Who created it
    artifact_type = Column(String, nullable=False)  # script, topic_list, brief, plan, seo_package, thumbnail_brief, newsletter_draft, research_package, report, template, custom
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    channel = Column(String, default="")  # Which channel this is for (if applicable)
    status = Column(String, default="draft")  # draft, in_review, approved, published, archived
    version = Column(String, default="1")
    extra_data = Column(JSON, default=dict)  # Flexible data (word count, target length, keywords, etc.)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    # Production pipeline tracking
    pipeline_stage = Column(String, default="")  # empty = not in pipeline yet
    make_execution_id = Column(String, default="")  # Track Make.com execution if pushed


class AgentPipeline(Base):
    """An agent's personal production pipeline — tracks work they're pushing through."""
    __tablename__ = "agent_pipelines"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)
    artifact_id = Column(String, nullable=False)  # Links to ContentArtifact
    action = Column(String, nullable=False)  # create, edit, review, push_to_make, publish, hand_off
    target_agent_id = Column(String, nullable=True)  # Who this is being handed off to
    make_scenario = Column(String, default="")  # Which Make.com scenario was triggered
    status = Column(String, default="pending")  # pending, running, complete, failed
    result = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)


# Template types each agent role can create
AGENT_ARTIFACT_TYPES = {
    "scriptwriter-agent": ["script", "outline", "hook_options", "cta_options"],
    "hook-specialist-agent": ["hook_options", "opening_variations"],
    "storyteller-agent": ["narrative_arc", "story_framework", "anecdote_library"],
    "ai-and-tech-channel-manager-agent": ["topic_list", "content_brief", "competitor_analysis"],
    "finance-channel-manager-agent": ["topic_list", "content_brief", "market_analysis"],
    "psychology-channel-manager-agent": ["topic_list", "content_brief", "study_roundup"],
    "thumbnail-designer-agent": ["thumbnail_brief", "ab_test_plan"],
    "video-editor-agent": ["edit_notes", "cut_list", "graphics_list"],
    "seo-specialist-agent": ["seo_package", "keyword_research", "title_options"],
    "trend-researcher-agent": ["trend_report", "topic_list", "platform_scan"],
    "senior-researcher-agent": ["research_package", "fact_check", "source_compilation"],
    "data-analyst-agent": ["analytics_report", "performance_dashboard", "forecast"],
    "newsletter-strategist-agent": ["newsletter_draft", "email_sequence", "subject_lines", "lead_magnet"],
    "social-media-manager-agent": ["social_calendar", "post_batch", "cross_platform_plan"],
    "shorts-and-clips-agent": ["clips_plan", "shorts_script", "repurpose_list"],
    "partnership-manager-agent": ["outreach_pitch", "deal_proposal", "partnership_brief"],
    "affiliate-coordinator-agent": ["affiliate_report", "link_audit", "program_evaluation"],
    "digital-product-manager-agent": ["product_brief", "launch_plan", "pricing_strategy"],
    "community-manager-agent": ["community_report", "engagement_plan", "content_ideas_from_community"],
    "project-manager-agent": ["project_status", "timeline", "resource_plan"],
    "workflow-orchestrator-agent": ["workflow_design", "automation_blueprint", "process_doc"],
    "qa-lead-agent": ["qa_review", "checklist", "quality_report"],
    "compliance-officer-agent": ["compliance_review", "disclosure_checklist", "audit_report"],
    "secretary-agent": ["meeting_notes", "daily_brief", "weekly_summary", "action_items"],
    "reflection-council-agent": ["retrospective", "assumption_audit", "pre_mortem"],
    "web-designer-agent": ["design_spec", "ui_mockup", "style_guide_update"],
    "web-developer-agent": ["code_spec", "feature_implementation", "bug_fix", "performance_audit"],
    "content-vp-agent": ["editorial_calendar", "content_strategy", "performance_debrief"],
    "operations-vp-agent": ["ops_report", "capacity_plan", "pipeline_review"],
    "analytics-vp-agent": ["analytics_report", "growth_strategy", "ab_test_plan"],
    "monetization-vp-agent": ["revenue_report", "monetization_strategy", "deal_pipeline"],
    "ceo-agent": ["strategic_directive", "okr_review", "company_memo"],
}
