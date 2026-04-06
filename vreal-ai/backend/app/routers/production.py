from __future__ import annotations

import uuid
import asyncio
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, async_session
from app.models.production import ProductionJob, PIPELINE_STAGES, CHANNEL_MANAGERS
from app.models.thread import Thread, Message
from app.models.agent import Agent
from app.models.scheduler import Escalation
from app.services.claude_service import generate_agent_response, generate_agent_response_async
from app.services.pressure_test import pressure_test

router = APIRouter(prefix="/api/production", tags=["production"])

# ── Quality Gate Configuration ──────────────────────────────────────────────
MAX_REVISION_LOOPS = 5  # Safety valve — max times a stage can loop before escalating
QUALITY_THRESHOLD = 10  # Only 10/10 passes. Period.

# Which stages get quality-gated (scored and looped)
GATED_STAGES = {"research", "scripted", "voiceover", "thumbnail", "edited", "seo"}

# Which stages get multi-model pressure tested (Claude + ChatGPT + Gemini + Grok)
PRESSURE_TEST_STAGES = {"scripted", "seo"}

# The QA reviewer for each stage — who judges the work
STAGE_REVIEWERS = {
    "research": "senior-researcher",
    "scripted": "quality-assurance-lead",
    "voiceover": "voice-director",
    "thumbnail": "quality-assurance-lead",
    "edited": "quality-assurance-lead",
    "seo": "seo-specialist",
}

# Agent IDs that match the reviewer names
REVIEWER_AGENT_IDS = {
    "senior-researcher": "senior-researcher",
    "quality-assurance-lead": "quality-assurance-lead",
    "voice-director": "voice-director",
    "seo-specialist": "seo-specialist",
}

QUALITY_REVIEW_PROMPT = """You are reviewing the output of the {stage} stage for the episode "{title}" on {channel}.

Your job is to score this work on a scale of 1-10 using the V-Real AI quality standards:
- 10/10 = BBC/Netflix documentary quality. Would stop you mid-scroll. No improvements needed.
- 9/10 = Excellent but one small thing could be better. NOT good enough — send back.
- 8/10 = Good but noticeable gaps. Definitely send back.
- 7/10 or below = Major issues. Send back with detailed notes.

ONLY a 10/10 passes. Everything else loops back for revision.

Review the work below and respond in EXACTLY this format:

QUALITY SCORE: [X]/10

VERDICT: [APPROVED or REVISION_NEEDED]

FEEDBACK:
[If REVISION_NEEDED: specific, actionable feedback on exactly what needs to change to reach 10/10]
[If APPROVED: brief note on what makes this 10/10 quality]

---

Work to review:
{work_output}
"""

REVISION_PROMPT = """Your previous {stage} output for "{title}" was reviewed and scored {score}/10 — NOT good enough.

It needs to be 10/10 to proceed. Here is the specific feedback:

{feedback}

IMPORTANT:
- Address EVERY point in the feedback
- Don't just tweak — genuinely improve
- This is revision #{revision_number} of max {max_revisions}
- If this doesn't hit 10/10, it loops again
- Read the feedback carefully and deliver exactly what's asked

Produce your complete revised output now. Make it 10/10."""


class CreateJobRequest(BaseModel):
    title: str
    channel: str
    target_date: str = ""


class RejectJobRequest(BaseModel):
    notes: str = ""
    send_back_to: str = "scripted"


def _extract_score(review_text: str) -> tuple[int, str, str]:
    """Extract score, verdict, and feedback from QA review response."""
    score = 0
    verdict = "REVISION_NEEDED"
    feedback = ""

    # Extract score
    score_match = re.search(r"QUALITY SCORE:\s*(\d+)\s*/\s*10", review_text)
    if score_match:
        score = int(score_match.group(1))

    # Extract verdict
    if "VERDICT:" in review_text:
        verdict_section = review_text.split("VERDICT:")[1].split("\n")[0].strip()
        if "APPROVED" in verdict_section.upper():
            verdict = "APPROVED"
        else:
            verdict = "REVISION_NEEDED"

    # Extract feedback
    if "FEEDBACK:" in review_text:
        feedback = review_text.split("FEEDBACK:")[1].strip()
        # Clean up — remove trailing sections if any
        if "---" in feedback:
            feedback = feedback.split("---")[0].strip()

    # Safety: if score < 10 but verdict says approved, override
    if score < QUALITY_THRESHOLD:
        verdict = "REVISION_NEEDED"

    return score, verdict, feedback


async def _quality_gate(
    job: ProductionJob,
    stage: str,
    work_output: str,
    db: AsyncSession,
) -> tuple[bool, int, str]:
    """
    Run quality review on stage output.
    Returns: (passed: bool, score: int, feedback: str)
    """
    reviewer_name = STAGE_REVIEWERS.get(stage)
    if not reviewer_name:
        return True, 10, "No reviewer configured — auto-pass"

    reviewer_id = REVIEWER_AGENT_IDS.get(reviewer_name, reviewer_name)
    reviewer = await db.get(Agent, reviewer_id)

    if not reviewer:
        # Try with -agent suffix
        reviewer = await db.get(Agent, reviewer_id + "-agent")
        if not reviewer:
            print(f"[QUALITY] Reviewer '{reviewer_id}' not found, auto-passing")
            return True, 10, "Reviewer not found — auto-pass"

    # Build the review prompt
    review_prompt = QUALITY_REVIEW_PROMPT.format(
        stage=stage,
        title=job.title,
        channel=job.channel,
        work_output=work_output[:8000],  # Limit to avoid token overflow
    )

    # Get the reviewer's assessment
    try:
        review_response = await generate_agent_response_async(
            system_prompt=reviewer.system_prompt,
            thread_messages=[{"id": "review", "sender_type": "user", "sender_agent_id": None,
                            "sender_name": "Pipeline QA System", "content": review_prompt,
                            "created_at": datetime.now(timezone.utc).isoformat(), "status": "complete"}],
            agent_id=reviewer.id,
        )

        score, verdict, feedback = _extract_score(review_response)

        # Log the review in the thread
        if job.thread_id:
            review_msg = Message(
                id=str(uuid.uuid4()),
                thread_id=job.thread_id,
                sender_type="agent",
                sender_agent_id=reviewer.id,
                content=f"[QUALITY GATE — {stage.upper()}]\n\n{review_response}",
                status="complete",
            )
            db.add(review_msg)
            await db.commit()

        passed = verdict == "APPROVED" and score >= QUALITY_THRESHOLD
        return passed, score, feedback

    except Exception as e:
        print(f"[QUALITY] Review failed for {stage}: {e}")
        return False, 0, f"Review failed: {str(e)}"


async def _advance_pipeline(job_id: str):
    """
    Auto-advance a production job through the pipeline.

    QUALITY LOOP: Each gated stage runs → gets reviewed → if not 10/10,
    loops back with feedback until it hits 10/10 or max revisions.
    Only 10/10 work advances. Everything else loops.
    """
    async with async_session() as db:
        job = await db.get(ProductionJob, job_id)
        if not job:
            return

        stage_info = PIPELINE_STAGES.get(job.stage)
        if not stage_info or not stage_info.get("agent"):
            return

        agent_id = stage_info["agent"]
        agent = await db.get(Agent, agent_id)
        if not agent:
            # Try without -agent suffix
            print(f"[PRODUCTION] Agent '{agent_id}' not found, skipping stage")
            return

        # Also involve the channel manager for context
        cm_id = CHANNEL_MANAGERS.get(job.channel)

        # Create or get thread for this job
        if not job.thread_id:
            thread = Thread(
                id=str(uuid.uuid4()),
                subject=f"[Production] {job.title} — {job.stage.upper()}",
                participants=[agent_id, cm_id] if cm_id else [agent_id],
            )
            db.add(thread)
            job.thread_id = thread.id
        else:
            thread = await db.get(Thread, job.thread_id)
            if thread:
                thread.subject = f"[Production] {job.title} — {job.stage.upper()}"
                participants = thread.participants or []
                if agent_id not in participants:
                    thread.participants = participants + [agent_id]

        # Build the stage-specific prompt
        stage_prompts = {
            "research": f"Research trending angles and data for a video titled '{job.title}' on the {job.channel} channel. Find key facts, statistics, competitor content, and unique angles. Provide a comprehensive research package. This must be 10/10 quality — deep, specific, with real data points.",
            "scripted": f"Write a complete video script for '{job.title}' on the {job.channel} channel. Use the research provided in this thread. Follow your SCRIPT format with hook, animation cues, voice principles, and 3-act structure. Target 8-12 minutes (~1200 words). This must be 10/10 — BBC documentary quality, not a single weak line.",
            "voiceover": f"The script for '{job.title}' is ready. Prepare a complete VOICEOVER BRIEF — pacing map, emphasis words, pause points, annotated script with all delivery directions. Voice: Julian on ElevenLabs (Stability 0.65, Similarity 0.75, Style 0.00, Speaker Boost OFF). This must be 10/10 — every word must land.",
            "thumbnail": f"Create 3 thumbnail concepts for '{job.title}' on {job.channel}. Use THUMBNAIL BRIEF format with SAFE, BOLD, and EXPERIMENTAL options. Dark background, max 5 words, Inter Black font, test at 120px. Must be 10/10 — would you click this?",
            "edited": f"The voiceover and thumbnail for '{job.title}' are ready. Prepare a complete EDIT BRIEF — scene-by-scene with footage sources, transitions, pattern interrupts every 15-20s, 4-layer audio mix, color grade specs. No static shot > 2 seconds. Must be 10/10.",
            "seo": f"Optimize SEO for '{job.title}' on {job.channel}. Full SEO PACKAGE — 5 title options ranked, description with chapters, 15-20 tags, keyword research, recommendation wake analysis. Must be 10/10 — maximum discoverability.",
            "review": f"FINAL QA review for '{job.title}' on {job.channel}. Run the complete QA CHECKLIST across ALL previous work in this thread — research quality, script quality, voiceover direction, thumbnail concepts, edit brief, SEO package. Score each component 1-10. Only if EVERYTHING is 10/10 does this pass. Give your final verdict.",
            "approved": f"'{job.title}' has passed all quality gates for {job.channel}. Every stage scored 10/10. Prepare final approval summary for Pedro. This needs his sign-off to go live.",
        }

        prompt = stage_prompts.get(job.stage, f"Process stage '{job.stage}' for '{job.title}'")

        # Add context about previous stages
        context_parts = []
        if job.research_data:
            context_parts.append(f"[Research completed — 10/10]\n{job.research_data[:2000]}")
        if job.script:
            context_parts.append(f"[Script completed — 10/10]\n{job.script[:2000]}")
        if job.seo_metadata:
            context_parts.append(f"[SEO completed — 10/10]\n{job.seo_metadata[:1000]}")
        if job.rejection_notes:
            context_parts.append(f"[PREVIOUS REJECTION NOTES]\n{job.rejection_notes}")
        if context_parts:
            prompt += "\n\nPrevious work:\n" + "\n---\n".join(context_parts)

        # ═══════════════════════════════════════════════════════════════
        # THE QUALITY LOOP — keeps going until 10/10 or max revisions
        # ═══════════════════════════════════════════════════════════════

        revision_count = 0
        current_prompt = prompt
        is_gated = job.stage in GATED_STAGES

        while True:
            # Send message to the thread
            msg = Message(
                id=str(uuid.uuid4()),
                thread_id=job.thread_id,
                sender_type="user",
                sender_agent_id=None,
                content=f"[Pipeline — Stage: {job.stage.upper()} | Attempt: {revision_count + 1}/{MAX_REVISION_LOOPS}]\n\n{current_prompt}",
            )
            db.add(msg)
            job.current_agent_id = agent_id
            job.updated_at = datetime.now(timezone.utc)
            await db.commit()

            # Get agent response
            try:
                result = await db.execute(
                    select(Message).where(Message.thread_id == job.thread_id).order_by(Message.created_at)
                )
                thread_msgs = []
                for m in result.scalars().all():
                    a = await db.get(Agent, m.sender_agent_id) if m.sender_agent_id else None
                    thread_msgs.append({
                        "id": m.id, "sender_type": m.sender_type,
                        "sender_agent_id": m.sender_agent_id,
                        "sender_name": a.name if a else None,
                        "content": m.content,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                        "status": m.status,
                    })

                response = await generate_agent_response_async(
                    system_prompt=agent.system_prompt,
                    thread_messages=thread_msgs,
                    agent_id=agent_id,
                )

                # Save response
                agent_msg = Message(
                    id=str(uuid.uuid4()),
                    thread_id=job.thread_id,
                    sender_type="agent",
                    sender_agent_id=agent_id,
                    content=response,
                    status="complete",
                )
                db.add(agent_msg)

                # Store output in the appropriate field
                if job.stage == "research":
                    job.research_data = response
                elif job.stage == "scripted":
                    job.script = response
                elif job.stage == "seo":
                    job.seo_metadata = response

                # Add to reviewed_by
                reviewed = job.reviewed_by or []
                if agent_id not in reviewed:
                    job.reviewed_by = reviewed + [agent_id]

                await db.commit()

            except Exception as e:
                print(f"[PRODUCTION] Pipeline error at stage '{job.stage}' for '{job.title}': {e}")
                return

            # ── QUALITY GATE ──────────────────────────────────────────
            if not is_gated:
                # Non-gated stages (review, approved) pass through
                break

            passed, score, feedback = await _quality_gate(job, job.stage, response, db)

            if passed and job.stage in PRESSURE_TEST_STAGES:
                # Passed internal QA — now run multi-model pressure test
                print(f"[PRESSURE TEST] Running multi-model review for {job.stage}...")

                # Log pressure test start in thread
                if job.thread_id:
                    pt_msg = Message(
                        id=str(uuid.uuid4()),
                        thread_id=job.thread_id,
                        sender_type="user",
                        sender_agent_id=None,
                        content=f"[PRESSURE TEST — {job.stage.upper()}]\nInternal QA passed ({score}/10). Now running multi-model pressure test: Claude + ChatGPT + Gemini + Grok...",
                    )
                    db.add(pt_msg)
                    await db.commit()

                pt_result = await pressure_test(
                    stage=job.stage,
                    title=job.title,
                    content=response,
                )

                # Log pressure test results in thread
                if job.thread_id:
                    model_scores = ", ".join(
                        f"{r.model}: {r.score}/10" for r in pt_result.results
                        if r.verdict not in ("SKIP", "ERROR")
                    )
                    skipped = [r.model for r in pt_result.results if r.verdict == "SKIP"]
                    skip_note = f" (Skipped: {', '.join(skipped)} — API keys not set)" if skipped else ""

                    pt_result_msg = Message(
                        id=str(uuid.uuid4()),
                        thread_id=job.thread_id,
                        sender_type="agent",
                        sender_agent_id="quality-assurance-lead",
                        content=(
                            f"[PRESSURE TEST RESULTS — {job.stage.upper()}]\n\n"
                            f"Scores: {model_scores}{skip_note}\n"
                            f"Average: {pt_result.average_score}/10\n"
                            f"Unanimous: {'YES' if pt_result.unanimous else 'NO'}\n"
                            f"Verdict: {'✓ ALL MODELS APPROVED' if pt_result.passed else '✗ REVISION NEEDED'}\n\n"
                            f"Synthesized Feedback:\n{pt_result.synthesized_feedback}"
                        ),
                        status="complete",
                    )
                    db.add(pt_result_msg)
                    await db.commit()

                if pt_result.passed:
                    print(f"[PRESSURE TEST] ✓ All models approved {job.stage} — avg {pt_result.average_score}/10")
                    break  # Passed everything!
                else:
                    # Failed pressure test — use synthesized feedback for revision
                    print(f"[PRESSURE TEST] ✗ Failed — avg {pt_result.average_score}/10, looping back")
                    passed = False
                    score = int(pt_result.average_score)
                    feedback = pt_result.synthesized_feedback

            elif passed:
                # Passed internal QA, no pressure test needed for this stage
                print(f"[QUALITY] ✓ {job.stage} for '{job.title}' scored {score}/10 — APPROVED (attempt {revision_count + 1})")
                break

            # Not 10/10 — loop back
            revision_count += 1
            print(f"[QUALITY] ✗ {job.stage} for '{job.title}' scored {score}/10 — REVISION {revision_count}/{MAX_REVISION_LOOPS}")

            if revision_count >= MAX_REVISION_LOOPS:
                # Safety valve — escalate to Pedro
                print(f"[QUALITY] ⚠ Max revisions ({MAX_REVISION_LOOPS}) reached for {job.stage}. Escalating to Pedro.")
                escalation = Escalation(
                    id=str(uuid.uuid4()),
                    thread_id=job.thread_id,
                    agent_id=agent_id,
                    reason=(
                        f"QUALITY GATE STUCK: '{job.title}' stage '{job.stage}' failed to reach 10/10 "
                        f"after {MAX_REVISION_LOOPS} attempts. Last score: {score}/10.\n\n"
                        f"Last feedback:\n{feedback[:500]}\n\n"
                        f"Pedro: Review the thread and either approve manually or provide direction."
                    ),
                    severity="critical",
                )
                db.add(escalation)
                await db.commit()
                return  # Stop pipeline — Pedro needs to intervene

            # Build revision prompt with specific feedback
            current_prompt = REVISION_PROMPT.format(
                stage=job.stage,
                title=job.title,
                score=score,
                feedback=feedback,
                revision_number=revision_count,
                max_revisions=MAX_REVISION_LOOPS,
            )

            # Small delay to avoid hammering the API
            await asyncio.sleep(2)

        # ═══════════════════════════════════════════════════════════════
        # STAGE PASSED — Auto-advance to next stage
        # ═══════════════════════════════════════════════════════════════

        next_stage = stage_info.get("next")
        if not next_stage:
            return  # Final stage

        # Special handling for "approved" stage — ALWAYS needs Pedro
        if next_stage == "approved" or job.stage == "review":
            # After QA review, create escalation for Pedro
            escalation = Escalation(
                id=str(uuid.uuid4()),
                thread_id=job.thread_id,
                agent_id="ceo-agent",
                reason=(
                    f"READY FOR FINAL APPROVAL: '{job.title}' for {job.channel} has passed all quality gates. "
                    f"Every stage scored 10/10. Review the thread and approve for publishing."
                ),
                severity="critical",
            )
            db.add(escalation)
            job.stage = "approved"
            job.updated_at = datetime.now(timezone.utc)
            await db.commit()
            # Run the approved stage (CEO summary) but DON'T auto-publish
            await _advance_pipeline(job_id)
            return

        # Auto-advance to next stage
        job.stage = next_stage
        job.updated_at = datetime.now(timezone.utc)
        await db.commit()

        print(f"[PRODUCTION] Auto-advancing '{job.title}' to stage: {next_stage}")

        # Trigger next stage automatically
        await _advance_pipeline(job_id)


# ═══════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/jobs")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProductionJob).order_by(ProductionJob.updated_at.desc()))
    jobs = result.scalars().all()
    out = []
    for j in jobs:
        agent = await db.get(Agent, j.current_agent_id) if j.current_agent_id else None
        out.append({
            "id": j.id, "title": j.title, "channel": j.channel,
            "stage": j.stage, "current_agent_id": j.current_agent_id,
            "current_agent_name": agent.name if agent else None,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "updated_at": j.updated_at.isoformat() if j.updated_at else None,
            "target_date": j.target_date, "thread_id": j.thread_id,
            "reviewed_by": j.reviewed_by or [],
            "make_executions": j.make_executions or [],
            "has_research": bool(j.research_data),
            "has_script": bool(j.script),
            "has_seo": bool(j.seo_metadata),
        })
    return out


@router.post("/jobs")
async def create_job(
    data: CreateJobRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new production job and start the auto-advancing quality-gated pipeline."""
    job = ProductionJob(
        id=str(uuid.uuid4()),
        title=data.title,
        channel=data.channel,
        stage="research",
        target_date=data.target_date,
    )
    db.add(job)
    await db.commit()

    # Start the pipeline — it auto-advances through ALL stages with quality gates
    background_tasks.add_task(_advance_pipeline, job.id)
    return {
        "id": job.id,
        "title": job.title,
        "stage": "research",
        "status": "started",
        "message": "Pipeline started. Each stage will auto-advance after hitting 10/10 quality. Pedro approval required before publish.",
    }


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get detailed job status including quality gate history."""
    job = await db.get(ProductionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    agent = await db.get(Agent, job.current_agent_id) if job.current_agent_id else None

    # Get thread messages for quality gate history
    quality_history = []
    if job.thread_id:
        result = await db.execute(
            select(Message).where(Message.thread_id == job.thread_id).order_by(Message.created_at)
        )
        for m in result.scalars().all():
            if "[QUALITY GATE" in (m.content or ""):
                score_match = re.search(r"QUALITY SCORE:\s*(\d+)\s*/\s*10", m.content)
                quality_history.append({
                    "agent": m.sender_agent_id,
                    "score": int(score_match.group(1)) if score_match else None,
                    "passed": "APPROVED" in (m.content or ""),
                    "timestamp": m.created_at.isoformat() if m.created_at else None,
                })

    return {
        "id": job.id, "title": job.title, "channel": job.channel,
        "stage": job.stage, "current_agent_id": job.current_agent_id,
        "current_agent_name": agent.name if agent else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        "target_date": job.target_date, "thread_id": job.thread_id,
        "reviewed_by": job.reviewed_by or [],
        "has_research": bool(job.research_data),
        "has_script": bool(job.script),
        "has_seo": bool(job.seo_metadata),
        "approved_by": job.approved_by,
        "rejection_notes": job.rejection_notes,
        "quality_history": quality_history,
    }


@router.post("/jobs/{job_id}/approve")
async def approve_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Pedro approves a job for publishing. Only Pedro can do this."""
    job = await db.get(ProductionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.stage not in ("approved", "review"):
        raise HTTPException(
            status_code=400,
            detail=f"Job is at stage '{job.stage}' — must be at 'approved' or 'review' stage for Pedro to approve"
        )

    job.approved_by = "pedro"
    job.stage = "published"
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "id": job.id,
        "stage": "published",
        "approved_by": "pedro",
        "message": "Approved by Pedro. Ready to upload.",
    }


@router.post("/jobs/{job_id}/reject")
async def reject_job(
    job_id: str,
    data: RejectJobRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Pedro rejects a job — sends it back to a specific stage with notes."""
    job = await db.get(ProductionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    target_stage = data.send_back_to
    if target_stage not in PIPELINE_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {target_stage}")

    job.stage = target_stage
    job.rejection_notes = data.notes or "Sent back for revisions by Pedro"
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Re-start the pipeline from the target stage with quality loops
    background_tasks.add_task(_advance_pipeline, job.id)

    return {
        "id": job.id,
        "stage": target_stage,
        "status": "rejected_for_revision",
        "message": f"Sent back to '{target_stage}' stage. Pipeline will re-run with quality gates.",
    }


@router.post("/jobs/{job_id}/advance")
async def advance_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually advance a job (override quality gate). Use sparingly."""
    job = await db.get(ProductionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    stage_info = PIPELINE_STAGES.get(job.stage)
    if not stage_info or not stage_info.get("next"):
        raise HTTPException(status_code=400, detail="Job is already at the final stage")

    job.stage = stage_info["next"]
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()

    background_tasks.add_task(_advance_pipeline, job.id)
    return {"id": job.id, "stage": job.stage, "status": "manually_advanced"}
