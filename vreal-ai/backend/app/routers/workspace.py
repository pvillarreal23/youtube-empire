from __future__ import annotations

import uuid
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, async_session
from app.models.workspace import AgentWorkspace, ContentArtifact, AgentPipeline, AGENT_ARTIFACT_TYPES
from app.models.agent import Agent
from app.models.thread import Thread, Message
from app.services.claude_service import generate_agent_response, generate_agent_response_async
from app.services.make_integration import trigger_make_scenario

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


# === WORKSPACE ===

@router.get("/{agent_id}")
async def get_workspace(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Get an agent's workspace — creates one if it doesn't exist."""
    workspace = (await db.execute(
        select(AgentWorkspace).where(AgentWorkspace.agent_id == agent_id)
    )).scalars().first()

    if not workspace:
        workspace = AgentWorkspace(id=str(uuid.uuid4()), agent_id=agent_id)
        db.add(workspace)
        await db.commit()

    agent = await db.get(Agent, agent_id)
    artifact_types = AGENT_ARTIFACT_TYPES.get(agent_id, ["custom"])

    # Get agent's artifacts
    artifacts = (await db.execute(
        select(ContentArtifact).where(ContentArtifact.agent_id == agent_id)
        .order_by(ContentArtifact.updated_at.desc())
    )).scalars().all()

    # Get agent's pipeline actions
    pipeline = (await db.execute(
        select(AgentPipeline).where(AgentPipeline.agent_id == agent_id)
        .order_by(AgentPipeline.created_at.desc()).limit(20)
    )).scalars().all()

    return {
        "agent_id": agent_id,
        "agent_name": agent.name if agent else agent_id,
        "artifact_types": artifact_types,
        "artifacts": [{
            "id": a.id, "type": a.artifact_type, "title": a.title,
            "content": a.content[:500], "channel": a.channel,
            "status": a.status, "version": a.version,
            "pipeline_stage": a.pipeline_stage,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        } for a in artifacts],
        "pipeline": [{
            "id": p.id, "artifact_id": p.artifact_id, "action": p.action,
            "target_agent_id": p.target_agent_id, "make_scenario": p.make_scenario,
            "status": p.status, "result": p.result[:200] if p.result else "",
            "created_at": p.created_at.isoformat() if p.created_at else None,
        } for p in pipeline],
        "custom_webhooks": workspace.custom_webhooks or [],
        "notes": workspace.notes,
    }


# === CONTENT CREATION ===

class CreateArtifactRequest(BaseModel):
    artifact_type: str
    title: str
    channel: str = ""
    prompt: str = ""  # If empty, agent generates based on type and title


@router.post("/{agent_id}/create")
async def create_artifact(
    agent_id: str,
    data: CreateArtifactRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Agent creates a new content artifact using Claude."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    artifact = ContentArtifact(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        artifact_type=data.artifact_type,
        title=data.title,
        channel=data.channel,
        content="Generating...",
        status="generating",
    )
    db.add(artifact)
    await db.commit()

    # Generate content in background
    async def _generate():
        async with async_session() as s:
            a = await s.get(Agent, agent_id)
            art = await s.get(ContentArtifact, artifact.id)
            if not a or not art:
                return

            prompt = data.prompt or f"Create a {data.artifact_type} titled '{data.title}'"
            if data.channel:
                prompt += f" for the {data.channel} channel"
            prompt += ". Use your role's output format. Be specific, detailed, and production-ready."

            try:
                content = await generate_agent_response_async(
                    system_prompt=a.system_prompt,
                    thread_messages=[{"id": "gen", "sender_type": "user", "sender_agent_id": None,
                                      "content": prompt, "created_at": datetime.now(timezone.utc).isoformat(), "status": "sent"}],
                    agent_id=agent_id,
                )
                art.content = content
                art.status = "draft"
                art.updated_at = datetime.now(timezone.utc)

                # Log pipeline action
                action = AgentPipeline(
                    id=str(uuid.uuid4()), agent_id=agent_id, artifact_id=art.id,
                    action="create", status="complete", result=f"Created {data.artifact_type}: {data.title}",
                    completed_at=datetime.now(timezone.utc),
                )
                s.add(action)

                # Post to feed
                from app.routers.feed import agent_post
                await agent_post(agent_id, f"Created new {data.artifact_type}: **{data.title}**{' for ' + data.channel if data.channel else ''}", channel="content", message_type="update")

                await s.commit()
            except Exception as e:
                art.content = f"Error generating: {str(e)[:300]}"
                art.status = "failed"
                await s.commit()

    background_tasks.add_task(_generate)
    return {"id": artifact.id, "status": "generating", "type": data.artifact_type, "title": data.title}


@router.get("/{agent_id}/artifacts/{artifact_id}")
async def get_artifact(agent_id: str, artifact_id: str, db: AsyncSession = Depends(get_db)):
    """Get full content of an artifact."""
    artifact = await db.get(ContentArtifact, artifact_id)
    if not artifact or artifact.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {
        "id": artifact.id, "agent_id": artifact.agent_id,
        "type": artifact.artifact_type, "title": artifact.title,
        "content": artifact.content, "channel": artifact.channel,
        "status": artifact.status, "version": artifact.version,
        "pipeline_stage": artifact.pipeline_stage,
        "extra_data": artifact.extra_data,
        "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        "updated_at": artifact.updated_at.isoformat() if artifact.updated_at else None,
    }


# === PUSH TO PRODUCTION ===

class PushRequest(BaseModel):
    make_scenario: str = ""  # Which Make.com scenario to trigger
    target_agent_id: str = ""  # Hand off to another agent


@router.post("/{agent_id}/artifacts/{artifact_id}/push")
async def push_artifact(
    agent_id: str,
    artifact_id: str,
    data: PushRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Push an artifact through the pipeline — either to Make.com or to another agent."""
    artifact = await db.get(ContentArtifact, artifact_id)
    if not artifact or artifact.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Artifact not found")

    agent = await db.get(Agent, agent_id)

    # Option 1: Push to Make.com
    if data.make_scenario:
        pipeline_action = AgentPipeline(
            id=str(uuid.uuid4()), agent_id=agent_id, artifact_id=artifact_id,
            action="push_to_make", make_scenario=data.make_scenario, status="running",
        )
        db.add(pipeline_action)
        artifact.pipeline_stage = f"make:{data.make_scenario}"
        await db.commit()

        async def _push_make():
            async with async_session() as s:
                pa = await s.get(AgentPipeline, pipeline_action.id)
                art = await s.get(ContentArtifact, artifact_id)
                result = await trigger_make_scenario(
                    agent_id=agent_id,
                    scenario=data.make_scenario,
                    payload={"title": art.title, "content": art.content[:3000], "type": art.artifact_type, "channel": art.channel},
                    thread_id=None,
                )
                pa.status = "complete" if result.get("status") == "triggered" else result.get("status", "failed")
                pa.result = str(result)[:500]
                pa.completed_at = datetime.now(timezone.utc)
                art.make_execution_id = result.get("http_status", "")
                from app.routers.feed import agent_post
                await agent_post(agent_id, f"Pushed **{art.title}** to Make.com ({data.make_scenario}) — {result.get('status')}", channel="operations", message_type="update")
                await s.commit()

        background_tasks.add_task(_push_make)
        return {"status": "pushing_to_make", "scenario": data.make_scenario}

    # Option 2: Hand off to another agent
    if data.target_agent_id:
        target = await db.get(Agent, data.target_agent_id)
        if not target:
            raise HTTPException(status_code=404, detail="Target agent not found")

        pipeline_action = AgentPipeline(
            id=str(uuid.uuid4()), agent_id=agent_id, artifact_id=artifact_id,
            action="hand_off", target_agent_id=data.target_agent_id, status="running",
        )
        db.add(pipeline_action)
        artifact.pipeline_stage = f"handoff:{data.target_agent_id}"
        await db.commit()

        async def _hand_off():
            async with async_session() as s:
                art = await s.get(ContentArtifact, artifact_id)
                tgt = await s.get(Agent, data.target_agent_id)
                src = await s.get(Agent, agent_id)
                pa = await s.get(AgentPipeline, pipeline_action.id)

                # Create a thread for the handoff
                thread = Thread(
                    id=str(uuid.uuid4()),
                    subject=f"[Handoff] {art.title}",
                    participants=[agent_id, data.target_agent_id],
                )
                s.add(thread)

                msg = Message(
                    id=str(uuid.uuid4()), thread_id=thread.id,
                    sender_type="agent", sender_agent_id=agent_id,
                    content=f"Handing off to you: **{art.title}** ({art.artifact_type})\n\nHere's what I produced:\n\n{art.content[:2000]}",
                )
                s.add(msg)
                await s.commit()

                # Target agent responds
                try:
                    thread_msgs = [{"id": msg.id, "sender_type": "agent", "sender_agent_id": agent_id,
                                    "sender_name": src.name, "content": msg.content,
                                    "created_at": datetime.now(timezone.utc).isoformat(), "status": "sent"}]
                    response = await generate_agent_response_async(
                        system_prompt=tgt.system_prompt,
                        thread_messages=thread_msgs,
                        agent_id=data.target_agent_id,
                    )
                    resp_msg = Message(
                        id=str(uuid.uuid4()), thread_id=thread.id,
                        sender_type="agent", sender_agent_id=data.target_agent_id,
                        content=response, status="complete",
                    )
                    s.add(resp_msg)

                    # Create new artifact from target agent's response
                    new_artifact = ContentArtifact(
                        id=str(uuid.uuid4()), agent_id=data.target_agent_id,
                        artifact_type=art.artifact_type, title=f"{art.title} (from {src.name})",
                        content=response, channel=art.channel, status="draft",
                    )
                    s.add(new_artifact)

                    pa.status = "complete"
                    pa.result = f"Handed off to {tgt.name}. New artifact created."
                    pa.completed_at = datetime.now(timezone.utc)

                    from app.routers.feed import agent_post
                    await agent_post(agent_id, f"Handed off **{art.title}** to {tgt.name}", channel="operations", message_type="update")
                    await agent_post(data.target_agent_id, f"Received **{art.title}** from {src.name} — processing", channel="operations", message_type="update")

                    await s.commit()
                except Exception as e:
                    pa.status = "failed"
                    pa.result = str(e)[:300]
                    pa.completed_at = datetime.now(timezone.utc)
                    await s.commit()

        background_tasks.add_task(_hand_off)
        return {"status": "handing_off", "target": data.target_agent_id}

    return {"error": "Provide either make_scenario or target_agent_id"}


# === AUTO-PRODUCE: Agent creates + pushes through their full pipeline ===

class AutoProduceRequest(BaseModel):
    title: str
    channel: str
    prompt: str = ""


@router.post("/{agent_id}/auto-produce")
async def auto_produce(
    agent_id: str,
    data: AutoProduceRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Agent creates content AND automatically pushes it through the production pipeline.
    This is the full autonomous flow — create, produce, hand off, all in one."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    artifact_types = AGENT_ARTIFACT_TYPES.get(agent_id, ["custom"])
    primary_type = artifact_types[0] if artifact_types else "custom"

    artifact = ContentArtifact(
        id=str(uuid.uuid4()), agent_id=agent_id,
        artifact_type=primary_type, title=data.title,
        content="Auto-producing...", channel=data.channel,
        status="generating", pipeline_stage="auto-produce",
    )
    db.add(artifact)
    await db.commit()

    async def _auto_produce():
        async with async_session() as s:
            a = await s.get(Agent, agent_id)
            art = await s.get(ContentArtifact, artifact.id)
            if not a or not art:
                return

            prompt = data.prompt or f"Create a {primary_type} titled '{data.title}' for the {data.channel} channel."
            prompt += " Make it production-ready. Use your full output format."

            try:
                content = await generate_agent_response_async(
                    system_prompt=a.system_prompt,
                    thread_messages=[{"id": "ap", "sender_type": "user", "sender_agent_id": None,
                                      "content": prompt, "created_at": datetime.now(timezone.utc).isoformat(), "status": "sent"}],
                    agent_id=agent_id,
                )
                art.content = content
                art.status = "draft"
                art.pipeline_stage = "produced"
                art.updated_at = datetime.now(timezone.utc)

                s.add(AgentPipeline(
                    id=str(uuid.uuid4()), agent_id=agent_id, artifact_id=art.id,
                    action="auto-produce", status="complete",
                    result=f"Auto-produced {primary_type}: {data.title}",
                    completed_at=datetime.now(timezone.utc),
                ))

                from app.routers.feed import agent_post
                await agent_post(agent_id, f"Auto-produced **{data.title}** for {data.channel} ({primary_type}) — ready for pipeline", channel="content", message_type="milestone")

                await s.commit()

                # Auto-trigger Make.com if the agent has a matching scenario
                from app.services.make_integration import AGENT_PERMISSIONS, MAKE_WEBHOOKS
                agent_perms = AGENT_PERMISSIONS.get(agent_id, [])
                for scenario in agent_perms:
                    webhook = MAKE_WEBHOOKS.get(scenario, "")
                    if webhook:  # Only trigger if webhook is configured
                        await trigger_make_scenario(
                            agent_id=agent_id, scenario=scenario,
                            payload={"title": data.title, "content": content[:3000], "channel": data.channel, "type": primary_type},
                        )
                        art.make_execution_id = scenario
                        await s.commit()
                        break  # Only trigger first matching scenario

            except Exception as e:
                art.content = f"Error: {str(e)[:300]}"
                art.status = "failed"
                await s.commit()

    background_tasks.add_task(_auto_produce)
    return {"id": artifact.id, "status": "auto-producing", "type": primary_type, "title": data.title, "channel": data.channel}


# === LIST ALL ARTIFACTS ACROSS ALL AGENTS ===

@router.get("/all/artifacts")
async def list_all_artifacts(limit: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ContentArtifact).order_by(ContentArtifact.updated_at.desc()).limit(limit)
    )
    artifacts = result.scalars().all()
    out = []
    for a in artifacts:
        agent = await db.get(Agent, a.agent_id)
        out.append({
            "id": a.id, "agent_id": a.agent_id,
            "agent_name": agent.name if agent else a.agent_id,
            "type": a.artifact_type, "title": a.title,
            "channel": a.channel, "status": a.status,
            "pipeline_stage": a.pipeline_stage,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        })
    return out
