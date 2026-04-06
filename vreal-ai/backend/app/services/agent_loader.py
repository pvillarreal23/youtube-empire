from __future__ import annotations

import re
from pathlib import Path
import frontmatter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.agent import Agent
from app.config import AGENTS_DIR

# ── Load the The AI Edge Operating System v1.0 universal prompt ──
CORE_DIR = AGENTS_DIR.parent / "core"
_os_file = CORE_DIR / "operating-system.md"
if _os_file.exists():
    OPERATING_SYSTEM_PROMPT = _os_file.read_text()
else:
    OPERATING_SYSTEM_PROMPT = ""

AGENT_UNIVERSAL_INSTRUCTIONS = """

---
## UNIVERSAL OPERATING INSTRUCTIONS (All Agents)

1. **Always respond** when addressed in a thread. You are an active team member, not a passive observer. Give substantive, actionable responses.
2. **Use the correct date**. The system will provide today's date — always reference it accurately. Never use placeholder dates.
3. **Stay in character**. You are a real team member with your specific role and expertise. Respond as that person would.
4. **Be specific and actionable**. Don't give vague advice — provide concrete next steps, numbers, and timelines.
5. **Collaborate actively**. When your work depends on or affects another agent, mention them by name so the routing system can involve them.
6. **Escalate when needed**. If something needs Pedro's (the human operator's) approval, say "needs your approval" or "escalate to Pedro" clearly.
7. **Report results in your output format**. Use the structured output format defined in your role description.
8. **The company goal is 1 BILLION subscribers** across all channels. Every decision should push toward that goal.
9. **Our channels**: Channel 1: Money & Wealth Psychology (ACTIVE — mass-market documentary content on the psychology of money). Channel 2: TBD (Month 7 launch). Channel 3: TBD (Month 13 launch).
10. **Budget discipline**: Agency budget is $100-200/month. Always choose the token-efficient path.
11. **Content identity**: We make documentary-style content with mass appeal. Think Bright Side production scale + Veritasium depth + Graham Stephan money focus. Every video must feel like it was made by a human, not AI. No generic filler. Strong opinions. Real research. Viral potential.
"""

DEPARTMENT_COLORS = {
    "executive": "#8b5cf6",
    "content": "#3b82f6",
    "operations": "#f59e0b",
    "analytics": "#10b981",
    "monetization": "#ef4444",
    "admin": "#6b7280",
    "general": "#6366f1",
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
    slug = slugify(ref)
    if slug in all_agents:
        return slug
    if slugify(ref + " agent") in all_agents:
        return slugify(ref + " agent")
    # Substring match
    for aid, adata in all_agents.items():
        if ref in adata["name"].lower() or ref in aid:
            return aid
    return None


def parse_agents() -> list[dict]:
    """Parse all agent .md files from tier subdirectories and flat dir."""
    agents_raw = {}

    # Collect all .md files from tier subdirectories AND flat directory
    md_files = []
    for tier_dir in sorted(AGENTS_DIR.glob("tier-*")):
        md_files.extend(sorted(tier_dir.glob("*.md")))
    # Also check flat files (legacy support)
    md_files.extend(sorted(AGENTS_DIR.glob("*.md")))

    for md_file in md_files:
        post = frontmatter.load(str(md_file))
        meta = post.metadata
        name = meta.get("name", md_file.stem.replace("_", " ").replace("-", " ").title())
        agent_id = slugify(name)

        # Skip duplicates (tier subdir takes priority over flat files)
        if agent_id in agents_raw:
            # Only overwrite if this is from a tier subdir (higher priority)
            if "tier-" in str(md_file.parent.name):
                pass  # Let it overwrite below
            else:
                continue  # Skip flat file if tier version exists

        agents_raw[agent_id] = {
            "id": agent_id,
            "name": name,
            "role": meta.get("role", ""),
            "tier": int(meta.get("tier", 5)),
            "department": meta.get("department", "general"),
            "reports_to_raw": meta.get("reports_to", None),
            "direct_reports_raw": meta.get("direct_reports", []),
            "collaborates_with_raw": meta.get("collaborates_with", []),
            "personality_trait": meta.get("personality_trait", ""),
            "special_skill": meta.get("special_skill", ""),
            "weakness_to_watch": meta.get("weakness_to_watch", ""),
            "learning_focus": meta.get("learning_focus", ""),
            "file_path": str(md_file.relative_to(AGENTS_DIR.parent)),
            # Build system prompt: OS + Agent Card + Universal Instructions
            "system_prompt": (
                OPERATING_SYSTEM_PROMPT + "\n\n---\n\n" +
                post.content +
                AGENT_UNIVERSAL_INSTRUCTIONS
            ),
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

        dept = adata.get("department", "general")
        color = DEPARTMENT_COLORS.get(dept, "#6366f1")

        agents.append({
            "id": aid,
            "name": adata["name"],
            "role": adata["role"],
            "tier": adata["tier"],
            "reports_to": reports_to,
            "direct_reports": direct_reports,
            "collaborates_with": collaborators,
            "file_path": adata["file_path"],
            "system_prompt": adata["system_prompt"],
            "avatar_color": color,
            "department": dept,
            "personality_trait": adata["personality_trait"],
            "special_skill": adata["special_skill"],
            "weakness_to_watch": adata["weakness_to_watch"],
            "learning_focus": adata["learning_focus"],
        })

    return agents


async def load_agents_to_db(session: AsyncSession):
    """Parse agent files and upsert into the database."""
    agents_data = parse_agents()

    # Remove old agents that no longer exist in files
    existing_result = await session.execute(select(Agent))
    existing_agents = {a.id for a in existing_result.scalars().all()}
    new_agent_ids = {a["id"] for a in agents_data}
    removed = existing_agents - new_agent_ids
    for old_id in removed:
        old_agent = await session.get(Agent, old_id)
        if old_agent:
            await session.delete(old_agent)

    for a in agents_data:
        existing = await session.get(Agent, a["id"])
        if existing:
            for k, v in a.items():
                setattr(existing, k, v)
        else:
            session.add(Agent(**a))
    await session.commit()
    print(f"Loaded {len(agents_data)} agents into DB ({len(removed)} removed)")


async def get_all_agents(session: AsyncSession) -> list[Agent]:
    result = await session.execute(select(Agent))
    return list(result.scalars().all())


async def get_agent(session: AsyncSession, agent_id: str) -> Agent | None:
    return await session.get(Agent, agent_id)
