"""
Baseline Skills Seeder

Every agent starts with skills that match their job title and tier.
A Trend Researcher doesn't start at zero — they already know how to research.
Higher tiers get higher starting levels because they're senior roles.

This runs once on startup to seed the skill folders and database.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from app.database import async_session
from app.models.skills import AgentSkill, SKILL_LEVELS
from app.services.skill_growth import write_skill_file

# ═══════════════════════════════════════════════════════════════════
# TIER → STARTING LEVEL: Senior roles start at higher skill levels
# ═══════════════════════════════════════════════════════════════════
TIER_STARTING_LEVEL = {
    1: 4,  # CEO — Expert level
    2: 4,  # VPs — Expert level
    3: 3,  # Channel Managers — Skilled
    4: 2,  # Production Specialists — Apprentice (they grow through doing)
    5: 3,  # Operations — Skilled
    6: 3,  # Analytics/Research — Skilled
    7: 2,  # Monetization — Apprentice
    8: 2,  # Community — Apprentice
    9: 3,  # Compliance — Skilled
}

# Starting XP per level so they're positioned correctly within the level
LEVEL_STARTING_XP = {
    1: 10,
    2: 60,
    3: 170,
    4: 380,
    5: 720,
}

# ═══════════════════════════════════════════════════════════════════
# AGENT BASELINE SKILLS: What each agent knows from day one
# ═══════════════════════════════════════════════════════════════════

AGENT_BASELINE_SKILLS = {
    # ── TIER 1: CEO ──
    "ceo-agent": [
        {"name": "strategic-vision", "category": "leadership", "desc": "Setting $1M/year revenue targets and channel direction"},
        {"name": "team-orchestration", "category": "leadership", "desc": "Coordinating 33 agents across 9 tiers for maximum output"},
        {"name": "quality-standards", "category": "leadership", "desc": "Enforcing BBC/Netflix documentary quality across all content"},
        {"name": "revenue-strategy", "category": "business", "desc": "Designing multi-stream monetization for faceless AI channels"},
        {"name": "brand-identity", "category": "branding", "desc": "Maintaining V-Real AI's premium documentary brand positioning"},
    ],

    # ── TIER 2: VPs ──
    "content-vp": [
        {"name": "content-strategy", "category": "strategy", "desc": "Planning content calendars that maximize growth and engagement"},
        {"name": "editorial-direction", "category": "editorial", "desc": "Guiding narrative quality across all channels and formats"},
        {"name": "pipeline-oversight", "category": "management", "desc": "Ensuring smooth flow from research to publication"},
        {"name": "talent-development", "category": "leadership", "desc": "Coaching production agents to improve output quality"},
        {"name": "audience-growth", "category": "growth", "desc": "Designing content strategies that drive subscriber growth"},
    ],
    "operations-vp": [
        {"name": "workflow-design", "category": "operations", "desc": "Designing efficient production pipelines with minimal waste"},
        {"name": "automation-strategy", "category": "operations", "desc": "Identifying and implementing automation opportunities"},
        {"name": "resource-allocation", "category": "management", "desc": "Distributing workload optimally across agent teams"},
        {"name": "process-optimization", "category": "operations", "desc": "Continuous improvement of production bottlenecks"},
        {"name": "crisis-management", "category": "operations", "desc": "Handling pipeline failures and escalations swiftly"},
    ],
    "analytics-vp": [
        {"name": "data-interpretation", "category": "analytics", "desc": "Turning YouTube metrics into actionable content decisions"},
        {"name": "performance-tracking", "category": "analytics", "desc": "Monitoring KPIs across channels, videos, and revenue streams"},
        {"name": "trend-forecasting", "category": "analytics", "desc": "Predicting which topics will trend before they peak"},
        {"name": "ab-testing", "category": "analytics", "desc": "Designing experiments for thumbnails, titles, and content"},
        {"name": "reporting", "category": "analytics", "desc": "Creating clear dashboards and reports for strategic decisions"},
    ],
    "monetization-vp": [
        {"name": "revenue-optimization", "category": "monetization", "desc": "Maximizing CPM, RPM, and total revenue across channels"},
        {"name": "sponsorship-strategy", "category": "monetization", "desc": "Identifying and landing high-value brand deals"},
        {"name": "product-strategy", "category": "monetization", "desc": "Designing digital products that complement content"},
        {"name": "affiliate-architecture", "category": "monetization", "desc": "Building systematic affiliate revenue streams"},
        {"name": "diversification", "category": "monetization", "desc": "Expanding beyond AdSense into sustainable revenue mix"},
    ],

    # ── TIER 3: Channel Managers ──
    "ai-and-tech-channel-manager": [
        {"name": "ai-domain-expertise", "category": "domain", "desc": "Deep knowledge of AI tools, systems, and industry trends"},
        {"name": "channel-positioning", "category": "strategy", "desc": "Positioning AI & Tech channel for maximum authority"},
        {"name": "content-curation", "category": "editorial", "desc": "Selecting which AI stories deserve full episodes"},
        {"name": "audience-engagement", "category": "community", "desc": "Understanding what AI-curious audiences want to learn"},
    ],
    "finance-and-business-channel-manager": [
        {"name": "finance-domain-expertise", "category": "domain", "desc": "Deep knowledge of business, fintech, and economic trends"},
        {"name": "channel-positioning", "category": "strategy", "desc": "Positioning Finance channel for professional credibility"},
        {"name": "content-curation", "category": "editorial", "desc": "Selecting compelling business stories and case studies"},
        {"name": "data-storytelling", "category": "editorial", "desc": "Turning financial data into engaging narratives"},
    ],
    "psychology-and-behavior-channel-manager": [
        {"name": "psychology-domain-expertise", "category": "domain", "desc": "Deep knowledge of behavioral science and human psychology"},
        {"name": "channel-positioning", "category": "strategy", "desc": "Positioning Psychology channel for mass curiosity appeal"},
        {"name": "human-interest-angles", "category": "editorial", "desc": "Finding the human story in every psychological concept"},
        {"name": "emotional-resonance", "category": "editorial", "desc": "Crafting content that makes viewers feel deeply understood"},
    ],

    # ── TIER 4: Production Specialists ──
    "trend-researcher": [
        {"name": "trend-analysis", "category": "research", "desc": "Identifying trending topics and angles with data backing"},
        {"name": "data-sourcing", "category": "research", "desc": "Finding credible statistics, studies, and real-world examples"},
        {"name": "competitor-analysis", "category": "research", "desc": "Analyzing what competitors are doing and finding gaps"},
        {"name": "audience-psychology", "category": "research", "desc": "Understanding what the target audience craves"},
        {"name": "source-verification", "category": "research", "desc": "Validating data credibility and cross-referencing claims"},
    ],
    "scriptwriter": [
        {"name": "hook-writing", "category": "scripting", "desc": "Writing scroll-stopping opening hooks that grab in 3 seconds"},
        {"name": "narrative-structure", "category": "scripting", "desc": "Building compelling 3-act story arcs for documentaries"},
        {"name": "dialogue-craft", "category": "scripting", "desc": "Writing natural, engaging voiceover copy that flows"},
        {"name": "pattern-interrupts", "category": "scripting", "desc": "Inserting retention-boosting surprises every 15-20s"},
        {"name": "emotional-pacing", "category": "scripting", "desc": "Managing tension, revelation, and payoff rhythm"},
        {"name": "information-density", "category": "scripting", "desc": "Packing maximum value without overwhelming the viewer"},
    ],
    "storyteller": [
        {"name": "narrative-architecture", "category": "storytelling", "desc": "Designing overarching story structures that captivate"},
        {"name": "character-development", "category": "storytelling", "desc": "Building relatable characters and case studies"},
        {"name": "tension-building", "category": "storytelling", "desc": "Creating suspense and anticipation throughout the story"},
        {"name": "metaphor-craft", "category": "storytelling", "desc": "Using vivid metaphors to explain complex concepts"},
        {"name": "emotional-payoff", "category": "storytelling", "desc": "Delivering satisfying conclusions that stick with viewers"},
    ],
    "hook-specialist": [
        {"name": "curiosity-gaps", "category": "hooks", "desc": "Creating irresistible curiosity that demands the click"},
        {"name": "pattern-disruption", "category": "hooks", "desc": "Breaking viewer expectations to force attention"},
        {"name": "emotional-triggers", "category": "hooks", "desc": "Activating fear, wonder, or urgency in the first 5 seconds"},
        {"name": "title-craft", "category": "hooks", "desc": "Writing titles that maximize both CTR and watch time"},
        {"name": "retention-engineering", "category": "hooks", "desc": "Designing hooks that keep viewers past the 30-second mark"},
    ],
    "voice-director": [
        {"name": "voice-direction", "category": "voiceover", "desc": "Crafting precise delivery instructions for AI voice (Julian)"},
        {"name": "pacing-design", "category": "voiceover", "desc": "Designing pauses, emphasis, and tempo changes for impact"},
        {"name": "audio-mixing", "category": "voiceover", "desc": "Balancing voice with music and sound design layers"},
        {"name": "emotional-delivery", "category": "voiceover", "desc": "Directing vocal tone to match narrative emotional beats"},
        {"name": "elevenlabs-mastery", "category": "voiceover", "desc": "Optimizing ElevenLabs settings for maximum voice quality"},
    ],
    "thumbnail-designer": [
        {"name": "visual-composition", "category": "thumbnail", "desc": "Creating eye-catching thumbnail layouts that pop"},
        {"name": "click-psychology", "category": "thumbnail", "desc": "Using curiosity gaps and emotion to drive clicks"},
        {"name": "brand-consistency", "category": "thumbnail", "desc": "Maintaining V-Real AI visual identity across thumbnails"},
        {"name": "color-theory", "category": "thumbnail", "desc": "Using contrast and color psychology for maximum impact"},
        {"name": "text-hierarchy", "category": "thumbnail", "desc": "Placing text for readability at 120px mobile preview"},
    ],
    "video-editor": [
        {"name": "scene-composition", "category": "editing", "desc": "Building dynamic scene-by-scene edit briefs"},
        {"name": "footage-selection", "category": "editing", "desc": "Choosing the right stock footage and B-roll for each scene"},
        {"name": "transition-design", "category": "editing", "desc": "Designing smooth, engaging transitions between scenes"},
        {"name": "retention-engineering", "category": "editing", "desc": "Keeping no static shot >2s, constant visual movement"},
        {"name": "color-grading", "category": "editing", "desc": "Applying cinematic color grades for documentary feel"},
        {"name": "motion-graphics", "category": "editing", "desc": "Directing kinetic text, data overlays, and visual effects"},
    ],
    "seo-specialist": [
        {"name": "keyword-research", "category": "seo", "desc": "Finding high-volume, low-competition keywords"},
        {"name": "title-optimization", "category": "seo", "desc": "Crafting titles that maximize CTR and search ranking"},
        {"name": "metadata-craft", "category": "seo", "desc": "Writing descriptions, tags, and chapters for discoverability"},
        {"name": "algorithm-awareness", "category": "seo", "desc": "Understanding YouTube recommendation and search systems"},
        {"name": "trending-optimization", "category": "seo", "desc": "Timing content release to ride trending search waves"},
    ],
    "shorts-and-clips-agent": [
        {"name": "clip-extraction", "category": "shorts", "desc": "Identifying the most viral-worthy moments from long-form"},
        {"name": "vertical-editing", "category": "shorts", "desc": "Adapting horizontal content to engaging vertical format"},
        {"name": "hook-compression", "category": "shorts", "desc": "Compressing hooks into 1-second attention grabbers"},
        {"name": "shorts-algorithm", "category": "shorts", "desc": "Optimizing for YouTube Shorts recommendation system"},
    ],

    # ── TIER 5: Operations ──
    "quality-assurance-lead": [
        {"name": "quality-evaluation", "category": "qa", "desc": "Scoring content against BBC/Netflix documentary standards"},
        {"name": "feedback-delivery", "category": "qa", "desc": "Giving specific, actionable feedback that improves output"},
        {"name": "standard-enforcement", "category": "qa", "desc": "Maintaining consistent 10/10 quality bar across all stages"},
        {"name": "pattern-detection", "category": "qa", "desc": "Identifying recurring quality issues across episodes"},
        {"name": "revision-guidance", "category": "qa", "desc": "Directing revision loops toward efficient improvement"},
    ],
    "project-manager": [
        {"name": "pipeline-management", "category": "management", "desc": "Keeping production jobs on track from research to publish"},
        {"name": "deadline-tracking", "category": "management", "desc": "Ensuring episodes hit target publication dates"},
        {"name": "blocker-resolution", "category": "management", "desc": "Identifying and clearing obstacles in the pipeline"},
        {"name": "resource-coordination", "category": "management", "desc": "Assigning the right agents to the right tasks"},
    ],
    "workflow-orchestrator": [
        {"name": "pipeline-automation", "category": "automation", "desc": "Designing automated workflows between pipeline stages"},
        {"name": "trigger-design", "category": "automation", "desc": "Setting up event-based triggers for pipeline advancement"},
        {"name": "error-recovery", "category": "automation", "desc": "Building resilient pipelines that recover from failures"},
        {"name": "efficiency-optimization", "category": "automation", "desc": "Reducing pipeline cycle time through parallel processing"},
    ],
    "automation-engineer": [
        {"name": "api-integration", "category": "engineering", "desc": "Connecting external APIs (ElevenLabs, Pexels, YouTube)"},
        {"name": "ffmpeg-mastery", "category": "engineering", "desc": "Assembling videos programmatically with FFmpeg"},
        {"name": "service-architecture", "category": "engineering", "desc": "Building reliable microservices for content pipeline"},
        {"name": "monitoring", "category": "engineering", "desc": "Setting up alerts and health checks for all services"},
    ],
    "reflection-council": [
        {"name": "strategic-analysis", "category": "strategy", "desc": "Analyzing channel performance for strategic pivots"},
        {"name": "retrospective-facilitation", "category": "strategy", "desc": "Running post-episode reviews to extract lessons"},
        {"name": "cross-agent-insight", "category": "strategy", "desc": "Synthesizing insights from multiple agents into strategy"},
        {"name": "long-term-planning", "category": "strategy", "desc": "Setting quarterly goals and tracking progress"},
    ],
    "finance-controller": [
        {"name": "revenue-tracking", "category": "finance", "desc": "Monitoring all income streams (AdSense, sponsors, products)"},
        {"name": "cost-analysis", "category": "finance", "desc": "Tracking expenses (API costs, tools, services) per episode"},
        {"name": "profit-forecasting", "category": "finance", "desc": "Projecting revenue growth and expense trends"},
        {"name": "budget-management", "category": "finance", "desc": "Allocating budget for maximum ROI across operations"},
        {"name": "financial-reporting", "category": "finance", "desc": "Generating clear P&L reports and financial dashboards"},
    ],

    # ── TIER 6: Analytics ──
    "senior-researcher": [
        {"name": "deep-research", "category": "research", "desc": "Conducting thorough multi-source research investigations"},
        {"name": "quality-review", "category": "research", "desc": "Reviewing and scoring research output for completeness"},
        {"name": "methodology-design", "category": "research", "desc": "Creating systematic research frameworks (Wow Filter etc)"},
        {"name": "fact-checking", "category": "research", "desc": "Verifying claims, statistics, and source credibility"},
        {"name": "insight-synthesis", "category": "research", "desc": "Connecting disparate data points into compelling narratives"},
    ],
    "data-analyst": [
        {"name": "youtube-analytics", "category": "analytics", "desc": "Interpreting watch time, CTR, retention, and revenue data"},
        {"name": "audience-segmentation", "category": "analytics", "desc": "Identifying viewer demographics and behavior patterns"},
        {"name": "performance-benchmarking", "category": "analytics", "desc": "Comparing channel metrics against competitors"},
        {"name": "data-visualization", "category": "analytics", "desc": "Creating clear charts and dashboards for decision-making"},
    ],

    # ── TIER 7: Monetization ──
    "partnership-manager": [
        {"name": "sponsor-outreach", "category": "partnerships", "desc": "Identifying and pitching to potential brand sponsors"},
        {"name": "deal-negotiation", "category": "partnerships", "desc": "Negotiating rates and terms for sponsorship deals"},
        {"name": "relationship-management", "category": "partnerships", "desc": "Maintaining long-term brand partner relationships"},
        {"name": "integration-design", "category": "partnerships", "desc": "Designing natural sponsor integrations that don't feel forced"},
    ],
    "affiliate-coordinator": [
        {"name": "affiliate-research", "category": "affiliate", "desc": "Finding high-converting affiliate programs for AI tools"},
        {"name": "link-optimization", "category": "affiliate", "desc": "Placing affiliate links for maximum click-through"},
        {"name": "conversion-tracking", "category": "affiliate", "desc": "Monitoring affiliate revenue and optimizing placements"},
        {"name": "disclosure-compliance", "category": "affiliate", "desc": "Ensuring all affiliate links are properly disclosed"},
    ],
    "newsletter-strategist": [
        {"name": "list-growth", "category": "newsletter", "desc": "Growing email subscriber base from YouTube viewers"},
        {"name": "content-repurposing", "category": "newsletter", "desc": "Turning video content into compelling newsletter editions"},
        {"name": "email-copywriting", "category": "newsletter", "desc": "Writing emails that get opened, read, and clicked"},
        {"name": "monetization-integration", "category": "newsletter", "desc": "Weaving sponsors and affiliates into newsletter content"},
    ],
    "digital-product-manager": [
        {"name": "product-ideation", "category": "products", "desc": "Identifying digital products the audience would buy"},
        {"name": "launch-strategy", "category": "products", "desc": "Planning and executing product launches from the channel"},
        {"name": "pricing-strategy", "category": "products", "desc": "Setting optimal prices for courses, templates, and guides"},
        {"name": "funnel-design", "category": "products", "desc": "Building viewer→subscriber→customer conversion funnels"},
    ],

    # ── TIER 8: Community ──
    "community-manager": [
        {"name": "comment-engagement", "category": "community", "desc": "Responding to comments that boost engagement and loyalty"},
        {"name": "community-building", "category": "community", "desc": "Fostering an active, positive community around the channel"},
        {"name": "sentiment-analysis", "category": "community", "desc": "Reading audience mood and flagging concerns early"},
        {"name": "feedback-collection", "category": "community", "desc": "Gathering viewer feedback to improve content strategy"},
    ],
    "social-media-manager": [
        {"name": "cross-platform-strategy", "category": "social", "desc": "Promoting content across Twitter, LinkedIn, Reddit, etc."},
        {"name": "content-adaptation", "category": "social", "desc": "Adapting video content for each social platform's format"},
        {"name": "engagement-tactics", "category": "social", "desc": "Driving discussion, shares, and traffic back to YouTube"},
        {"name": "trend-hijacking", "category": "social", "desc": "Jumping on social trends to amplify video reach"},
    ],
    "secretary-agent": [
        {"name": "scheduling", "category": "admin", "desc": "Managing publishing schedules and content calendars"},
        {"name": "communication", "category": "admin", "desc": "Coordinating messages between agents and Pedro"},
        {"name": "documentation", "category": "admin", "desc": "Maintaining organized records of all decisions and actions"},
        {"name": "prioritization", "category": "admin", "desc": "Triaging tasks and escalations by urgency and importance"},
    ],

    # ── TIER 9: Compliance ──
    "compliance-officer": [
        {"name": "youtube-policy", "category": "compliance", "desc": "Ensuring all content follows YouTube Terms of Service"},
        {"name": "copyright-review", "category": "compliance", "desc": "Checking footage, music, and content for copyright issues"},
        {"name": "disclosure-compliance", "category": "compliance", "desc": "Ensuring FTC/regulatory disclosure requirements are met"},
        {"name": "brand-safety", "category": "compliance", "desc": "Protecting the channel from controversial or risky content"},
        {"name": "legal-awareness", "category": "compliance", "desc": "Flagging potential legal issues before they become problems"},
    ],
}

# ═══════════════════════════════════════════════════════════════════
# UNIVERSAL SKILLS — Every agent gets these (meta-prompting + learning)
# ═══════════════════════════════════════════════════════════════════

UNIVERSAL_SKILLS = [
    {
        "name": "meta-prompting",
        "category": "meta",
        "desc": "Self-improving prompt engineering — refining own instructions based on past failures and successes to produce better outputs each iteration",
    },
    {
        "name": "self-reflection",
        "category": "meta",
        "desc": "Analyzing own output quality before submission, catching issues proactively",
    },
    {
        "name": "feedback-integration",
        "category": "meta",
        "desc": "Absorbing reviewer, pressure test, and Pedro feedback to permanently improve approach",
    },
    {
        "name": "cross-agent-collaboration",
        "category": "meta",
        "desc": "Working effectively with other agents, understanding handoff quality requirements",
    },
]


# ═══════════════════════════════════════════════════════════════════
# AGENT TIER LOOKUP (agent_id → tier number)
# ═══════════════════════════════════════════════════════════════════

AGENT_TIERS = {
    "ceo-agent": 1,
    "content-vp": 2, "operations-vp": 2, "analytics-vp": 2, "monetization-vp": 2,
    "ai-and-tech-channel-manager": 3, "finance-and-business-channel-manager": 3, "psychology-and-behavior-channel-manager": 3,
    "trend-researcher": 4, "scriptwriter": 4, "storyteller": 4, "hook-specialist": 4,
    "voice-director": 4, "thumbnail-designer": 4, "video-editor": 4, "seo-specialist": 4, "shorts-and-clips-agent": 4,
    "quality-assurance-lead": 5, "project-manager": 5, "workflow-orchestrator": 5,
    "automation-engineer": 5, "reflection-council": 5, "finance-controller": 5,
    "senior-researcher": 6, "data-analyst": 6,
    "partnership-manager": 7, "affiliate-coordinator": 7, "newsletter-strategist": 7, "digital-product-manager": 7,
    "community-manager": 8, "social-media-manager": 8, "secretary-agent": 8,
    "compliance-officer": 9,
}


async def seed_baseline_skills():
    """
    Seed all agents with their role-appropriate baseline skills.
    Only creates skills that don't already exist (safe to run multiple times).
    Returns count of new skills created.
    """
    created = 0
    async with async_session() as db:
        for agent_id, skills in AGENT_BASELINE_SKILLS.items():
            tier = AGENT_TIERS.get(agent_id, 5)
            starting_level = TIER_STARTING_LEVEL.get(tier, 2)
            starting_xp = LEVEL_STARTING_XP.get(starting_level, 10)

            # Add universal skills (meta-prompting, self-reflection, etc.)
            all_skills = skills + UNIVERSAL_SKILLS

            for skill_def in all_skills:
                # Check if skill already exists
                existing = await db.execute(
                    select(AgentSkill).where(
                        AgentSkill.agent_id == agent_id,
                        AgentSkill.skill_name == skill_def["name"],
                    )
                )
                if existing.scalar_one_or_none():
                    continue  # Already seeded

                # Meta skills start 1 level lower (they grow through practice)
                level = starting_level if skill_def["category"] != "meta" else max(1, starting_level - 1)
                xp = LEVEL_STARTING_XP.get(level, 10)

                skill = AgentSkill(
                    id=str(uuid.uuid4()),
                    agent_id=agent_id,
                    skill_name=skill_def["name"],
                    category=skill_def["category"],
                    level=level,
                    xp=xp,
                    description=skill_def["desc"],
                    times_used=0,
                    total_uses=0,
                    first_try_passes_with_skill=0,
                    best_score=0,
                    evidence=[{"episode": "Baseline", "score": level * 2, "date": "2026-04-06", "first_try": True}],
                )
                db.add(skill)
                created += 1

                # Write physical skill file
                try:
                    write_skill_file(
                        agent_id, skill_def["name"], level, xp,
                        skill_def["desc"],
                        [{"episode": "Baseline", "score": level * 2, "date": "2026-04-06"}],
                    )
                except Exception as e:
                    print(f"[SKILL SEEDER] Could not write file for {agent_id}/{skill_def['name']}: {e}")

        await db.commit()
    return created

