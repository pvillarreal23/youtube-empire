from __future__ import annotations

import uuid
import asyncio
import re
from datetime import datetime, timezone
from sqlalchemy import select, update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.database import async_session
from app.models.scheduler import ScheduledTask, TaskRun, Escalation
from app.models.thread import Thread, Message
from app.models.agent import Agent
from app.services.claude_service import generate_agent_response, analyze_routing

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone="UTC")

ESCALATION_KEYWORDS = [
    "need your approval", "requires human", "escalate", "pedro",
    "your decision", "need your input", "awaiting your", "human review",
    "cannot proceed without", "please confirm", "need authorization",
    "budget approval", "legal review", "compliance concern",
]


async def run_scheduled_task(task_id: str):
    """Execute a single scheduled task — create thread, get agent response, check for escalation."""
    async with async_session() as db:
        task = await db.get(ScheduledTask, task_id)
        if not task or not task.enabled:
            return

        agent = await db.get(Agent, task.agent_id)
        if not agent:
            return

        # Create a task run record
        run = TaskRun(
            id=str(uuid.uuid4()),
            scheduled_task_id=task.id,
            agent_id=task.agent_id,
            task_name=task.name,
            status="running",
        )
        db.add(run)

        # Create a thread for this task
        thread = Thread(
            id=str(uuid.uuid4()),
            subject=f"[Auto] {task.name}",
            participants=[task.agent_id],
        )
        db.add(thread)

        # Create the initial system message
        msg = Message(
            id=str(uuid.uuid4()),
            thread_id=thread.id,
            sender_type="user",
            sender_agent_id=None,
            content=f"[Automated Task — {task.name}]\n\n{task.prompt}",
        )
        db.add(msg)
        run.thread_id = thread.id
        task.last_run = datetime.now(timezone.utc)
        await db.commit()

        # Generate agent response
        try:
            thread_msgs = [{
                "id": msg.id,
                "sender_type": "user",
                "sender_agent_id": None,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else None,
                "status": "sent",
            }]

            response_text = generate_agent_response(
                system_prompt=agent.system_prompt,
                thread_messages=thread_msgs,
                agent_id=task.agent_id,
            )

            # Save response
            agent_msg = Message(
                id=str(uuid.uuid4()),
                thread_id=thread.id,
                sender_type="agent",
                sender_agent_id=task.agent_id,
                content=response_text,
                status="complete",
            )
            db.add(agent_msg)

            # Create summary (first 200 chars)
            run.summary = response_text[:200].replace("\n", " ")
            run.status = "complete"
            run.completed_at = datetime.now(timezone.utc)

            # Post to live feed
            from app.routers.feed import agent_post
            await agent_post(
                agent_id=task.agent_id,
                content=f"**{task.name}** completed.\n\n{response_text[:300]}",
                channel=task.category if task.category in ("content", "operations", "analytics", "monetization") else "general",
                message_type="report",
                thread_id=thread.id,
            )

            # Check for escalation
            lower_response = response_text.lower()
            escalation_reasons = [kw for kw in ESCALATION_KEYWORDS if kw in lower_response]
            if escalation_reasons:
                escalation = Escalation(
                    id=str(uuid.uuid4()),
                    thread_id=thread.id,
                    agent_id=task.agent_id,
                    reason=f"Agent flagged: {', '.join(escalation_reasons[:3])}",
                    severity="medium" if len(escalation_reasons) < 2 else "high",
                )
                db.add(escalation)
                run.status = "escalated"

                await agent_post(
                    agent_id=task.agent_id,
                    content=f"**Escalation** — {task.name}\n\n{', '.join(escalation_reasons[:3])}. Needs your review.",
                    channel="alerts",
                    message_type="alert",
                    severity="urgent",
                    thread_id=thread.id,
                )

            # Route to other agents if needed
            all_agents_result = await db.execute(select(Agent))
            all_agents = {a.id: a.name for a in all_agents_result.scalars().all()}

            routed = analyze_routing(
                agent_name=agent.name,
                agent_role=agent.role,
                response_text=response_text,
                reports_to=agent.reports_to,
                direct_reports=agent.direct_reports or [],
                collaborates_with=agent.collaborates_with or [],
                all_agent_names=all_agents,
            )

            for next_agent_id in routed[:2]:
                next_agent = await db.get(Agent, next_agent_id)
                if not next_agent:
                    continue

                # Add the routed agent to participants
                participants = thread.participants or []
                if next_agent_id not in participants:
                    thread.participants = participants + [next_agent_id]

                # Get full thread messages for context
                result = await db.execute(
                    select(Message).where(Message.thread_id == thread.id).order_by(Message.created_at)
                )
                all_msgs = []
                for m in result.scalars().all():
                    a = await db.get(Agent, m.sender_agent_id) if m.sender_agent_id else None
                    all_msgs.append({
                        "id": m.id, "sender_type": m.sender_type,
                        "sender_agent_id": m.sender_agent_id,
                        "sender_name": a.name if a else None,
                        "content": m.content,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                        "status": m.status,
                    })

                routed_response = generate_agent_response(
                    system_prompt=next_agent.system_prompt,
                    thread_messages=all_msgs,
                    agent_id=next_agent_id,
                )

                routed_msg = Message(
                    id=str(uuid.uuid4()),
                    thread_id=thread.id,
                    sender_type="agent",
                    sender_agent_id=next_agent_id,
                    content=routed_response,
                    status="complete",
                )
                db.add(routed_msg)

                # Log routed agent run
                routed_run = TaskRun(
                    id=str(uuid.uuid4()),
                    scheduled_task_id=task.id,
                    thread_id=thread.id,
                    agent_id=next_agent_id,
                    task_name=f"{task.name} (delegated)",
                    status="complete",
                    completed_at=datetime.now(timezone.utc),
                    summary=routed_response[:200].replace("\n", " "),
                )
                db.add(routed_run)

            await db.commit()

        except Exception as e:
            run.status = "failed"
            run.error = str(e)[:500]
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()
            print(f"[SCHEDULER] Task '{task.name}' failed: {e}")


# ========== DEFAULT TASK DEFINITIONS ==========

DEFAULT_TASKS = [
    # CEO
    {"agent_id": "ceo-agent", "name": "Weekly Strategic Review", "cron": "0 9 * * 1", "category": "executive",
     "prompt": "Conduct your weekly strategic review. Assess the empire's performance across all channels, flag any concerns, set priorities for this week, and issue directives to the VPs. If anything needs my direct approval, escalate it clearly."},
    {"agent_id": "ceo-agent", "name": "Monthly OKR Check", "cron": "0 10 1 * *", "category": "executive",
     "prompt": "Review progress on our monthly OKRs. Score each objective, identify what's on track and what's at risk. Recommend adjustments and escalate any blockers that need my decision."},

    # Content VP
    {"agent_id": "content-vp", "name": "Daily Content Calendar Review", "cron": "0 8 * * *", "category": "content",
     "prompt": "Review today's content calendar across all channels. Confirm what's publishing today, what's in production, and flag any gaps or delays. Coordinate with channel managers on any issues."},
    {"agent_id": "content-vp", "name": "Weekly Performance Debrief", "cron": "0 14 * * 5", "category": "content",
     "prompt": "Conduct the weekly content performance debrief. Analyze this week's published videos across all channels. What performed above/below expectations? What patterns do you see? Provide recommendations for next week."},

    # Operations VP
    {"agent_id": "operations-vp", "name": "Daily Pipeline Health Check", "cron": "0 7 * * *", "category": "operations",
     "prompt": "Run the daily pipeline health check. Check buffer depth for each channel, identify bottlenecks, verify on-time delivery status, and flag any resource conflicts. Report status using your OPS STATUS REPORT format."},
    {"agent_id": "operations-vp", "name": "Weekly Capacity Review", "cron": "0 9 * * 5", "category": "operations",
     "prompt": "Conduct the weekly capacity review. Assess team workload, identify overallocation, and plan resource allocation for next week. Flag if we need to adjust publishing cadence."},

    # Analytics VP
    {"agent_id": "analytics-vp", "name": "Daily Metrics Pull", "cron": "0 6 * * *", "category": "analytics",
     "prompt": "Pull and analyze yesterday's performance metrics across all channels. Report on views, watch time, CTR, subscriber changes, and revenue. Flag any anomalies (>15% deviation from average)."},
    {"agent_id": "analytics-vp", "name": "Weekly Analytics Report", "cron": "0 10 * * 1", "category": "analytics",
     "prompt": "Produce the weekly analytics report for the CEO. Include highlights, concerns, deep dives on the most important trend, and specific actionable recommendations. Use your ANALYTICS REPORT format."},

    # Monetization VP
    {"agent_id": "monetization-vp", "name": "Weekly Revenue Report", "cron": "0 10 * * 2", "category": "monetization",
     "prompt": "Produce the weekly revenue report. Break down all revenue streams, compare to previous week, identify optimization opportunities, and update the pipeline of upcoming deals/launches."},
    {"agent_id": "monetization-vp", "name": "Monthly Partnership Pipeline Review", "cron": "0 11 1 * *", "category": "monetization",
     "prompt": "Review the partnership pipeline. Assess active deals, pending proposals, and upcoming renewals. Identify new partnership opportunities and recommend priorities for this month."},

    # Channel Managers
    {"agent_id": "ai-and-tech-channel-manager", "name": "Daily AI Trend Scan", "cron": "0 7 * * *", "category": "content",
     "prompt": "Scan for trending AI and tech topics today. Check YouTube trending, Google Trends, Reddit r/artificial, Twitter/X tech discussions, and HackerNews. Report any content opportunities with urgency level."},
    {"agent_id": "ai-and-tech-channel-manager", "name": "Weekly Content Proposals", "cron": "0 9 * * 2", "category": "content",
     "prompt": "Propose 5 video topics for The AI Edge this week. Use your CONTENT PROPOSAL format. Prioritize by trending potential and SEO opportunity. Include at least 1 evergreen and 1 trending topic."},

    {"agent_id": "finance-and-business-channel-manager", "name": "Daily Finance News Scan", "cron": "0 7 * * *", "category": "content",
     "prompt": "Scan for trending personal finance and investing topics. Check market movements, economic news, policy changes, and social media finance discussions. Flag time-sensitive content opportunities."},
    {"agent_id": "finance-and-business-channel-manager", "name": "Weekly Content Proposals", "cron": "0 9 * * 2", "category": "content",
     "prompt": "Propose 4 video topics for Cash Flow Code this week. Use your CONTENT PROPOSAL format. Ensure all financial disclaimers are planned. Include market-relevant and evergreen topics."},

    {"agent_id": "psychology-and-behavior-channel-manager", "name": "Weekly Content Proposals", "cron": "0 9 * * 2", "category": "content",
     "prompt": "Propose 3 video topics for Mind Shift this week. Use your CONTENT PROPOSAL format. Include key studies to reference and sensitivity levels. Balance behavioral psychology with practical self-improvement."},

    # Research
    {"agent_id": "trend-researcher", "name": "Daily Trend Briefing", "cron": "30 6 * * *", "category": "analytics",
     "prompt": "Produce today's trend briefing. Scan all platforms for emerging and rising trends relevant to our 3 channels. Use your TREND ALERT format for anything scoring above 30/60. Include lifecycle stage assessment."},
    {"agent_id": "senior-researcher", "name": "Weekly Research Roundup", "cron": "0 8 * * 1", "category": "analytics",
     "prompt": "Compile a weekly research roundup of the most important new studies, reports, and data across AI, finance, and psychology. Identify the top 5 findings that could become video content."},

    # SEO
    {"agent_id": "seo-specialist", "name": "Weekly SEO Audit", "cron": "0 8 * * 3", "category": "analytics",
     "prompt": "Run a weekly SEO audit across all channels. Check keyword rankings, identify new keyword opportunities, review recent video metadata quality, and recommend optimizations for underperforming content."},

    # Data Analyst
    {"agent_id": "data-analyst", "name": "Daily Performance Snapshot", "cron": "0 6 * * *", "category": "analytics",
     "prompt": "Pull yesterday's performance snapshot. Key metrics per channel: views, watch time, CTR, new subs, RPM. Flag any anomalies. Deliver in your DATA REPORT format."},

    # Scriptwriter
    {"agent_id": "scriptwriter", "name": "Script Queue Check", "cron": "0 8 * * *", "category": "content",
     "prompt": "Check the content pipeline for any approved topics that need scripts. If there are topics in RESEARCHED or TITLED status, begin drafting the highest-priority script using your SCRIPT format."},

    # Newsletter
    {"agent_id": "newsletter-strategist", "name": "Weekly Newsletter Draft", "cron": "0 10 * * 4", "category": "monetization",
     "prompt": "Draft this week's newsletter. Pull the best insights from our recent videos, add an exclusive tip, tease upcoming content, include one curated resource, and one product/affiliate mention. Deliver in your NEWSLETTER PLAN format with 3 subject line options."},
    {"agent_id": "newsletter-strategist", "name": "Monthly List Growth Report", "cron": "0 9 1 * *", "category": "monetization",
     "prompt": "Produce the monthly email list growth report. Analyze subscriber growth, open rates, click rates, and unsubscribe trends. Identify top-performing lead magnets and recommend next month's growth tactics."},

    # QA
    {"agent_id": "quality-assurance-lead", "name": "Daily QA Queue Check", "cron": "0 9 * * *", "category": "operations",
     "prompt": "Check the production pipeline for any content in READY status awaiting QA review. Run through your QA checklist for each item and report findings using your QA REVIEW format."},

    # Project Manager
    {"agent_id": "project-manager", "name": "Daily Standup Report", "cron": "0 8 * * 1-5", "category": "operations",
     "prompt": "Produce the daily standup report. Track all active projects, check for overdue tasks, update status on each pipeline item, and flag blockers. Use your PROJECT STATUS format."},

    # Secretary
    {"agent_id": "secretary-agent", "name": "Daily Morning Brief", "cron": "0 7 * * *", "category": "executive",
     "prompt": "Compile the daily morning briefing for Pedro. Include: what's publishing today, key deadlines, any overnight performance highlights, and today's priorities. Use your DAILY BRIEF format."},
    {"agent_id": "secretary-agent", "name": "Weekly Summary Report", "cron": "0 16 * * 5", "category": "executive",
     "prompt": "Compile the weekly summary report. Summarize what was accomplished this week across all departments, what's pending, key decisions made, and priorities for next week. This is Pedro's end-of-week review."},

    # Compliance
    {"agent_id": "compliance-officer", "name": "Weekly Compliance Audit", "cron": "0 10 * * 3", "category": "executive",
     "prompt": "Run the weekly compliance audit across all channels. Check recent videos for FTC disclosure compliance, financial disclaimers, copyright issues, and community guideline adherence. Flag any issues."},

    # Voice Director
    {"agent_id": "voice-director", "name": "Weekly Voice Quality Review", "cron": "0 10 * * 4", "category": "content",
     "prompt": "Review recent voiceover outputs for quality. Assess pacing, naturalness, and audience engagement. Recommend ElevenLabs settings adjustments. Propose voice direction improvements for upcoming scripts."},

    # Automation Engineer
    {"agent_id": "automation-engineer", "name": "Weekly Automation Health Check", "cron": "0 10 * * 5", "category": "operations",
     "prompt": "Run a health check on all Make.com automation scenarios. Verify each pipeline is functioning, check for failed executions, identify new automation opportunities, and report on API cost efficiency."},

    # Reflection Council
    {"agent_id": "reflection-council", "name": "Weekly Retrospective", "cron": "0 15 * * 5", "category": "executive",
     "prompt": "Conduct the weekly content retrospective. Analyze what worked and didn't this week. Challenge our assumptions. Identify blind spots. Play devil's advocate on our current strategy. Use your REFLECTION REPORT format."},

    # Affiliate
    {"agent_id": "affiliate-coordinator", "name": "Weekly Affiliate Report", "cron": "0 9 * * 2", "category": "monetization",
     "prompt": "Produce the weekly affiliate performance report. Track clicks, conversions, revenue per program, and top-performing videos for affiliate income. Identify new programs to join and links to update."},

    # Partnership Manager
    {"agent_id": "partnership-manager", "name": "Weekly Outreach Pipeline", "cron": "0 10 * * 1", "category": "monetization",
     "prompt": "Review the brand partnership pipeline. Identify 3 new potential brand partners aligned with our channels. Draft outreach proposals and update status on existing partnerships."},

    # Community Manager
    {"agent_id": "community-manager", "name": "Daily Community Pulse", "cron": "0 8 * * *", "category": "monetization",
     "prompt": "Produce the daily community pulse report. Summarize audience sentiment from recent comments, community posts, and social mentions. Identify top themes, content ideas from the community, and any issues requiring attention."},

    # Social Media
    {"agent_id": "social-media-manager", "name": "Daily Social Calendar", "cron": "0 7 * * *", "category": "content",
     "prompt": "Plan today's social media posts across all platforms. Align with today's publishing schedule and any trending topics. Specify platform, content type, copy, and posting time for each post."},

    # Shorts
    {"agent_id": "shorts-and-clips-agent", "name": "Daily Clips Review", "cron": "0 11 * * *", "category": "content",
     "prompt": "Review recently published long-form videos for clip extraction opportunities. Identify the top 3 moments from each new video that would make strong Shorts/Reels/TikToks. Use your SHORTS PLAN format."},

    # Thumbnail
    {"agent_id": "thumbnail-designer", "name": "Thumbnail Queue Check", "cron": "0 9 * * *", "category": "operations",
     "prompt": "Check the pipeline for videos in PRODUCTION or READY status that need thumbnails. Create thumbnail briefs for each using your THUMBNAIL BRIEF format with 3 options per video."},

    # Digital Products
    {"agent_id": "digital-product-manager", "name": "Monthly Product Review", "cron": "0 11 1 * *", "category": "monetization",
     "prompt": "Conduct the monthly digital product review. Analyze product sales, customer feedback, and market demand. Recommend next product to develop and improvements to existing products."},
]


async def init_scheduled_tasks():
    """Create default scheduled tasks if they don't exist."""
    async with async_session() as db:
        result = await db.execute(select(ScheduledTask))
        existing = {t.name for t in result.scalars().all()}

        for task_def in DEFAULT_TASKS:
            if task_def["name"] not in existing:
                task = ScheduledTask(
                    id=str(uuid.uuid4()),
                    agent_id=task_def["agent_id"],
                    name=task_def["name"],
                    description=task_def.get("description", ""),
                    prompt=task_def["prompt"],
                    cron_expression=task_def["cron"],
                    category=task_def.get("category", "general"),
                    enabled=True,
                )
                db.add(task)

        await db.commit()
        total = (await db.execute(select(ScheduledTask))).scalars().all()
        print(f"[SCHEDULER] {len(total)} scheduled tasks ready")


def parse_cron_expression(cron_expr: str) -> dict:
    """Parse '0 9 * * 1' into APScheduler CronTrigger kwargs."""
    parts = cron_expr.strip().split()
    if len(parts) != 5:
        return None
    return {
        "minute": parts[0],
        "hour": parts[1],
        "day": parts[2],
        "month": parts[3],
        "day_of_week": parts[4],
    }


async def start_scheduler():
    """Load all enabled tasks from DB and register them as cron jobs."""
    async with async_session() as db:
        result = await db.execute(select(ScheduledTask).where(ScheduledTask.enabled == True))
        tasks = result.scalars().all()

        for task in tasks:
            cron_kwargs = parse_cron_expression(task.cron_expression)
            if not cron_kwargs:
                print(f"[SCHEDULER] Skipping '{task.name}' — bad cron: {task.cron_expression}")
                continue

            scheduler.add_job(
                run_scheduled_task,
                CronTrigger(**cron_kwargs),
                args=[task.id],
                id=f"task_{task.id}",
                name=task.name,
                replace_existing=True,
                misfire_grace_time=300,
            )

        scheduler.start()
        jobs = scheduler.get_jobs()
        print(f"[SCHEDULER] Started with {len(jobs)} cron jobs running")

        # Print next 5 fires
        for job in jobs[:5]:
            print(f"  -> {job.name}: next fire at {job.next_run_time}")


def stop_scheduler():
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[SCHEDULER] Stopped")


async def get_active_runs(db) -> list:
    """Get currently running and recent task runs."""
    result = await db.execute(
        select(TaskRun).order_by(TaskRun.started_at.desc()).limit(50)
    )
    return list(result.scalars().all())


async def get_pending_escalations(db) -> list:
    """Get pending escalations for Pedro."""
    result = await db.execute(
        select(Escalation).where(Escalation.status == "pending").order_by(Escalation.created_at.desc())
    )
    return list(result.scalars().all())
