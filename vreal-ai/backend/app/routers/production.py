from __future__ import annotations

import uuid
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.database import get_db, async_session
from app.models.production import ProductionJob, PIPELINE_STAGES, CHANNEL_MANAGERS
from app.models.thread import Thread, Message
from app.models.agent import Agent
from app.models.scheduler import Escalation
from app.services.claude_service import generate_agent_response, generate_agent_response_async
from app.services.make_integration import trigger_make_scenario

router = APIRouter(prefix="/api/production", tags=["production"])


class CreateJobRequest(BaseModel):
    title: str
    channel: str
    target_date: str = ""


async def _advance_pipeline(job_id: str):
    """Auto-advance a production job to the next stage, triggering the responsible agent."""
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
            "research": f"Research trending angles and data for a video titled '{job.title}' on the {job.channel} channel. Find key facts, statistics, competitor content, and unique angles. Provide a comprehensive research package.",
            "scripted": f"Write a complete video script for '{job.title}' on the {job.channel} channel. Use the research provided in this thread. Follow your SCRIPT format with hook, sections, and CTA. Target 8-12 minutes.",
            "voiceover": f"The script for '{job.title}' is ready. Prepare voiceover direction notes — pacing, emphasis, tone shifts, and pronunciation guides. Then trigger the ElevenLabs voiceover generation.",
            "thumbnail": f"Create 3 thumbnail concepts for '{job.title}' on {job.channel}. Use your THUMBNAIL BRIEF format with safe, bold, and experimental options. Consider CTR optimization for this topic.",
            "edited": f"The voiceover and thumbnail for '{job.title}' are ready. Prepare video editing notes — cut list, B-roll suggestions, graphics, text overlays, and music. Then trigger the video assembly.",
            "seo": f"Optimize SEO for '{job.title}' on {job.channel}. Prepare the full SEO PACKAGE — title options, description, tags, chapters, end screens, and cards. Target high-CTR keywords.",
            "review": f"QA review for '{job.title}' on {job.channel}. Run through your complete QA CHECKLIST. Check content accuracy, production quality, SEO metadata, brand consistency, and compliance. Give a verdict.",
            "approved": f"'{job.title}' has passed QA review for {job.channel}. Prepare final approval summary with publish recommendation. If everything is ready, recommend scheduling for {job.target_date or 'optimal time'}. This needs Pedro's sign-off to go live.",
        }

        prompt = stage_prompts.get(job.stage, f"Process stage '{job.stage}' for '{job.title}'")

        # Add context about previous stages
        context_parts = []
        if job.research_data:
            context_parts.append(f"[Research completed]\n{job.research_data[:500]}")
        if job.script:
            context_parts.append(f"[Script completed]\n{job.script[:500]}")
        if context_parts:
            prompt += "\n\nPrevious work:\n" + "\n---\n".join(context_parts)

        # Send message to the thread
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=job.thread_id,
            sender_type="user",
            sender_agent_id=None,
            content=f"[Pipeline — Stage: {job.stage.upper()}]\n\n{prompt}",
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

            # Trigger Make.com if applicable
            make_scenario = stage_info.get("make_scenario")
            if make_scenario:
                make_result = await trigger_make_scenario(
                    agent_id=agent_id,
                    scenario=make_scenario,
                    payload={"title": job.title, "channel": job.channel, "stage": job.stage, "content": response[:2000]},
                    thread_id=job.thread_id,
                )
                executions = job.make_executions or []
                executions.append({
                    "scenario": make_scenario,
                    "status": make_result.get("status"),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                job.make_executions = executions

            # If this is the "approved" stage, create an escalation for Pedro
            if job.stage == "approved":
                escalation = Escalation(
                    id=str(uuid.uuid4()),
                    thread_id=job.thread_id,
                    agent_id=agent_id,
                    reason=f"PUBLISH APPROVAL: '{job.title}' for {job.channel} is ready to go live. Review the thread and approve for publishing.",
                    severity="critical",
                )
                db.add(escalation)

            # Add to reviewed_by
            reviewed = job.reviewed_by or []
            if agent_id not in reviewed:
                job.reviewed_by = reviewed + [agent_id]

            await db.commit()

        except Exception as e:
            print(f"[PRODUCTION] Pipeline error at stage '{job.stage}' for '{job.title}': {e}")


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
    """Create a new production job and start the pipeline."""
    job = ProductionJob(
        id=str(uuid.uuid4()),
        title=data.title,
        channel=data.channel,
        stage="research",
        target_date=data.target_date,
    )
    db.add(job)
    await db.commit()

    # Start the pipeline
    background_tasks.add_task(_advance_pipeline, job.id)
    return {"id": job.id, "title": job.title, "stage": "research", "status": "started"}


@router.post("/jobs/{job_id}/advance")
async def advance_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Manually advance a job to the next pipeline stage."""
    job = await db.get(ProductionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    stage_info = PIPELINE_STAGES.get(job.stage)
    if not stage_info or not stage_info.get("next"):
        raise HTTPException(status_code=400, detail="Job is already at the final stage")

    job.stage = stage_info["next"]
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Trigger next agent
    background_tasks.add_task(_advance_pipeline, job.id)
    return {"id": job.id, "stage": job.stage, "status": "advancing"}


@router.post("/jobs/{job_id}/approve")
async def approve_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Pedro approves a job for publishing."""
    job = await db.get(ProductionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.approved_by = "pedro"
    job.stage = "published"
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Trigger Make.com upload
    await trigger_make_scenario(
        agent_id="ceo-agent",
        scenario="upload_schedule",
        payload={"title": job.title, "channel": job.channel, "job_id": job.id},
        thread_id=job.thread_id,
    )

    return {"id": job.id, "stage": "published", "approved_by": "pedro"}


@router.post("/jobs/{job_id}/reject")
async def reject_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Reject and send back for revisions."""
    job = await db.get(ProductionJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Send back to scripted stage for revisions
    job.stage = "scripted"
    job.rejection_notes = "Sent back for revisions by Pedro"
    job.updated_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": job.id, "stage": "scripted", "status": "rejected_for_revision"}
