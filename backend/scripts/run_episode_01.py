"""
Run V-Real AI Episode 01 "Wake Up" through the full pipeline.

This feeds the script through every agent in order:
  1. Hook Specialist → refine the cold open
  2. Scriptwriter → add visual cues, pattern interrupts, open loops
  3. SEO Specialist → title, description, tags, chapters
  4. Thumbnail Designer → 3 thumbnail concepts
  5. Shorts & Clips → extract 3 shorts
  6. Social Media Manager → cross-platform posts
  7. Newsletter Strategist → email draft
  8. QA Lead → score and review (must hit 8/10)
  9. Reflection Council → final sanity check
  10. Video generation → voiceover + stock footage
  11. YouTube upload → PRIVATE
  12. Notification → Discord/Telegram with full review package

Usage:
  cd backend
  source .venv/bin/activate
  python -m scripts.run_episode_01

Or via API once deployed:
  POST /api/webhooks/trigger
  {
    "action": "run_pipeline",
    "topic": "V-Real AI Episode 01: Wake Up — Channel launch video about AI replacing jobs and why now is the time to act"
  }
"""

import asyncio
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db, async_session
from app.services.agent_loader import load_agents_to_db
from app.models.thread import Thread, Message
from app.models.agent import Agent
from app.routers.webhooks import _run_pipeline_sequential, CONTENT_PIPELINE_AGENTS
from app.routers.pipeline import _run_quality_gate, _send_review_notification

# The Wake Up script
EPISODE_01_SCRIPT = Path(__file__).resolve().parent.parent.parent / "content" / "scripts" / "vreal-ai" / "episode-01-wake-up.md"


async def main():
    print("=" * 60)
    print("V-REAL AI — EPISODE 01: WAKE UP")
    print("Running through the full pipeline")
    print("=" * 60)

    # Init
    await init_db()
    async with async_session() as session:
        await load_agents_to_db(session)
    print("✓ Database initialized, 30 agents loaded\n")

    # Read the script
    script_text = EPISODE_01_SCRIPT.read_text()
    print(f"✓ Script loaded ({len(script_text)} chars)\n")

    # Create the pipeline thread
    async with async_session() as db:
        thread = Thread(
            id=str(uuid.uuid4()),
            subject="V-Real AI Episode 01: Wake Up",
            participants=CONTENT_PIPELINE_AGENTS,
            status="running",
        )
        db.add(thread)

        # The initial prompt includes the full script + instructions
        prompt = f"""V-Real AI Episode 01: "Wake Up" — Channel Launch Video

FORMAT: Documentary style — stock footage + AI voiceover + captions + text overlays
TONE: Real, direct, emotional, no fluff
RUNTIME TARGET: 6-8 minutes
AUDIENCE: People who feel the AI shift and want to act — not developers, regular people ready to learn

EXISTING SCRIPT (draft — needs refinement through the pipeline):

{script_text}

INSTRUCTIONS FOR EACH AGENT:
- This is the channel launch video. It sets the tone for everything.
- The script above is the emotional foundation. Refine it, don't replace it.
- Hook Specialist: Evaluate the cold open. Score it. Suggest improvements if needed.
- Scriptwriter: Add [B-ROLL:], [GRAPHIC:], [SFX:], [MUSIC:] cues throughout.
  Add pattern interrupts every 60-90 seconds. Add open loops between acts.
  Add a credibility beat in the first 30 seconds. Keep the emotional core.
- SEO Specialist: Full package — this needs to rank for "AI automation", "AI replacing jobs", "make money with AI"
- Thumbnail Designer: 3 concepts matching the documentary/dark brand aesthetic
- Shorts & Clips: Extract 3 viral moments for YouTube Shorts/TikTok/Reels
- Social Media Manager: Launch week social campaign across all platforms
- Newsletter Strategist: "Welcome to V-Real AI" launch email
- QA Lead: This must be 10/10. MrBeast quality bar. No compromises.

Build on each other's work. Every agent reads what came before."""

        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            sender_type="user",
            sender_agent_id=None,
            content=prompt,
        )
        db.add(msg)
        await db.commit()

        thread_id = thread.id

    print(f"✓ Pipeline thread created: {thread_id}\n")
    print("Running agents through the pipeline...\n")

    # Skip trend researcher and senior researcher — we already have the script
    pipeline_agents = [
        "hook-specialist-agent",
        "scriptwriter-agent",
        "seo-specialist-agent",
        "thumbnail-designer-agent",
        "shorts-clips-agent",
        "social-media-manager-agent",
        "newsletter-strategist-agent",
    ]

    await _run_pipeline_sequential(thread_id, pipeline_agents, None)
    print("✓ All content agents complete\n")

    # Quality gate
    print("Running quality gate (QA Lead + Reflection Council)...\n")
    passed = await _run_quality_gate(thread_id, threshold=8, max_retries=2)

    if passed:
        print("✓ QUALITY GATE PASSED\n")
    else:
        print("⚠ Quality gate did not pass after retries — sending for manual review\n")

    # Send notification
    print("Sending review notification...\n")
    await _send_review_notification(thread_id)

    # Mark complete
    async with async_session() as db:
        thread = await db.get(Thread, thread_id)
        if thread:
            thread.status = "complete"
            thread.updated_at = datetime.now(timezone.utc)
            await db.commit()

    print("=" * 60)
    print("PIPELINE COMPLETE")
    print(f"Thread ID: {thread_id}")
    print("Check Discord/Telegram for the review package.")
    print("Check the dashboard at your deployed URL to see all agent responses.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
