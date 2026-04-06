"""
Post-Publish Monitoring Service

Watches video performance after upload and automates the feedback loop:
  - Tracks views, retention, CTR, engagement in real-time
  - Monitors comments (flags questions, negative feedback, spam)
  - Generates 24h and 48h performance reports
  - Feeds insights back to agents (Reflection Council, Data Analyst, Content VP)
  - Alerts Pedro if metrics are significantly above or below expectations
  - Manages community engagement (comment replies, hearts, pins)

This is the "closed loop" that makes every episode better than the last.
"""
from __future__ import annotations

import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from app.services.youtube_uploader import (
    get_video_performance,
    get_video_comments,
    reply_to_comment,
    VideoPerformance,
)


# ── Configuration ────────────────────────────────────────────────────────────

REPORTS_DIR = os.getenv("REPORTS_DIR", os.path.expanduser("~/youtube-empire/reports"))
DEBRIEF_DIR = os.path.join(REPORTS_DIR, "debriefs")

# Check intervals
CHECK_INTERVALS = {
    "first_hour": 60 * 15,       # Every 15 min for first hour
    "hours_1_to_6": 60 * 30,     # Every 30 min for hours 1-6
    "hours_6_to_24": 60 * 60,    # Every hour for hours 6-24
    "hours_24_to_48": 60 * 120,  # Every 2 hours for hours 24-48
}

# Performance benchmarks (adjust as channel grows)
BENCHMARKS = {
    "new_channel": {  # First 10 episodes
        "views_1h": 50,
        "views_24h": 300,
        "views_48h": 500,
        "ctr_target": 0.04,        # 4% CTR
        "like_ratio": 0.05,        # 5% of viewers like
        "comment_ratio": 0.01,     # 1% of viewers comment
        "avg_view_duration_pct": 0.50,  # 50% average view duration
        "subscriber_conversion": 0.02,   # 2% of viewers subscribe
    },
    "growing": {  # Episodes 11-50
        "views_1h": 200,
        "views_24h": 1000,
        "views_48h": 2000,
        "ctr_target": 0.06,
        "like_ratio": 0.05,
        "comment_ratio": 0.015,
        "avg_view_duration_pct": 0.50,
        "subscriber_conversion": 0.03,
    },
    "established": {  # Episodes 50+
        "views_1h": 1000,
        "views_24h": 5000,
        "views_48h": 10000,
        "ctr_target": 0.08,
        "like_ratio": 0.06,
        "comment_ratio": 0.02,
        "avg_view_duration_pct": 0.55,
        "subscriber_conversion": 0.04,
    },
}

# Comment classification keywords
COMMENT_SIGNALS = {
    "question": ["?", "how do", "what is", "can you", "where", "when", "which", "explain"],
    "positive": ["amazing", "great", "love", "awesome", "incredible", "subscribed", "best", "thank"],
    "negative": ["boring", "bad", "hate", "waste", "clickbait", "dislike", "unsubscribe", "terrible"],
    "suggestion": ["you should", "next video", "can you cover", "would love to see", "please make"],
    "spam": ["check out my", "subscribe to my", "free money", "click my", "giveaway", "www.", "http"],
}


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class MonitoredVideo:
    """A video being actively monitored post-publish."""
    video_id: str
    title: str
    episode_id: str
    published_at: str
    stage: str = "new_channel"        # benchmark tier
    checks: list[dict] = field(default_factory=list)
    comments_processed: list[str] = field(default_factory=list)  # comment IDs already handled
    alerts_sent: list[dict] = field(default_factory=list)
    debrief_generated: bool = False


@dataclass
class PerformanceSnapshot:
    """Single point-in-time performance measurement."""
    timestamp: str
    hours_since_publish: float
    views: int
    likes: int
    comments: int
    views_velocity: float = 0.0       # views per hour since last check
    engagement_rate: float = 0.0      # (likes + comments) / views
    on_track: bool = True             # vs benchmark
    notes: list[str] = field(default_factory=list)


@dataclass
class CommentAnalysis:
    """Analyzed comment with classification and recommended action."""
    comment_id: str
    author: str
    text: str
    category: str           # "question", "positive", "negative", "suggestion", "spam", "neutral"
    sentiment_score: float  # -1 to 1
    action: str             # "reply", "heart", "pin", "ignore", "flag"
    suggested_reply: str = ""
    priority: int = 0       # 0=low, 1=medium, 2=high


@dataclass
class DebriefReport:
    """Complete post-publish debrief for agent system consumption."""
    video_id: str
    episode_id: str
    title: str
    published_at: str
    report_type: str              # "24h" or "48h"
    generated_at: str = ""

    # Metrics
    total_views: int = 0
    total_likes: int = 0
    total_comments: int = 0
    like_ratio: float = 0.0
    comment_ratio: float = 0.0
    views_velocity_trend: str = ""  # "accelerating", "steady", "decelerating"

    # Benchmarks
    vs_benchmark: dict = field(default_factory=dict)  # metric -> "above"/"below"/"on_track"

    # Comment insights
    top_questions: list[str] = field(default_factory=list)
    top_suggestions: list[str] = field(default_factory=list)
    sentiment_breakdown: dict = field(default_factory=dict)

    # Actionable insights for agents
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    # Next episode implications
    content_signals: list[str] = field(default_factory=list)


# ── Comment Analysis ─────────────────────────────────────────────────────────

def classify_comment(comment: dict) -> CommentAnalysis:
    """
    Classify a YouTube comment and recommend an action.
    Used by Community Manager agent for engagement.
    """
    text = comment.get("text", "").lower()
    author = comment.get("author", "")
    comment_id = comment.get("comment_id", "")

    # Classify
    category = "neutral"
    sentiment = 0.0

    for cat, keywords in COMMENT_SIGNALS.items():
        matches = sum(1 for kw in keywords if kw.lower() in text)
        if matches > 0:
            category = cat
            break

    # Sentiment scoring
    positive_words = sum(1 for kw in COMMENT_SIGNALS["positive"] if kw in text)
    negative_words = sum(1 for kw in COMMENT_SIGNALS["negative"] if kw in text)
    sentiment = (positive_words - negative_words) / max(positive_words + negative_words, 1)

    # Determine action
    action = "ignore"
    priority = 0
    suggested_reply = ""

    if category == "question":
        action = "reply"
        priority = 2
        suggested_reply = _generate_reply_suggestion(text, "question")
    elif category == "positive":
        action = "heart"
        priority = 0
        if comment.get("likes", 0) > 5:
            action = "pin"
            priority = 1
    elif category == "negative":
        action = "flag"
        priority = 2
        suggested_reply = _generate_reply_suggestion(text, "negative")
    elif category == "suggestion":
        action = "reply"
        priority = 1
        suggested_reply = _generate_reply_suggestion(text, "suggestion")
    elif category == "spam":
        action = "flag"
        priority = 0

    return CommentAnalysis(
        comment_id=comment_id,
        author=author,
        text=comment.get("text", ""),
        category=category,
        sentiment_score=sentiment,
        action=action,
        suggested_reply=suggested_reply,
        priority=priority,
    )


def _generate_reply_suggestion(text: str, category: str) -> str:
    """Generate a suggested reply based on comment type. Community Manager reviews before posting."""
    templates = {
        "question": "Great question! [AGENT: Draft a specific answer based on the episode content and this comment]",
        "negative": "[AGENT: Review this feedback. If constructive, acknowledge and explain. If trolling, ignore.]",
        "suggestion": "Thanks for the suggestion! We're always looking for great topics to cover. [AGENT: Evaluate if this aligns with content calendar]",
    }
    return templates.get(category, "")


# ── Performance Monitoring ───────────────────────────────────────────────────

async def check_video_performance(video: MonitoredVideo) -> PerformanceSnapshot:
    """
    Take a performance snapshot and compare against benchmarks.
    """
    perf = get_video_performance(video.video_id)
    now = datetime.now(timezone.utc)
    published = datetime.fromisoformat(video.published_at.replace("Z", "+00:00"))
    hours_since = (now - published).total_seconds() / 3600

    # Calculate velocity
    views_velocity = 0.0
    if video.checks:
        last_check = video.checks[-1]
        time_diff = hours_since - last_check.get("hours_since_publish", 0)
        if time_diff > 0:
            views_velocity = (perf.views - last_check.get("views", 0)) / time_diff

    # Compare to benchmarks
    benchmarks = BENCHMARKS.get(video.stage, BENCHMARKS["new_channel"])
    notes = []
    on_track = True

    if hours_since <= 1 and perf.views < benchmarks["views_1h"] * 0.5:
        notes.append(f"Views below target: {perf.views} vs {benchmarks['views_1h']} expected at 1h")
        on_track = False
    elif hours_since <= 24 and perf.views < benchmarks["views_24h"] * 0.5:
        notes.append(f"Views below target: {perf.views} vs {benchmarks['views_24h']} expected at 24h")
        on_track = False

    like_ratio = perf.likes / max(perf.views, 1)
    if perf.views > 50 and like_ratio < benchmarks["like_ratio"] * 0.5:
        notes.append(f"Like ratio low: {like_ratio:.1%} vs {benchmarks['like_ratio']:.1%} target")

    # Positive signals
    if perf.views > 50 and like_ratio > benchmarks["like_ratio"]:
        notes.append(f"Strong engagement: {like_ratio:.1%} like ratio")

    if views_velocity > (benchmarks["views_24h"] / 24) * 1.5:
        notes.append(f"Views accelerating: {views_velocity:.0f}/hour")

    engagement_rate = (perf.likes + perf.comments) / max(perf.views, 1)

    snapshot = PerformanceSnapshot(
        timestamp=now.isoformat(),
        hours_since_publish=round(hours_since, 2),
        views=perf.views,
        likes=perf.likes,
        comments=perf.comments,
        views_velocity=round(views_velocity, 1),
        engagement_rate=round(engagement_rate, 4),
        on_track=on_track,
        notes=notes,
    )

    # Store check
    video.checks.append({
        "timestamp": snapshot.timestamp,
        "hours_since_publish": snapshot.hours_since_publish,
        "views": snapshot.views,
        "likes": snapshot.likes,
        "comments": snapshot.comments,
        "velocity": snapshot.views_velocity,
        "on_track": snapshot.on_track,
    })

    return snapshot


async def monitor_comments(video: MonitoredVideo, max_results: int = 50) -> list[CommentAnalysis]:
    """
    Fetch and analyze new comments on a video.
    Returns only comments that haven't been processed yet.
    """
    raw_comments = get_video_comments(video.video_id, max_results=max_results)

    new_analyses = []
    for comment in raw_comments:
        if comment["comment_id"] in video.comments_processed:
            continue

        analysis = classify_comment(comment)
        new_analyses.append(analysis)
        video.comments_processed.append(comment["comment_id"])

    # Sort by priority (high first)
    new_analyses.sort(key=lambda a: a.priority, reverse=True)

    if new_analyses:
        print(f"[MONITOR] {len(new_analyses)} new comments on '{video.title}'")
        questions = [a for a in new_analyses if a.category == "question"]
        if questions:
            print(f"[MONITOR]   {len(questions)} questions need replies")

    return new_analyses


# ── Debrief Generation ───────────────────────────────────────────────────────

async def generate_debrief(video: MonitoredVideo, report_type: str = "48h") -> DebriefReport:
    """
    Generate a comprehensive post-publish debrief.

    This report gets consumed by:
    - Data Analyst → updates performance baselines
    - Reflection Council → identifies patterns and learnings
    - Content VP → adjusts content strategy
    - CEO Agent → reviews channel health
    """
    os.makedirs(DEBRIEF_DIR, exist_ok=True)

    perf = get_video_performance(video.video_id)
    benchmarks = BENCHMARKS.get(video.stage, BENCHMARKS["new_channel"])

    # Analyze view velocity trend
    velocity_trend = "steady"
    if len(video.checks) >= 3:
        recent_velocities = [c.get("velocity", 0) for c in video.checks[-3:]]
        if recent_velocities[-1] > recent_velocities[0] * 1.2:
            velocity_trend = "accelerating"
        elif recent_velocities[-1] < recent_velocities[0] * 0.8:
            velocity_trend = "decelerating"

    # Benchmark comparison
    target_key = f"views_{report_type.replace('h', '')}h" if report_type in ["24h", "48h"] else "views_48h"
    views_target = benchmarks.get(target_key, benchmarks["views_48h"])

    vs_benchmark = {
        "views": "above" if perf.views >= views_target else ("on_track" if perf.views >= views_target * 0.7 else "below"),
        "engagement": "above" if (perf.likes / max(perf.views, 1)) >= benchmarks["like_ratio"] else "below",
        "comments": "above" if (perf.comments / max(perf.views, 1)) >= benchmarks["comment_ratio"] else "below",
    }

    # Comment analysis
    all_comments = get_video_comments(video.video_id, max_results=100)
    comment_analyses = [classify_comment(c) for c in all_comments]

    sentiment_breakdown = {
        "positive": len([a for a in comment_analyses if a.category == "positive"]),
        "neutral": len([a for a in comment_analyses if a.category == "neutral"]),
        "negative": len([a for a in comment_analyses if a.category == "negative"]),
        "questions": len([a for a in comment_analyses if a.category == "question"]),
        "suggestions": len([a for a in comment_analyses if a.category == "suggestion"]),
    }

    top_questions = [a.text for a in comment_analyses if a.category == "question"][:5]
    top_suggestions = [a.text for a in comment_analyses if a.category == "suggestion"][:5]

    # Generate insights
    insights = []
    recommendations = []
    content_signals = []

    if vs_benchmark["views"] == "above":
        insights.append(f"Views exceeded {report_type} target ({perf.views} vs {views_target})")
    elif vs_benchmark["views"] == "below":
        insights.append(f"Views below {report_type} target ({perf.views} vs {views_target})")
        recommendations.append("Review title/thumbnail for CTR optimization")

    if velocity_trend == "accelerating":
        insights.append("View velocity is accelerating — algorithm may be picking up the video")
    elif velocity_trend == "decelerating":
        insights.append("View velocity is slowing — video may have saturated initial audience")
        recommendations.append("Consider promoting on social media to extend reach")

    if vs_benchmark["engagement"] == "above":
        insights.append("Strong engagement signals — audience resonating with content")
    elif vs_benchmark["engagement"] == "below":
        recommendations.append("Engagement below target — review content quality and hook effectiveness")

    if top_questions:
        content_signals.append(f"Audience asking about: {', '.join(q[:50] for q in top_questions[:3])}")
        recommendations.append("Consider addressing top viewer questions in next episode or community post")

    if top_suggestions:
        content_signals.append(f"Audience wants: {', '.join(s[:50] for s in top_suggestions[:3])}")

    # Build debrief
    debrief = DebriefReport(
        video_id=video.video_id,
        episode_id=video.episode_id,
        title=video.title,
        published_at=video.published_at,
        report_type=report_type,
        generated_at=datetime.now(timezone.utc).isoformat(),
        total_views=perf.views,
        total_likes=perf.likes,
        total_comments=perf.comments,
        like_ratio=round(perf.likes / max(perf.views, 1), 4),
        comment_ratio=round(perf.comments / max(perf.views, 1), 4),
        views_velocity_trend=velocity_trend,
        vs_benchmark=vs_benchmark,
        top_questions=top_questions,
        top_suggestions=top_suggestions,
        sentiment_breakdown=sentiment_breakdown,
        insights=insights,
        recommendations=recommendations,
        content_signals=content_signals,
    )

    # Save report
    report_path = os.path.join(DEBRIEF_DIR, f"{video.episode_id}-debrief-{report_type}.json")
    with open(report_path, "w") as f:
        json.dump(debrief.__dict__, f, indent=2)
    print(f"[MONITOR] ✓ {report_type} debrief saved: {report_path}")

    video.debrief_generated = True
    return debrief


# ── Monitoring Loop ──────────────────────────────────────────────────────────

async def run_monitoring_cycle(video: MonitoredVideo) -> dict:
    """
    Run a single monitoring cycle: check performance + process comments.
    Called by the scheduler at appropriate intervals.
    """
    # Performance check
    snapshot = await check_video_performance(video)

    # Comment monitoring
    new_comments = await monitor_comments(video)

    # Check if alerts needed
    alerts = []
    if not snapshot.on_track:
        alerts.append({
            "type": "performance_below_target",
            "message": "; ".join(snapshot.notes),
            "severity": "warning",
        })

    high_priority_comments = [c for c in new_comments if c.priority >= 2]
    if high_priority_comments:
        alerts.append({
            "type": "comments_need_attention",
            "message": f"{len(high_priority_comments)} comments need response",
            "comments": [{"author": c.author, "text": c.text[:100], "category": c.category} for c in high_priority_comments],
            "severity": "info",
        })

    # Check if debrief is due
    published = datetime.fromisoformat(video.published_at.replace("Z", "+00:00"))
    hours_since = (datetime.now(timezone.utc) - published).total_seconds() / 3600

    debrief = None
    if hours_since >= 48 and not video.debrief_generated:
        debrief = await generate_debrief(video, "48h")
    elif hours_since >= 24 and len(video.checks) > 0 and not any(
        c.get("hours_since_publish", 0) >= 24 for c in video.checks[:-1]
    ):
        debrief = await generate_debrief(video, "24h")

    return {
        "snapshot": snapshot.__dict__,
        "new_comments": len(new_comments),
        "actionable_comments": [c.__dict__ for c in high_priority_comments],
        "alerts": alerts,
        "debrief": debrief.__dict__ if debrief else None,
    }
