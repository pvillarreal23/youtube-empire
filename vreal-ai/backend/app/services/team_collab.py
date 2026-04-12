"""
Claude Team Collaboration System

Agents can autonomously start conversations with each other,
collaborate on tasks, and escalate through the chain of command.

This is the "brain" that makes the 32 agents act as a real team:
- Agents can request help from collaborators
- VPs hold cross-team meetings
- CEO gets synthesis reports
- Everything is logged and visible in the feed
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import async_session
from app.models.thread import Thread, Message
from app.models.agent import Agent
from app.services.claude_service import generate_agent_response, generate_agent_response_async


# Collaboration types that agents can initiate
COLLAB_TYPES = {
    "brainstorm": {
        "desc": "Multi-agent brainstorm on a topic",
        "max_rounds": 3,
        "prompt_template": "You're in a brainstorm session with {participants}. Topic: {topic}. Share your perspective based on your role and expertise. Build on what others have said. Be specific and actionable.",
    },
    "review": {
        "desc": "Cross-functional review of work product",
        "max_rounds": 2,
        "prompt_template": "Review the following work from {from_agent}: {content}. Provide feedback from your perspective as {role}. Be constructive and specific.",
    },
    "handoff": {
        "desc": "Hand off completed work to the next agent in the pipeline",
        "max_rounds": 1,
        "prompt_template": "{from_agent} has completed their work and is handing off to you. Here's what they produced: {content}. Take it from here and do your part.",
    },
    "standup": {
        "desc": "Team standup — each agent reports status",
        "max_rounds": 1,
        "prompt_template": "This is the daily standup for the {department} team. Report: 1) What you completed since last standup, 2) What you're working on today, 3) Any blockers.",
    },
    "strategy": {
        "desc": "Strategic discussion between VPs and CEO",
        "max_rounds": 3,
        "prompt_template": "Strategic discussion topic: {topic}. As {role}, share your analysis, concerns, and recommendations. This discussion will inform the CEO's decision.",
    },
}


async def start_collaboration(
    collab_type: str,
    initiator_id: str,
    participant_ids: list[str],
    topic: str,
    context: str = "",
) -> dict:
    """Start a multi-agent collaboration session."""
    async with async_session() as db:
        collab = COLLAB_TYPES.get(collab_type)
        if not collab:
            return {"error": f"Unknown collaboration type: {collab_type}"}

        initiator = await db.get(Agent, initiator_id)
        if not initiator:
            return {"error": f"Agent not found: {initiator_id}"}

        # Create thread
        all_participants = [initiator_id] + [p for p in participant_ids if p != initiator_id]
        thread = Thread(
            id=str(uuid.uuid4()),
            subject=f"[{collab_type.title()}] {topic[:50]}",
            participants=all_participants,
        )
        db.add(thread)

        # Initial message from initiator
        init_prompt = f"[{collab_type.upper()} SESSION]\nTopic: {topic}\nParticipants: {', '.join(all_participants)}\n"
        if context:
            init_prompt += f"\nContext:\n{context[:1000]}\n"
        init_prompt += f"\nAs the initiator ({initiator.name}), kick off this {collab_type} session."

        init_msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            sender_type="user",
            sender_agent_id=None,
            content=init_prompt,
        )
        db.add(init_msg)
        await db.commit()

        # Get initiator's response
        thread_msgs = [{
            "id": init_msg.id, "sender_type": "user", "sender_agent_id": None,
            "content": init_msg.content, "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent",
        }]

        try:
            initiator_response = await generate_agent_response_async(
                system_prompt=initiator.system_prompt,
                thread_messages=thread_msgs,
                agent_id=initiator_id,
            )

            msg1 = Message(
                id=str(uuid.uuid4()),
                thread_id=thread.id,
                sender_type="agent",
                sender_agent_id=initiator_id,
                content=initiator_response,
                status="complete",
            )
            db.add(msg1)
            await db.commit()

            # Each participant responds in turn
            for round_num in range(collab["max_rounds"]):
                for pid in participant_ids:
                    if pid == initiator_id:
                        continue

                    participant = await db.get(Agent, pid)
                    if not participant:
                        continue

                    # Fetch full thread history
                    result = await db.execute(
                        select(Message).where(Message.thread_id == thread.id).order_by(Message.created_at)
                    )
                    history = []
                    for m in result.scalars().all():
                        a = await db.get(Agent, m.sender_agent_id) if m.sender_agent_id else None
                        history.append({
                            "id": m.id, "sender_type": m.sender_type,
                            "sender_agent_id": m.sender_agent_id,
                            "sender_name": a.name if a else None,
                            "content": m.content,
                            "created_at": m.created_at.isoformat() if m.created_at else None,
                            "status": m.status,
                        })

                    response = await generate_agent_response_async(
                        system_prompt=participant.system_prompt,
                        thread_messages=history,
                        agent_id=pid,
                    )

                    resp_msg = Message(
                        id=str(uuid.uuid4()),
                        thread_id=thread.id,
                        sender_type="agent",
                        sender_agent_id=pid,
                        content=response,
                        status="complete",
                    )
                    db.add(resp_msg)
                    await db.commit()

            # Post summary to feed
            from app.routers.feed import agent_post
            participant_names = []
            for pid in all_participants:
                a = await db.get(Agent, pid)
                if a:
                    participant_names.append(a.name)

            await agent_post(
                agent_id=initiator_id,
                content=f"**{collab_type.title()} Session Complete** — {topic}\n\nParticipants: {', '.join(participant_names)}\n\nThread has {len(all_participants)} agent responses.",
                channel="general",
                message_type="update",
                thread_id=thread.id,
            )

            return {
                "status": "complete",
                "thread_id": thread.id,
                "participants": all_participants,
                "rounds": collab["max_rounds"],
            }

        except Exception as e:
            return {"status": "error", "error": str(e)[:300], "thread_id": thread.id}


# Pre-defined team meetings that run on schedule
TEAM_MEETINGS = {
    "executive_sync": {
        "type": "strategy",
        "initiator": "ceo-agent",
        "participants": ["content-vp-agent", "operations-vp-agent", "analytics-vp-agent", "monetization-vp-agent"],
        "topic": "Weekly executive sync — review empire performance, align on priorities, address cross-team issues",
    },
    "content_standup": {
        "type": "standup",
        "initiator": "content-vp-agent",
        "participants": ["ai-and-tech-channel-manager-agent", "finance-channel-manager-agent", "psychology-channel-manager-agent", "scriptwriter-agent"],
        "topic": "Content team daily standup",
    },
    "ops_standup": {
        "type": "standup",
        "initiator": "operations-vp-agent",
        "participants": ["project-manager-agent", "qa-lead-agent", "video-editor-agent", "web-developer-agent"],
        "topic": "Operations team daily standup",
    },
    "growth_brainstorm": {
        "type": "brainstorm",
        "initiator": "analytics-vp-agent",
        "participants": ["trend-researcher-agent", "seo-specialist-agent", "data-analyst-agent", "content-vp-agent"],
        "topic": "Growth brainstorm — how to accelerate subscriber growth across all channels toward 1B goal",
    },
    "monetization_review": {
        "type": "review",
        "initiator": "monetization-vp-agent",
        "participants": ["partnership-manager-agent", "affiliate-coordinator-agent", "newsletter-strategist-agent", "digital-product-manager-agent"],
        "topic": "Weekly revenue review — all streams, pipeline, optimization opportunities",
    },
}
