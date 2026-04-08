from __future__ import annotations

import re
from pathlib import Path
import frontmatter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent import Agent
from app.config import AGENTS_DIR

DEPARTMENT_COLORS = {
    "executive": "#8b5cf6",
    "content": "#3b82f6",
    "operations": "#f59e0b",
    "analytics": "#10b981",
    "monetization": "#ef4444",
    "admin": "#6b7280",
}

DEPARTMENT_MAP = {
    "ceo-agent": "executive",
    "content-vp-agent": "content",
    "operations-vp-agent": "operations",
    "analytics-vp-agent": "analytics",
    "monetization-vp-agent": "monetization",
    "secretary-agent": "admin",
    "compliance-officer-agent": "admin",
    "reflection-council-agent": "executive",
    "ai-tech-channel-manager": "content",
    "finance-channel-manager": "content",
    "psychology-channel-manager": "content",
    "scriptwriter-agent": "content",
    "hook-specialist-agent": "content",
    "storyteller-agent": "content",
    "shorts-clips-agent": "content",
    "social-media-manager-agent": "content",
    "project-manager-agent": "operations",
    "workflow-orchestrator-agent": "operations",
    "qa-lead-agent": "operations",
    "video-editor-agent": "operations",
    "thumbnail-designer-agent": "operations",
    "data-analyst-agent": "analytics",
    "trend-researcher-agent": "analytics",
    "seo-specialist-agent": "analytics",
    "senior-researcher-agent": "analytics",
    "partnership-manager-agent": "monetization",
    "affiliate-coordinator-agent": "monetization",
    "digital-product-manager-agent": "monetization",
    "newsletter-strategist-agent": "monetization",
    "community-manager-agent": "monetization",
}


def slugify(name: str) -> str:
    """Convert agent name to a URL-friendly slug."""
    s = name.lower().strip()
    s = re.sub(r"[&]", "and", s)
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s]+", "-", s)
    return s


def resolve_agent_id(name_ref: str, all_agents: dict[str, dict]) -> str | None:
    """Fuzzy match a name reference to an agent id."""
    ref = name_ref.lower().strip()
    # Direct match
    slug = slugify(ref)
    if slug in all_agents:
        return slug
    # Try appending "-agent"
    if slugify(ref + " agent") in all_agents:
        return slugify(ref + " agent")
    # Substring match
    for aid, adata in all_agents.items():
        if ref in adata["name"].lower() or ref in aid:
            return aid
    return None


def parse_agents() -> list[dict]:
    """Parse all agent .md files and return structured data."""
    agents_raw = {}

    for md_file in sorted(AGENTS_DIR.rglob("*.md")):
        # Skip skill files, READMEs, and archived agents
        if "/skills/" in str(md_file) or "/archive/" in str(md_file):
            continue
        if md_file.name.lower() == "readme.md":
            continue
        post = frontmatter.load(str(md_file))
        meta = post.metadata
        name = meta.get("name", md_file.stem.replace("_", " ").title())
        agent_id = slugify(name)

        agents_raw[agent_id] = {
            "id": agent_id,
            "name": name,
            "role": meta.get("role", ""),
            "reports_to_raw": meta.get("reports_to", None),
            "direct_reports_raw": meta.get("direct_reports", []),
            "collaborates_with_raw": meta.get("collaborates_with", []),
            "file_path": str(md_file.relative_to(AGENTS_DIR.parent)),
            "system_prompt": post.content,
        }

    # Resolve references
    agents = []
    for aid, adata in agents_raw.items():
        reports_to = None
        if adata["reports_to_raw"] and "none" not in str(adata["reports_to_raw"]).lower():
            reports_to = resolve_agent_id(str(adata["reports_to_raw"]), agents_raw)

        direct_reports = []
        for dr in adata.get("direct_reports_raw", []) or []:
            resolved = resolve_agent_id(str(dr), agents_raw)
            if resolved:
                direct_reports.append(resolved)

        collaborators = []
        for c in adata.get("collaborates_with_raw", []) or []:
            resolved = resolve_agent_id(str(c), agents_raw)
            if resolved:
                collaborators.append(resolved)

        dept = DEPARTMENT_MAP.get(aid, "general")
        color = DEPARTMENT_COLORS.get(dept, "#6366f1")

        agents.append({
            "id": aid,
            "name": adata["name"],
            "role": adata["role"],
            "reports_to": reports_to,
            "direct_reports": direct_reports,
            "collaborates_with": collaborators,
            "file_path": adata["file_path"],
            "system_prompt": adata["system_prompt"],
            "avatar_color": color,
            "department": dept,
        })

    return agents


async def load_agents_to_db(session: AsyncSession):
    """Parse agent files and upsert into the database."""
    agents_data = parse_agents()
    for a in agents_data:
        existing = await session.get(Agent, a["id"])
        if existing:
            for k, v in a.items():
                setattr(existing, k, v)
        else:
            session.add(Agent(**a))
    await session.commit()


async def get_all_agents(session: AsyncSession) -> list[Agent]:
    result = await session.execute(select(Agent))
    return list(result.scalars().all())


async def get_agent(session: AsyncSession, agent_id: str) -> Agent | None:
    return await session.get(Agent, agent_id)
