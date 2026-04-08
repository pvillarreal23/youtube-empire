from __future__ import annotations

import uuid
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db, async_session
from app.models.thread import Thread, Message
from app.models.agent import Agent
from app.services.claude_service import generate_agent_response
from app.routers.webhooks import _run_pipeline_sequential, CONTENT_PIPELINE_AGENTS

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


class AutopilotConfig(BaseModel):
    channel: str = "V-Real AI"
    niche: str = "AI agents, automation, and building income with AI"
    num_ideas: int = 3
    quality_threshold: int = 8  # Minimum score (out of 10) to pass QA
    max_retries: int = 2  # Max times to revise before sending to you anyway


# Quality gate agents — run after the content pipeline
QUALITY_GATE_AGENTS = [
    "qa-lead-agent",
    "reflection-council-agent",
    "content-vp-agent",
]


# --- Autopilot: Trend Research -> Pick Best -> Run Full Pipeline ---

async def _run_autopilot(config: AutopilotConfig, callback_url: str | None = None):
    """
    Full autopilot pipeline:
    1. Trend Researcher finds top ideas
    2. Content VP picks the best one
    3. Full content pipeline runs on the winning topic
    """
    async with async_session() as db:
        # Step 1: Trend Researcher finds ideas
        thread = Thread(
            id=str(uuid.uuid4()),
            subject=f"Autopilot: {config.channel} — {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
            participants=["trend-researcher-agent", "content-vp-agent"] + CONTENT_PIPELINE_AGENTS,
            status="running",
        )
        db.add(thread)

        discovery_prompt = (
            f"You are scanning for the next video topic for {config.channel}.\n\n"
            f"Channel niche: {config.niche}\n\n"
            f"Find the top {config.num_ideas} video opportunities right now. For each:\n"
            f"1. Topic/title idea\n"
            f"2. Why NOW (what's trending, what just happened, what's about to change)\n"
            f"3. Target keyword and estimated search demand\n"
            f"4. Urgency score (1-10)\n"
            f"5. Unique angle competitors haven't covered\n\n"
            f"Focus on topics that are timely, searchable, and would resonate with people "
            f"who want to use AI to build income and escape the 9-to-5."
        )

        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            sender_type="user",
            sender_agent_id=None,
            content=discovery_prompt,
        )
        db.add(msg)
        await db.commit()

        # Run Trend Researcher
        trend_agent = await db.get(Agent, "trend-researcher-agent")
        if not trend_agent:
            return

        try:
            trend_response = generate_agent_response(
                system_prompt=trend_agent.system_prompt,
                thread_messages=[{
                    "id": msg.id, "thread_id": thread.id, "sender_type": "user",
                    "sender_agent_id": None, "sender_name": None,
                    "content": discovery_prompt, "created_at": msg.created_at.isoformat(),
                    "status": "sent",
                }],
                agent_id="trend-researcher-agent",
            )
        except Exception as e:
            error = Message(
                id=str(uuid.uuid4()), thread_id=thread.id, sender_type="agent",
                sender_agent_id="trend-researcher-agent",
                content=f"[Error: {str(e)[:200]}]", status="failed",
            )
            db.add(error)
            thread.status = "failed"
            await db.commit()
            return

        trend_msg = Message(
            id=str(uuid.uuid4()), thread_id=thread.id, sender_type="agent",
            sender_agent_id="trend-researcher-agent",
            content=trend_response, status="complete",
        )
        db.add(trend_msg)
        thread.updated_at = datetime.now(timezone.utc)
        await db.commit()

        # Step 2: Content VP picks the best topic
        content_vp = await db.get(Agent, "content-vp-agent")
        if not content_vp:
            return

        pick_prompt = (
            f"The Trend Researcher found these opportunities:\n\n{trend_response}\n\n"
            f"Pick the BEST one for this week's video. Consider:\n"
            f"- Urgency (will this still be relevant next week?)\n"
            f"- Search demand\n"
            f"- Fit for {config.channel}\n"
            f"- Unique angle potential\n\n"
            f"Respond with ONLY:\n"
            f"SELECTED TOPIC: [the exact topic]\n"
            f"REASON: [one sentence why]\n"
            f"ANGLE: [the specific angle to take]"
        )

        thread_msgs = [
            {
                "id": msg.id, "thread_id": thread.id, "sender_type": "user",
                "sender_agent_id": None, "sender_name": None,
                "content": discovery_prompt, "created_at": msg.created_at.isoformat(),
                "status": "sent",
            },
            {
                "id": trend_msg.id, "thread_id": thread.id, "sender_type": "agent",
                "sender_agent_id": "trend-researcher-agent", "sender_name": "Trend Researcher Agent",
                "content": trend_response, "created_at": trend_msg.created_at.isoformat(),
                "status": "complete",
            },
            {
                "id": str(uuid.uuid4()), "thread_id": thread.id, "sender_type": "user",
                "sender_agent_id": None, "sender_name": None,
                "content": pick_prompt, "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "sent",
            },
        ]

        # Save the pick prompt as a message
        pick_msg = Message(
            id=str(uuid.uuid4()), thread_id=thread.id, sender_type="user",
            sender_agent_id=None, content=pick_prompt,
        )
        db.add(pick_msg)
        await db.commit()

        try:
            vp_response = generate_agent_response(
                system_prompt=content_vp.system_prompt,
                thread_messages=thread_msgs,
                agent_id="content-vp-agent",
            )
        except Exception as e:
            error = Message(
                id=str(uuid.uuid4()), thread_id=thread.id, sender_type="agent",
                sender_agent_id="content-vp-agent",
                content=f"[Error: {str(e)[:200]}]", status="failed",
            )
            db.add(error)
            thread.status = "failed"
            await db.commit()
            return

        vp_msg = Message(
            id=str(uuid.uuid4()), thread_id=thread.id, sender_type="agent",
            sender_agent_id="content-vp-agent",
            content=vp_response, status="complete",
        )
        db.add(vp_msg)
        await db.commit()

        # Step 3: Run the full content pipeline with the selected topic
        pipeline_prompt = (
            f"Content VP has selected this topic for V-Real AI:\n\n{vp_response}\n\n"
            f"Trend Researcher's full research:\n{trend_response}\n\n"
            f"Each agent should now do their part to create a complete video package. "
            f"Build on each other's work."
        )

        pipeline_msg = Message(
            id=str(uuid.uuid4()), thread_id=thread.id, sender_type="user",
            sender_agent_id=None, content=pipeline_prompt,
        )
        db.add(pipeline_msg)
        await db.commit()

    # Run remaining pipeline agents (skip trend researcher, already done)
    remaining_agents = [a for a in CONTENT_PIPELINE_AGENTS if a not in ("trend-researcher-agent",)]
    await _run_pipeline_sequential(thread.id, remaining_agents, callback_url)

    # Step 4: Quality gate — QA Lead + Reflection Council pressure test
    passed = await _run_quality_gate(thread.id, config.quality_threshold, config.max_retries)

    if not passed:
        async with async_session() as db:
            note = Message(
                id=str(uuid.uuid4()), thread_id=thread.id, sender_type="user",
                sender_agent_id=None,
                content=(
                    "QUALITY GATE: Content did not reach the quality threshold after retries. "
                    "Sending to you for manual review. Check the QA notes above."
                ),
            )
            db.add(note)
            await db.commit()

    # Step 5: Video generation + YouTube upload (if API keys are configured)
    from app.config import ELEVENLABS_API_KEY, CREATOMATE_API_KEY
    if ELEVENLABS_API_KEY and CREATOMATE_API_KEY:
        try:
            await _generate_and_upload_video(thread.id)
        except Exception as e:
            async with async_session() as db:
                note = Message(
                    id=str(uuid.uuid4()), thread_id=thread.id, sender_type="user",
                    sender_agent_id=None,
                    content=f"[Video generation skipped: {str(e)[:200]}]",
                )
                db.add(note)
                await db.commit()

    # Step 6: Send review notification regardless
    await _send_review_notification(thread.id)


async def _run_quality_gate(thread_id: str, threshold: int, max_retries: int) -> bool:
    """
    Run QA Lead + Reflection Council on the content.
    If score < threshold, send feedback to Scriptwriter for revision.
    Retry up to max_retries times.
    Returns True if quality passed, False if it didn't after all retries.
    """
    import re

    for attempt in range(max_retries + 1):
        async with async_session() as db:
            # Run QA Lead
            qa_agent = await db.get(Agent, "qa-lead-agent")
            if not qa_agent:
                return True  # Skip if agent doesn't exist

            # Get all messages
            result = await db.execute(
                select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
            )
            messages = list(result.scalars().all())
            thread_msgs = []
            for m in messages:
                sender = await db.get(Agent, m.sender_agent_id) if m.sender_agent_id else None
                thread_msgs.append({
                    "id": m.id, "thread_id": m.thread_id,
                    "sender_type": m.sender_type, "sender_agent_id": m.sender_agent_id,
                    "sender_name": sender.name if sender else None,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "status": m.status,
                })

            qa_prompt = (
                "Review ALL the content produced in this thread. Score it 1-10 on overall quality. "
                "Use your full QA checklist. Be brutally honest — this is MrBeast-level quality bar. "
                "If the score is below 8, list SPECIFIC issues that must be fixed. "
                "End your review with exactly this format on its own line: SCORE: X/10"
            )

            thread_msgs.append({
                "id": str(uuid.uuid4()), "thread_id": thread_id,
                "sender_type": "user", "sender_agent_id": None, "sender_name": None,
                "content": qa_prompt,
                "created_at": datetime.now(timezone.utc).isoformat(), "status": "sent",
            })

            try:
                qa_response = generate_agent_response(
                    system_prompt=qa_agent.system_prompt,
                    thread_messages=thread_msgs,
                    agent_id="qa-lead-agent",
                )
            except Exception:
                return True  # Don't block pipeline on QA error

            qa_msg = Message(
                id=str(uuid.uuid4()), thread_id=thread_id, sender_type="agent",
                sender_agent_id="qa-lead-agent", content=qa_response, status="complete",
            )
            db.add(qa_msg)
            await db.commit()

            # Parse the score
            score_match = re.search(r'SCORE:\s*(\d+)/10', qa_response)
            score = int(score_match.group(1)) if score_match else 0

            if score >= threshold:
                # Passed! Run Reflection Council for a final sanity check
                reflection = await db.get(Agent, "reflection-council-agent")
                if reflection:
                    reflection_msgs = thread_msgs + [{
                        "id": qa_msg.id, "thread_id": thread_id,
                        "sender_type": "agent", "sender_agent_id": "qa-lead-agent",
                        "sender_name": "QA Lead Agent", "content": qa_response,
                        "created_at": qa_msg.created_at.isoformat(), "status": "complete",
                    }]
                    try:
                        reflection_response = generate_agent_response(
                            system_prompt=reflection.system_prompt,
                            thread_messages=reflection_msgs,
                            agent_id="reflection-council-agent",
                        )
                        ref_msg = Message(
                            id=str(uuid.uuid4()), thread_id=thread_id, sender_type="agent",
                            sender_agent_id="reflection-council-agent",
                            content=reflection_response, status="complete",
                        )
                        db.add(ref_msg)
                        await db.commit()
                    except Exception:
                        pass
                return True

            # Score below threshold — send feedback to Scriptwriter for revision
            if attempt < max_retries:
                revision_prompt = (
                    f"QA REVISION REQUIRED (Attempt {attempt + 1}/{max_retries})\n\n"
                    f"QA Score: {score}/10 (need {threshold}/10 minimum)\n\n"
                    f"QA Feedback:\n{qa_response}\n\n"
                    f"Revise the script addressing ALL issues listed above. "
                    f"This needs to be 10/10 quality. No shortcuts."
                )

                revision_msg = Message(
                    id=str(uuid.uuid4()), thread_id=thread_id, sender_type="user",
                    sender_agent_id=None, content=revision_prompt,
                )
                db.add(revision_msg)
                await db.commit()

                # Re-run scriptwriter, then SEO, then QA again
                await _run_pipeline_sequential(
                    thread_id,
                    ["scriptwriter-agent", "seo-specialist-agent", "hook-specialist-agent"],
                    None,
                )

    return False


async def _generate_and_upload_video(thread_id: str):
    """After agents finish, generate video and upload to YouTube as private."""
    from app.services.video_service import generate_video_from_script
    from app.services.youtube_service import upload_video

    async with async_session() as db:
        result = await db.execute(
            select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
        )
        messages = list(result.scalars().all())

        # Find the scriptwriter output
        script_text = None
        seo_text = None
        for m in messages:
            if m.sender_agent_id == "scriptwriter-agent" and m.status == "complete":
                script_text = m.content
            if m.sender_agent_id == "seo-specialist-agent" and m.status == "complete":
                seo_text = m.content

        if not script_text:
            return

        thread = await db.get(Thread, thread_id)
        title = thread.subject.replace("Autopilot: ", "").replace("Pipeline: ", "") if thread else "V-Real AI"

        # Parse SEO output for title/description/tags
        video_title = title
        video_description = ""
        video_tags = ["V-Real AI", "AI agents", "automation"]

        if seo_text:
            # Try to extract optimized title from SEO output
            import re
            title_match = re.search(r'(?:TITLE|Title)[^:]*:\s*(.+)', seo_text)
            if title_match:
                video_title = title_match.group(1).strip().strip('"').strip("'")[:100]

            desc_match = re.search(r'DESCRIPTION:\s*\n([\s\S]+?)(?=\nTAGS:|\nHASHTAGS:|\nCHAPTERS:|\Z)', seo_text)
            if desc_match:
                video_description = desc_match.group(1).strip()

            tags_match = re.search(r'TAGS:\s*\n(.+)', seo_text)
            if tags_match:
                video_tags = [t.strip() for t in tags_match.group(1).split(",")][:15]

        # Generate video
        video_result = await generate_video_from_script(script_text, video_title)

        # Upload to YouTube as PRIVATE
        try:
            yt_result = await upload_video(
                video_url=video_result["video_url"],
                title=video_title,
                description=video_description or f"V-Real AI\n\n{script_text[:500]}",
                tags=video_tags,
                privacy="private",
            )

            # Save YouTube link in thread
            yt_msg = Message(
                id=str(uuid.uuid4()), thread_id=thread_id, sender_type="user",
                sender_agent_id=None,
                content=(
                    f"VIDEO UPLOADED (PRIVATE)\n"
                    f"YouTube: {yt_result['url']}\n"
                    f"Status: Private — review in YouTube Studio and set to public when ready."
                ),
            )
            db.add(yt_msg)
            await db.commit()

            # Send review package notification
            await _send_review_notification(thread_id, yt_result.get("url"))

        except Exception as e:
            # YouTube upload failed — save video URL anyway
            note = Message(
                id=str(uuid.uuid4()), thread_id=thread_id, sender_type="user",
                sender_agent_id=None,
                content=(
                    f"VIDEO GENERATED — YouTube upload failed: {str(e)[:200]}\n"
                    f"Video URL: {video_result.get('video_url', 'N/A')}\n"
                    f"Upload manually to YouTube as private."
                ),
            )
            db.add(note)
            await db.commit()


async def _send_review_notification(thread_id: str, youtube_url: str | None = None):
    """Send the review package (script, thumbnail, SEO, etc.) to all notification channels."""
    from app.services.notification_service import send_review_package

    async with async_session() as db:
        result = await db.execute(
            select(Message).where(Message.thread_id == thread_id).order_by(Message.created_at)
        )
        messages = list(result.scalars().all())

        agent_outputs = {}
        for m in messages:
            if m.sender_type == "agent" and m.status == "complete" and m.sender_agent_id:
                agent_outputs[m.sender_agent_id] = m.content

        thread = await db.get(Thread, thread_id)
        title = thread.subject if thread else "V-Real AI Video"

        await send_review_package(
            title=title,
            script=agent_outputs.get("scriptwriter-agent", "No script generated"),
            seo_package=agent_outputs.get("seo-specialist-agent"),
            thumbnail_brief=agent_outputs.get("thumbnail-designer-agent"),
            shorts_scripts=agent_outputs.get("shorts-clips-agent"),
            youtube_url=youtube_url,
            social_posts=agent_outputs.get("social-media-manager-agent"),
            newsletter_draft=agent_outputs.get("newsletter-strategist-agent"),
        )


@router.post("/autopilot")
async def start_autopilot(
    config: AutopilotConfig,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Start the full autopilot pipeline.
    Trend Researcher finds topics -> Content VP picks best -> Full pipeline runs.

    Call this from Make.com on a daily schedule, or manually from the dashboard.
    """
    background_tasks.add_task(_run_autopilot, config)
    return {
        "status": "started",
        "message": f"Autopilot pipeline started for {config.channel}",
    }


@router.get("/history")
async def pipeline_history(db: AsyncSession = Depends(get_db)):
    """List all pipeline runs."""
    result = await db.execute(
        select(Thread)
        .where(Thread.subject.like("Pipeline:%") | Thread.subject.like("Autopilot:%"))
        .order_by(Thread.created_at.desc())
    )
    threads = list(result.scalars().all())
    return [
        {
            "id": t.id,
            "subject": t.subject,
            "status": t.status,
            "created_at": t.created_at,
            "updated_at": t.updated_at,
            "agents_involved": t.participants or [],
        }
        for t in threads
    ]
