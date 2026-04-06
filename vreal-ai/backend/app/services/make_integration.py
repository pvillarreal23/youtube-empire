"""
Make.com Integration Service

Agents trigger Make.com scenarios to execute real work:
- Script generation → Google Sheets
- Voiceover synthesis → ElevenLabs
- Thumbnail creation → Midjourney/Canva
- Video assembly → InVideo
- SEO optimization → YouTube metadata
- Upload scheduling → YouTube API
- Social posting → Multi-platform distribution

All outputs flow through the approval pipeline before going live.
"""
from __future__ import annotations

import os
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from app.database import async_session
from app.models.scheduler import Escalation
from app.models.thread import Thread, Message
from app.models.agent import Agent

# Make.com webhook URLs — agents trigger these to execute real work
MAKE_WEBHOOKS = {
    # Production pipeline scenarios
    "research": os.getenv("MAKE_WEBHOOK_RESEARCH", ""),
    "script_generation": os.getenv("MAKE_WEBHOOK_SCRIPT", ""),
    "voiceover": os.getenv("MAKE_WEBHOOK_VOICEOVER", ""),
    "thumbnail": os.getenv("MAKE_WEBHOOK_THUMBNAIL", ""),
    "video_assembly": os.getenv("MAKE_WEBHOOK_VIDEO", ""),
    "seo_optimization": os.getenv("MAKE_WEBHOOK_SEO", ""),
    "upload_schedule": os.getenv("MAKE_WEBHOOK_UPLOAD", ""),
    "social_post": os.getenv("MAKE_WEBHOOK_SOCIAL", ""),

    # Business operations scenarios
    "newsletter_send": os.getenv("MAKE_WEBHOOK_NEWSLETTER", ""),
    "analytics_pull": os.getenv("MAKE_WEBHOOK_ANALYTICS", ""),
    "sheets_update": os.getenv("MAKE_WEBHOOK_SHEETS", ""),
    "notify_pedro": os.getenv("MAKE_WEBHOOK_NOTIFY", ""),

    # General purpose
    "custom": os.getenv("MAKE_WEBHOOK_CUSTOM", ""),
}

# Every agent gets full access to create and push production — this is how we scale
# Agents autonomously trigger Make.com scenarios relevant to their role
AGENT_PERMISSIONS = {
    # Content creators — full content pipeline access
    "scriptwriter-agent": ["script_generation", "sheets_update", "custom", "research"],
    "hook-specialist-agent": ["script_generation", "sheets_update", "custom"],
    "storyteller-agent": ["script_generation", "sheets_update", "custom"],

    # Production — full production pipeline access
    "video-editor-agent": ["video_assembly", "voiceover", "thumbnail", "sheets_update", "custom"],
    "thumbnail-designer-agent": ["thumbnail", "sheets_update", "custom"],
    "shorts-and-clips-agent": ["video_assembly", "social_post", "thumbnail", "sheets_update", "custom"],

    # Channel managers — full content + research + social
    "ai-and-tech-channel-manager-agent": ["script_generation", "research", "seo_optimization", "social_post", "sheets_update", "custom"],
    "finance-channel-manager-agent": ["script_generation", "research", "seo_optimization", "social_post", "sheets_update", "custom"],
    "psychology-channel-manager-agent": ["script_generation", "research", "seo_optimization", "social_post", "sheets_update", "custom"],

    # Distribution — full social + newsletter
    "social-media-manager-agent": ["social_post", "sheets_update", "custom"],
    "community-manager-agent": ["social_post", "sheets_update", "custom"],
    "newsletter-strategist-agent": ["newsletter_send", "sheets_update", "custom"],

    # Analytics & Research — full research + analytics
    "seo-specialist-agent": ["seo_optimization", "research", "analytics_pull", "sheets_update", "custom"],
    "data-analyst-agent": ["analytics_pull", "research", "sheets_update", "custom"],
    "trend-researcher-agent": ["research", "analytics_pull", "sheets_update", "custom"],
    "senior-researcher-agent": ["research", "analytics_pull", "sheets_update", "custom"],

    # Monetization — full revenue stack
    "partnership-manager-agent": ["sheets_update", "notify_pedro", "custom"],
    "affiliate-coordinator-agent": ["sheets_update", "custom"],
    "digital-product-manager-agent": ["sheets_update", "custom", "notify_pedro"],

    # Operations — full pipeline management
    "project-manager-agent": ["sheets_update", "notify_pedro", "custom"],
    "workflow-orchestrator-agent": ["sheets_update", "notify_pedro", "custom"],
    "qa-lead-agent": ["sheets_update", "notify_pedro", "custom"],
    "secretary-agent": ["sheets_update", "notify_pedro", "custom"],
    "compliance-officer-agent": ["sheets_update", "notify_pedro", "custom"],
    "reflection-council-agent": ["sheets_update", "notify_pedro", "custom"],

    # Web team — full custom access
    "web-designer-agent": ["custom", "sheets_update"],
    "web-developer-agent": ["custom", "sheets_update"],

    # VPs — full domain access + cross-domain
    "content-vp-agent": ["script_generation", "research", "seo_optimization", "social_post", "sheets_update", "notify_pedro", "custom"],
    "operations-vp-agent": ["video_assembly", "voiceover", "thumbnail", "seo_optimization", "sheets_update", "notify_pedro", "custom"],
    "analytics-vp-agent": ["analytics_pull", "seo_optimization", "research", "sheets_update", "notify_pedro", "custom"],
    "monetization-vp-agent": ["newsletter_send", "social_post", "sheets_update", "notify_pedro", "custom"],

    # CEO — everything
    "ceo-agent": list(MAKE_WEBHOOKS.keys()),
}

# Actions that require Pedro's approval before executing
REQUIRES_APPROVAL = {
    "upload_schedule",   # Publishing to YouTube
    "social_post",       # Posting publicly
    "newsletter_send",   # Sending to email list
    "notify_pedro",      # Notifying Pedro directly
}

# Actions that can run autonomously (internal work only)
AUTO_APPROVE = {
    "research",          # Research is always safe
    "script_generation", # Drafting scripts (not publishing)
    "voiceover",         # Generating voiceover files
    "thumbnail",         # Creating thumbnail options
    "video_assembly",    # Assembling video (not uploading)
    "seo_optimization",  # Preparing SEO metadata
    "analytics_pull",    # Pulling analytics data
    "sheets_update",     # Updating internal spreadsheets
    "custom",            # Custom webhooks (internal)
}


async def trigger_make_scenario(
    agent_id: str,
    scenario: str,
    payload: dict,
    thread_id: Optional[str] = None,
) -> dict:
    """
    Trigger a Make.com scenario from an agent.

    Returns: {"status": "triggered"|"queued_for_approval"|"denied", ...}
    """
    import httpx

    # Check permissions
    allowed = AGENT_PERMISSIONS.get(agent_id, [])
    if scenario not in allowed:
        return {
            "status": "denied",
            "reason": f"Agent {agent_id} does not have permission for '{scenario}'",
        }

    # Check if webhook URL is configured
    webhook_url = MAKE_WEBHOOKS.get(scenario, "")
    if not webhook_url:
        return {
            "status": "not_configured",
            "reason": f"Make.com webhook for '{scenario}' is not configured. Add MAKE_WEBHOOK_{scenario.upper()} to .env",
        }

    # Check if approval is needed
    if scenario in REQUIRES_APPROVAL:
        # Create an escalation for Pedro to approve
        async with async_session() as db:
            escalation = Escalation(
                id=str(uuid.uuid4()),
                thread_id=thread_id or "",
                agent_id=agent_id,
                reason=f"Requesting approval to execute: {scenario}\nPayload: {json.dumps(payload, indent=2)[:500]}",
                severity="high",
            )
            db.add(escalation)
            await db.commit()

        return {
            "status": "queued_for_approval",
            "reason": f"'{scenario}' requires Pedro's approval. Escalation created.",
            "escalation_id": escalation.id,
        }

    # Auto-approved — execute immediately
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                webhook_url,
                json={
                    "agent_id": agent_id,
                    "scenario": scenario,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "thread_id": thread_id,
                    **payload,
                },
            )
            return {
                "status": "triggered",
                "http_status": response.status_code,
                "response": response.text[:500],
            }
    except Exception as e:
        return {
            "status": "error",
            "reason": str(e)[:300],
        }


async def get_agent_capabilities(agent_id: str) -> dict:
    """Return what Make.com scenarios an agent can trigger."""
    allowed = AGENT_PERMISSIONS.get(agent_id, [])
    capabilities = {}
    for scenario in allowed:
        webhook = MAKE_WEBHOOKS.get(scenario, "")
        capabilities[scenario] = {
            "configured": bool(webhook),
            "requires_approval": scenario in REQUIRES_APPROVAL,
            "auto_approve": scenario in AUTO_APPROVE,
        }
    return capabilities
