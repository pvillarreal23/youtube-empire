from __future__ import annotations

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.database import get_db, async_session
from app.models.social import SocialAccount, SocialPost, AccountProposal, PLATFORMS, PLATFORM_AGENTS
from app.models.agent import Agent
from app.models.scheduler import Escalation
from app.services.claude_service import generate_agent_response, generate_agent_response_async
from app.services.make_integration import trigger_make_scenario

router = APIRouter(prefix="/api/social", tags=["social"])


# === ACCOUNTS ===

@router.get("/platforms")
async def list_platforms():
    return PLATFORMS


@router.get("/accounts")
async def list_accounts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SocialAccount).order_by(SocialAccount.platform))
    accounts = result.scalars().all()
    return [{
        "id": a.id, "platform": a.platform, "account_name": a.account_name,
        "display_name": a.display_name, "channel_brand": a.channel_brand,
        "managed_by": a.managed_by, "status": a.status,
        "followers": a.followers, "url": a.url,
        "created_at": a.created_at.isoformat() if a.created_at else None,
    } for a in accounts]


class RegisterAccountRequest(BaseModel):
    platform: str
    account_name: str
    display_name: str = ""
    channel_brand: str = ""
    url: str = ""
    make_webhook: str = ""


@router.post("/accounts")
async def register_account(data: RegisterAccountRequest, db: AsyncSession = Depends(get_db)):
    """Register an existing social media account for agents to manage."""
    if data.platform not in PLATFORMS:
        raise HTTPException(status_code=400, detail=f"Unknown platform: {data.platform}")

    # Auto-assign managing agent
    managing_agents = PLATFORM_AGENTS.get(data.platform, ["social-media-manager-agent"])

    account = SocialAccount(
        id=str(uuid.uuid4()),
        platform=data.platform,
        account_name=data.account_name,
        display_name=data.display_name or data.account_name,
        channel_brand=data.channel_brand,
        managed_by=managing_agents[0],
        url=data.url,
        make_webhook=data.make_webhook,
    )
    db.add(account)
    await db.commit()

    # Notify feed
    from app.routers.feed import agent_post
    await agent_post(
        managing_agents[0],
        f"New {PLATFORMS[data.platform]['emoji']} {PLATFORMS[data.platform]['name']} account registered: **{data.account_name}** ({data.channel_brand}). I'm now managing this account.",
        channel="general", message_type="milestone",
    )

    return {"id": account.id, "status": "registered", "managed_by": managing_agents[0]}


# === PROPOSALS — Agents propose new accounts ===

@router.get("/proposals")
async def list_proposals(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccountProposal).order_by(AccountProposal.created_at.desc()))
    proposals = result.scalars().all()
    out = []
    for p in proposals:
        agent = await db.get(Agent, p.agent_id)
        out.append({
            "id": p.id, "agent_id": p.agent_id,
            "agent_name": agent.name if agent else p.agent_id,
            "platform": p.platform, "proposed_name": p.proposed_name,
            "channel_brand": p.channel_brand, "rationale": p.rationale,
            "content_strategy": p.content_strategy, "growth_target": p.growth_target,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return out


class ProposeAccountRequest(BaseModel):
    platform: str
    proposed_name: str
    channel_brand: str = ""
    prompt: str = ""  # Agent generates rationale if empty


@router.post("/proposals/{agent_id}")
async def propose_account(
    agent_id: str,
    data: ProposeAccountRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Agent proposes a new social media account — creates escalation for Pedro."""
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    proposal = AccountProposal(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        platform=data.platform,
        proposed_name=data.proposed_name,
        channel_brand=data.channel_brand,
        rationale="Generating strategy...",
        status="pending",
    )
    db.add(proposal)
    await db.commit()

    async def _generate_strategy():
        async with async_session() as s:
            a = await s.get(Agent, agent_id)
            p = await s.get(AccountProposal, proposal.id)
            if not a or not p:
                return

            prompt = data.prompt or (
                f"Propose a new {data.platform} account called '{data.proposed_name}' "
                f"for the {data.channel_brand or 'YouTube Empire'} brand. "
                f"Explain: 1) Why we need this account, 2) Content strategy (what we'll post), "
                f"3) Growth target for the first 90 days, 4) How it fits into our 1B subscriber goal. "
                f"Be specific and data-driven."
            )

            try:
                response = await generate_agent_response_async(
                    system_prompt=a.system_prompt,
                    thread_messages=[{"id": "prop", "sender_type": "user", "sender_agent_id": None,
                                      "content": prompt, "created_at": datetime.now(timezone.utc).isoformat(), "status": "sent"}],
                    agent_id=agent_id,
                )
                p.rationale = response
                p.content_strategy = response

                # Create escalation for Pedro
                esc = Escalation(
                    id=str(uuid.uuid4()),
                    thread_id="",
                    agent_id=agent_id,
                    reason=f"NEW ACCOUNT PROPOSAL: {PLATFORMS.get(data.platform, {}).get('emoji', '')} {data.platform} — '{data.proposed_name}' for {data.channel_brand}. Review the proposal and approve/reject.",
                    severity="high",
                )
                s.add(esc)

                from app.routers.feed import agent_post
                await agent_post(
                    agent_id,
                    f"Proposed new {PLATFORMS.get(data.platform, {}).get('emoji', '')} {data.platform} account: **{data.proposed_name}** for {data.channel_brand}. Awaiting Pedro's approval.",
                    channel="alerts", message_type="request", severity="warning",
                )

                await s.commit()
            except Exception as e:
                p.rationale = f"Error: {str(e)[:300]}"
                await s.commit()

    background_tasks.add_task(_generate_strategy)
    return {"id": proposal.id, "status": "pending", "platform": data.platform, "name": data.proposed_name}


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    """Pedro approves a new account proposal."""
    proposal = await db.get(AccountProposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    proposal.status = "approved"
    proposal.reviewed_at = datetime.now(timezone.utc)

    # Create the account entry as "pending_creation" — Pedro still needs to actually create it on the platform
    account = SocialAccount(
        id=str(uuid.uuid4()),
        platform=proposal.platform,
        account_name=proposal.proposed_name,
        display_name=proposal.proposed_name,
        channel_brand=proposal.channel_brand,
        status="pending_creation",
    )
    db.add(account)
    await db.commit()

    from app.routers.feed import agent_post
    await agent_post(
        proposal.agent_id,
        f"Account APPROVED: {PLATFORMS.get(proposal.platform, {}).get('emoji', '')} {proposal.proposed_name} on {proposal.platform}. Pedro needs to create the account, then we'll start posting.",
        channel="wins", message_type="milestone", severity="celebration",
    )

    return {"status": "approved", "account_id": account.id, "message": "Account approved. Create it on the platform, then update the URL and webhook."}


@router.post("/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: str, db: AsyncSession = Depends(get_db)):
    proposal = await db.get(AccountProposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal.status = "rejected"
    proposal.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    return {"status": "rejected"}


# === POSTS — Agents create and schedule posts ===

class CreatePostRequest(BaseModel):
    account_id: str
    post_type: str = "post"
    prompt: str = ""
    content: str = ""  # If provided, use this directly instead of generating


@router.post("/posts/{agent_id}")
async def create_post(
    agent_id: str,
    data: CreatePostRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Agent creates a post for a social media account."""
    agent = await db.get(Agent, agent_id)
    account = await db.get(SocialAccount, data.account_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    platform_config = PLATFORMS.get(account.platform, {})

    post = SocialPost(
        id=str(uuid.uuid4()),
        account_id=data.account_id,
        agent_id=agent_id,
        platform=account.platform,
        content=data.content or "Generating...",
        post_type=data.post_type,
        status="generating" if not data.content else "draft",
    )
    db.add(post)
    await db.commit()

    if not data.content:
        async def _generate_post():
            async with async_session() as s:
                a = await s.get(Agent, agent_id)
                p = await s.get(SocialPost, post.id)
                acc = await s.get(SocialAccount, data.account_id)
                if not a or not p:
                    return

                prompt = data.prompt or (
                    f"Create a {data.post_type} for {platform_config.get('name', account.platform)} "
                    f"account '{acc.account_name}' ({acc.channel_brand}). "
                    f"Max length: {platform_config.get('max_post_length', 280)} chars. "
                    f"Make it engaging, on-brand, and optimized for {account.platform}. "
                    f"Include relevant hashtags."
                )

                try:
                    content = await generate_agent_response_async(
                        system_prompt=a.system_prompt,
                        thread_messages=[{"id": "post", "sender_type": "user", "sender_agent_id": None,
                                          "content": prompt, "created_at": datetime.now(timezone.utc).isoformat(), "status": "sent"}],
                        agent_id=agent_id,
                    )
                    p.content = content
                    p.status = "draft"

                    from app.routers.feed import agent_post as feed_post
                    await feed_post(agent_id, f"Created {data.post_type} for {platform_config.get('emoji', '')} {acc.account_name}: {content[:100]}...", channel="content", message_type="update")

                    await s.commit()
                except Exception as e:
                    p.content = f"Error: {str(e)[:300]}"
                    p.status = "failed"
                    await s.commit()

        background_tasks.add_task(_generate_post)

    return {"id": post.id, "status": post.status, "platform": account.platform, "account": account.account_name}


@router.get("/posts")
async def list_posts(account_id: str = "", limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = select(SocialPost).order_by(SocialPost.created_at.desc()).limit(limit)
    if account_id:
        query = query.where(SocialPost.account_id == account_id)
    result = await db.execute(query)
    posts = result.scalars().all()
    out = []
    for p in posts:
        agent = await db.get(Agent, p.agent_id)
        account = await db.get(SocialAccount, p.account_id)
        out.append({
            "id": p.id, "account_id": p.account_id,
            "account_name": account.account_name if account else "",
            "platform": p.platform, "agent_id": p.agent_id,
            "agent_name": agent.name if agent else p.agent_id,
            "content": p.content[:300], "post_type": p.post_type,
            "hashtags": p.hashtags, "status": p.status,
            "scheduled_for": p.scheduled_for,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })
    return out


@router.post("/posts/{post_id}/publish")
async def publish_post(post_id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Push a post to Make.com for publishing."""
    post = await db.get(SocialPost, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    account = await db.get(SocialAccount, post.account_id)

    post.status = "publishing"
    await db.commit()

    async def _publish():
        async with async_session() as s:
            p = await s.get(SocialPost, post_id)
            acc = await s.get(SocialAccount, post.account_id)

            result = await trigger_make_scenario(
                agent_id=p.agent_id,
                scenario="social_post",
                payload={
                    "platform": p.platform,
                    "account": acc.account_name if acc else "",
                    "content": p.content,
                    "post_type": p.post_type,
                    "hashtags": p.hashtags,
                },
            )

            if result.get("status") in ["triggered", "queued_for_approval"]:
                p.status = "posted" if result["status"] == "triggered" else "pending_approval"
                p.posted_at = datetime.now(timezone.utc)
                p.make_execution_id = str(result.get("http_status", ""))
            else:
                p.status = "failed"

            from app.routers.feed import agent_post
            await agent_post(
                p.agent_id,
                f"{'Published' if p.status == 'posted' else 'Queued'} {p.post_type} on {PLATFORMS.get(p.platform, {}).get('emoji', '')} {acc.account_name if acc else p.platform}: {p.content[:80]}...",
                channel="content", message_type="update",
            )
            await s.commit()

    background_tasks.add_task(_publish)
    return {"status": "publishing", "post_id": post_id}
