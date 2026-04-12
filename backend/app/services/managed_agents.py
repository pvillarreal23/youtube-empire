"""Claude Managed Agents service for YouTube Empire automation.

Registers 6 consolidated agents on the Claude Platform and provides
workflow execution via Managed Agent sessions with SSE streaming.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import AsyncGenerator

import anthropic
import frontmatter
from app.config import ANTHROPIC_API_KEY, AGENTS_DIR

# ---------------------------------------------------------------------------
# Agent prompt loader
# ---------------------------------------------------------------------------

def _load_prompt(filename: str) -> str:
    """Load the markdown body (system prompt) from an agent .md file."""
    path = AGENTS_DIR / filename
    if not path.exists():
        return ""
    post = frontmatter.load(str(path))
    return post.content.strip()


def _combine_prompts(filenames: list[str], preamble: str) -> str:
    """Merge several agent prompts into one system prompt with a preamble."""
    sections = [preamble.strip()]
    for fn in filenames:
        body = _load_prompt(fn)
        if body:
            sections.append(f"---\n\n{body}")
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Channel definitions
# ---------------------------------------------------------------------------

CHANNELS = {
    "ai-tech": {
        "name": "AI & Tech",
        "manager_prompt": "ai_tech_channel_manager.md",
        "description": "AI tools, tech news, tutorials, and the future of technology",
    },
    "finance": {
        "name": "Finance",
        "manager_prompt": "finance_channel_manager.md",
        "description": "Investing, money management, wealth building, and market analysis",
    },
    "psychology": {
        "name": "Psychology",
        "manager_prompt": "psychology_channel_manager.md",
        "description": "Behavioral psychology, relationships, habits, and mental health",
    },
}

# ---------------------------------------------------------------------------
# Managed Agent configurations
# ---------------------------------------------------------------------------

AGENT_CONFIGS = {
    "content-creator": {
        "name": "Content Creator",
        "description": "Researches trends, writes scripts, crafts hooks, and designs narrative arcs for YouTube videos.",
        "model": "claude-sonnet-4-6",
        "prompt_files": [
            "trend_researcher_agent.md",
            "scriptwriter_agent.md",
            "hook_specialist_agent.md",
            "storyteller_agent.md",
        ],
        "preamble": (
            "You are the Content Creator for a multi-channel YouTube empire. "
            "You combine the expertise of a Trend Researcher, Scriptwriter, Hook Specialist, and Storyteller. "
            "Your job is to research what's trending, identify high-potential video topics, and produce complete, "
            "retention-optimized scripts with compelling hooks and narrative arcs.\n\n"
            "Always structure your output with clear sections:\n"
            "1. TOPIC RESEARCH — trending topics with data backing\n"
            "2. VIDEO IDEAS — 3 ranked ideas per channel with rationale\n"
            "3. FULL SCRIPT — for the top idea, with hook, story beats, and CTA\n"
            "4. HOOK VARIATIONS — 3 alternative opening hooks\n"
            "5. NARRATIVE NOTES — story framework used, emotional arc, tension map"
        ),
    },
    "seo-optimizer": {
        "name": "SEO Optimizer",
        "description": "Optimizes video metadata — titles, descriptions, tags, chapters — and designs thumbnail concepts.",
        "model": "claude-sonnet-4-6",
        "prompt_files": [
            "seo_specialist_agent.md",
            "thumbnail_designer_agent.md",
        ],
        "preamble": (
            "You are the SEO Optimizer for a multi-channel YouTube empire. "
            "You combine the expertise of an SEO Specialist and Thumbnail Designer. "
            "Your job is to maximize discoverability and click-through rate for every video.\n\n"
            "Always structure your output with clear sections:\n"
            "1. TITLE OPTIONS — 3 SEO-optimized titles ranked by CTR potential\n"
            "2. DESCRIPTION — full YouTube description with keywords, links, timestamps\n"
            "3. TAGS — 15-20 relevant tags ordered by search volume\n"
            "4. CHAPTERS — timestamped chapter markers with keyword-rich labels\n"
            "5. THUMBNAIL CONCEPTS — 3 thumbnail designs with layout, text, emotion, colors"
        ),
    },
    "community-manager": {
        "name": "Community Manager",
        "description": "Manages community engagement — comment replies, social media posts, and community posts.",
        "model": "claude-sonnet-4-6",
        "prompt_files": [
            "community_manager_agent.md",
            "social_media_manager_agent.md",
        ],
        "preamble": (
            "You are the Community Manager for a multi-channel YouTube empire. "
            "You combine the expertise of a Community Manager and Social Media Manager. "
            "Your job is to keep the audience engaged across all platforms.\n\n"
            "Always structure your output with clear sections:\n"
            "1. YOUTUBE COMMUNITY POSTS — 1 post per channel with poll/question ideas\n"
            "2. SOCIAL MEDIA POSTS — Twitter/X thread, Instagram caption, LinkedIn post\n"
            "3. COMMENT REPLY TEMPLATES — 5 templates for common comment types\n"
            "4. ENGAGEMENT STRATEGY — weekly engagement plan with specific actions"
        ),
    },
    "analytics-reporter": {
        "name": "Analytics Reporter",
        "description": "Analyzes channel performance and produces actionable reports with growth recommendations.",
        "model": "claude-sonnet-4-6",
        "prompt_files": [
            "data_analyst_agent.md",
            "analytics_vp_agent.md",
        ],
        "preamble": (
            "You are the Analytics Reporter for a multi-channel YouTube empire. "
            "You combine the expertise of a Data Analyst and Analytics VP. "
            "Your job is to analyze performance and produce actionable insights.\n\n"
            "Always structure your output with clear sections:\n"
            "1. EXECUTIVE SUMMARY — top-line metrics and key takeaways\n"
            "2. CHANNEL PERFORMANCE — per-channel breakdown (views, subs, revenue, retention)\n"
            "3. TOP PERFORMERS — what worked and why\n"
            "4. UNDERPERFORMERS — what didn't work and diagnosis\n"
            "5. RECOMMENDATIONS — specific, actionable next steps ranked by impact\n"
            "6. GROWTH FORECAST — projected trajectory based on current trends"
        ),
    },
    "strategy-director": {
        "name": "Strategy Director",
        "description": "Sets strategic direction — content calendars, OKRs, and organizational priorities.",
        "model": "claude-sonnet-4-6",
        "prompt_files": [
            "ceo_agent.md",
            "content_vp_agent.md",
            "reflection_council_agent.md",
        ],
        "preamble": (
            "You are the Strategy Director for a multi-channel YouTube empire. "
            "You combine the strategic vision of a CEO, the editorial expertise of a Content VP, "
            "and the critical thinking of a Reflection Council. "
            "Your job is to set direction, plan content calendars, and ensure the empire grows.\n\n"
            "Always structure your output with clear sections:\n"
            "1. WEEKLY EXECUTIVE SUMMARY — state of the empire\n"
            "2. CONTENT CALENDAR — next week's plan for all 3 channels (titles, formats, goals)\n"
            "3. STRATEGIC PRIORITIES — top 3 focus areas with rationale\n"
            "4. RISKS & OPPORTUNITIES — what to watch for\n"
            "5. OKR CHECK-IN — progress against quarterly goals\n"
            "6. DEVIL'S ADVOCATE — challenging our assumptions"
        ),
    },
    "revenue-manager": {
        "name": "Revenue Manager",
        "description": "Manages monetization — newsletters, sponsorships, affiliates, and revenue optimization.",
        "model": "claude-sonnet-4-6",
        "prompt_files": [
            "monetization_vp_agent.md",
            "newsletter_strategist_agent.md",
            "affiliate_coordinator_agent.md",
        ],
        "preamble": (
            "You are the Revenue Manager for a multi-channel YouTube empire. "
            "You combine the expertise of a Monetization VP, Newsletter Strategist, and Affiliate Coordinator. "
            "Your job is to maximize and diversify revenue.\n\n"
            "Always structure your output with clear sections:\n"
            "1. NEWSLETTER DRAFT — ready-to-send weekly newsletter with subject line\n"
            "2. SPONSORSHIP OPPORTUNITIES — brands to pitch with rationale and rate suggestions\n"
            "3. AFFILIATE RECOMMENDATIONS — products/services to promote per channel\n"
            "4. REVENUE HEALTH — diversification check (no stream > 40%)\n"
            "5. MONETIZATION IDEAS — new revenue experiments to test"
        ),
    },
}

# ---------------------------------------------------------------------------
# Workflow definitions
# ---------------------------------------------------------------------------

WORKFLOWS = {
    "content-pipeline": {
        "name": "Weekly Content Pipeline",
        "description": "Research trends, write scripts, craft hooks, and generate SEO metadata for all 3 channels.",
        "agents": ["content-creator", "seo-optimizer"],
        "channel_specific": True,
        "task_template": (
            "You are producing content for the **{channel_name}** YouTube channel.\n"
            "Channel focus: {channel_desc}\n\n"
            "Complete these tasks:\n"
            "1. Research the latest trending topics in this niche using web search\n"
            "2. Generate 3 video ideas ranked by viral potential, with search volume and competition analysis\n"
            "3. Write a FULL video script for the #1 idea (aim for 10-12 minute video)\n"
            "4. Create 3 hook variations for the opening 30 seconds\n"
            "5. Generate complete SEO metadata: 3 title options, full description, 15+ tags, chapter timestamps\n"
            "6. Describe 3 thumbnail concepts with layout, text overlay, colors, and emotion\n\n"
            "Use web search to find real trending topics, news, and data. Be specific and current."
        ),
    },
    "analytics-report": {
        "name": "Analytics Report",
        "description": "Analyze channel performance and produce an actionable report with growth recommendations.",
        "agents": ["analytics-reporter"],
        "channel_specific": False,
        "task_template": (
            "Produce a comprehensive analytics report for a YouTube empire with 3 channels:\n"
            "- AI & Tech (tutorials, news, tool reviews)\n"
            "- Finance (investing, money management, wealth building)\n"
            "- Psychology (behavioral science, relationships, habits)\n\n"
            "Tasks:\n"
            "1. Research current YouTube trends and algorithm changes that affect these niches\n"
            "2. Analyze what types of content are performing best in each niche right now (use web search)\n"
            "3. Identify the top-performing video formats, lengths, and topics in each category\n"
            "4. Provide specific, actionable recommendations for each channel\n"
            "5. Forecast growth opportunities for the next 30 days\n"
            "6. Flag any risks (algorithm changes, competitor moves, audience fatigue)\n\n"
            "Use web search to get real, current data. Include specific examples and numbers."
        ),
    },
    "community-engagement": {
        "name": "Community Engagement",
        "description": "Draft community posts, social media content, and comment reply templates for all channels.",
        "agents": ["community-manager"],
        "channel_specific": True,
        "task_template": (
            "You are managing community engagement for the **{channel_name}** YouTube channel.\n"
            "Channel focus: {channel_desc}\n\n"
            "Complete these tasks:\n"
            "1. Draft 2 YouTube Community posts (1 poll, 1 discussion question) tailored to this audience\n"
            "2. Write a Twitter/X thread (5-7 tweets) about a trending topic in this niche\n"
            "3. Write an Instagram carousel caption (educational, 200-300 words)\n"
            "4. Write a LinkedIn post (professional angle on the same topic)\n"
            "5. Create 5 comment reply templates for: praise, question, criticism, suggestion, troll\n"
            "6. Recommend 3 engagement tactics to boost community interaction this week\n\n"
            "Use web search to find current trending topics to base the content on. Be authentic and engaging."
        ),
    },
    "strategy-review": {
        "name": "Weekly Strategy Review",
        "description": "Executive review with content calendar, strategic priorities, and risk assessment.",
        "agents": ["strategy-director"],
        "channel_specific": False,
        "task_template": (
            "Conduct a weekly strategy review for a YouTube empire with 3 channels:\n"
            "- AI & Tech (tutorials, news, tool reviews)\n"
            "- Finance (investing, money management, wealth building)\n"
            "- Psychology (behavioral science, relationships, habits)\n\n"
            "Tasks:\n"
            "1. Research what's happening in each niche this week (use web search for current events)\n"
            "2. Create a detailed content calendar for next week — 2 videos per channel with:\n"
            "   - Working title, format, target length, publish day/time\n"
            "   - Brief description and why this topic now\n"
            "3. Identify top 3 strategic priorities with rationale\n"
            "4. Assess risks and opportunities (algorithm changes, competitor moves, trending events)\n"
            "5. Play devil's advocate — challenge the current strategy and suggest alternatives\n"
            "6. Set 3 measurable goals for the week\n\n"
            "Be specific and actionable. Use real, current information from web searches."
        ),
    },
    "revenue-newsletter": {
        "name": "Revenue & Newsletter",
        "description": "Draft weekly newsletter, identify sponsorship opportunities, and recommend affiliate products.",
        "agents": ["revenue-manager"],
        "channel_specific": False,
        "task_template": (
            "Manage revenue and produce newsletter content for a YouTube empire with 3 channels:\n"
            "- AI & Tech (tutorials, news, tool reviews)\n"
            "- Finance (investing, money management, wealth building)\n"
            "- Psychology (behavioral science, relationships, habits)\n\n"
            "Tasks:\n"
            "1. Write a complete weekly newsletter (subject line + body) that:\n"
            "   - Highlights the week's best content across all channels\n"
            "   - Includes an exclusive insight not in the videos\n"
            "   - Has a clear CTA (reply, share, product recommendation)\n"
            "   - Follows 60% value / 20% curation / 15% promotion / 5% community\n"
            "2. Research and recommend 3 brands to pitch for sponsorship (use web search)\n"
            "   - Include why they're a fit, suggested rate, and talking points\n"
            "3. Recommend affiliate products/services for each channel's upcoming content\n"
            "4. Assess revenue diversification — flag if any stream might exceed 40%\n"
            "5. Propose 2 new monetization experiments to test this month\n\n"
            "Use web search for real brands, products, and current market rates."
        ),
    },
}

# ---------------------------------------------------------------------------
# Client & registration
# ---------------------------------------------------------------------------

_registered_agents: dict[str, str] = {}  # local_id -> managed_agent_id
_environment_id: str | None = None


def get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


async def register_agents() -> dict[str, str]:
    """Register all managed agents on the Claude Platform. Returns mapping of local_id -> platform_id."""
    global _registered_agents
    client = get_client()

    for local_id, cfg in AGENT_CONFIGS.items():
        system_prompt = _combine_prompts(cfg["prompt_files"], cfg["preamble"])
        try:
            agent = client.beta.agents.create(
                name=cfg["name"],
                description=cfg.get("description", ""),
                model=cfg["model"],
                system=system_prompt,
                tools=[{"type": "agent_toolset_20260401"}],
            )
            _registered_agents[local_id] = agent.id
            print(f"  Registered managed agent: {cfg['name']} -> {agent.id}")
        except Exception as e:
            print(f"  Failed to register {cfg['name']}: {e}")

    return _registered_agents


async def ensure_environment() -> str:
    """Create or return the shared cloud environment."""
    global _environment_id
    if _environment_id:
        return _environment_id

    client = get_client()
    try:
        env = client.beta.environments.create(
            name="youtube-empire-env",
            config={
                "type": "cloud",
                "networking": {"type": "unrestricted"},
            },
        )
        _environment_id = env.id
        print(f"  Created environment: {_environment_id}")
    except Exception as e:
        print(f"  Failed to create environment: {e}")
        raise

    return _environment_id


# ---------------------------------------------------------------------------
# Workflow execution
# ---------------------------------------------------------------------------

def _build_task(workflow_id: str, channel: str | None) -> str:
    """Build the task prompt for a workflow, substituting channel info."""
    wf = WORKFLOWS[workflow_id]
    template = wf["task_template"]

    if channel and channel in CHANNELS:
        ch = CHANNELS[channel]
        return template.format(channel_name=ch["name"], channel_desc=ch["description"])

    return template


def run_workflow_session(
    workflow_id: str,
    channel: str | None = None,
) -> tuple[str, str]:
    """Create a session and send the task. Returns (session_id, agent_name).

    Uses the first agent in the workflow's agent list.
    """
    wf = WORKFLOWS[workflow_id]
    agent_local_id = wf["agents"][0]

    if agent_local_id not in _registered_agents:
        raise ValueError(
            f"Agent '{agent_local_id}' not registered. "
            "Ensure register_agents() was called on startup."
        )

    platform_agent_id = _registered_agents[agent_local_id]
    env_id = _environment_id

    if not env_id:
        raise ValueError("Environment not created. Ensure ensure_environment() was called.")

    client = get_client()

    session = client.beta.sessions.create(
        agent=platform_agent_id,
        environment_id=env_id,
    )

    task = _build_task(workflow_id, channel)

    # Send the task as a user message
    client.beta.sessions.events.send(
        session.id,
        events=[
            {
                "type": "user.message",
                "content": [{"type": "text", "text": task}],
            }
        ],
    )

    agent_name = AGENT_CONFIGS[agent_local_id]["name"]
    return session.id, agent_name


def stream_session_events(session_id: str) -> AsyncGenerator[dict, None]:
    """Stream events from a managed agent session as dicts.

    Yields serialized event dicts suitable for SSE.
    """
    client = get_client()

    with client.beta.sessions.events.stream(session_id) as stream:
        for event in stream:
            evt = {"type": event.type}

            if event.type == "agent.message":
                text_parts = []
                for block in event.content:
                    if hasattr(block, "text"):
                        text_parts.append(block.text)
                evt["text"] = "".join(text_parts)

            elif event.type == "agent.tool_use":
                evt["tool"] = getattr(event, "name", "unknown")
                evt["text"] = f"[Using tool: {evt['tool']}]"

            elif event.type == "session.status_idle":
                evt["text"] = ""
                yield evt
                return  # session complete

            else:
                evt["text"] = ""

            yield evt


# ---------------------------------------------------------------------------
# Convenience: list workflows for API
# ---------------------------------------------------------------------------

def list_workflows() -> list[dict]:
    """Return workflow metadata for the API."""
    out = []
    for wf_id, wf in WORKFLOWS.items():
        out.append({
            "id": wf_id,
            "name": wf["name"],
            "description": wf["description"],
            "agents_used": [AGENT_CONFIGS[a]["name"] for a in wf["agents"]],
            "channel_specific": wf["channel_specific"],
        })
    return out


def list_channels() -> list[dict]:
    """Return available channels."""
    return [
        {"id": k, "name": v["name"], "description": v["description"]}
        for k, v in CHANNELS.items()
    ]
