from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from app.database import Base


class SocialAccount(Base):
    """A social media account managed by the empire."""
    __tablename__ = "social_accounts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String, nullable=False)  # youtube, instagram, snapchat, tiktok, twitter, linkedin, threads
    account_name = Column(String, nullable=False)  # @handle or channel name
    display_name = Column(String, default="")
    channel_brand = Column(String, default="")  # "V-Real AI", "Cash Flow Code", "Mind Shift", "Empire Main"
    managed_by = Column(String, default="social-media-manager-agent")  # Primary agent responsible
    status = Column(String, default="active")  # active, planned, pending_creation, paused
    followers = Column(String, default="0")
    url = Column(String, default="")
    make_webhook = Column(String, default="")  # Make.com webhook for posting to this account
    credentials_note = Column(String, default="")  # NOT the actual password — just notes like "in password manager"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    extra_data = Column(JSON, default=dict)  # Platform-specific data


class SocialPost(Base):
    """A post created by an agent for a social media account."""
    __tablename__ = "social_posts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String, nullable=False)  # Links to SocialAccount
    agent_id = Column(String, nullable=False)  # Who created it
    platform = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    post_type = Column(String, default="post")  # post, reel, short, story, thread, carousel
    media_notes = Column(Text, default="")  # Description of media to attach
    hashtags = Column(Text, default="")
    scheduled_for = Column(String, default="")  # When to post
    status = Column(String, default="draft")  # draft, scheduled, posted, failed
    make_execution_id = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    posted_at = Column(DateTime, nullable=True)


class AccountProposal(Base):
    """Agent proposes a new account/channel — needs Pedro's approval to create."""
    __tablename__ = "account_proposals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    proposed_name = Column(String, nullable=False)
    channel_brand = Column(String, default="")
    rationale = Column(Text, nullable=False)  # Why we need this account
    content_strategy = Column(Text, default="")  # What we'll post
    growth_target = Column(String, default="")  # e.g. "10K followers in 90 days"
    status = Column(String, default="pending")  # pending, approved, rejected, created
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    reviewed_at = Column(DateTime, nullable=True)


# Platform configurations
PLATFORMS = {
    "youtube": {"name": "YouTube", "emoji": "📺", "post_types": ["video", "short", "community_post", "live"], "max_post_length": 5000},
    "instagram": {"name": "Instagram", "emoji": "📸", "post_types": ["post", "reel", "story", "carousel"], "max_post_length": 2200},
    "snapchat": {"name": "Snapchat", "emoji": "👻", "post_types": ["snap", "story", "spotlight"], "max_post_length": 250},
    "tiktok": {"name": "TikTok", "emoji": "📱", "post_types": ["video", "photo", "live"], "max_post_length": 4000},
    "twitter": {"name": "X (Twitter)", "emoji": "𝕏", "post_types": ["tweet", "thread", "space"], "max_post_length": 280},
    "linkedin": {"name": "LinkedIn", "emoji": "💼", "post_types": ["post", "article", "newsletter"], "max_post_length": 3000},
    "threads": {"name": "Threads", "emoji": "🧵", "post_types": ["post", "reply"], "max_post_length": 500},
    "facebook": {"name": "Facebook", "emoji": "📘", "post_types": ["post", "reel", "story", "live", "group_post"], "max_post_length": 63206},
}

# Which agents manage which platform focus
PLATFORM_AGENTS = {
    "youtube": ["social-media-manager-agent", "shorts-and-clips-agent", "video-editor-agent"],
    "instagram": ["social-media-manager-agent", "thumbnail-designer-agent"],
    "snapchat": ["social-media-manager-agent", "shorts-and-clips-agent"],
    "tiktok": ["social-media-manager-agent", "shorts-and-clips-agent"],
    "twitter": ["social-media-manager-agent", "community-manager-agent"],
    "linkedin": ["social-media-manager-agent", "newsletter-strategist-agent"],
    "threads": ["social-media-manager-agent", "community-manager-agent"],
    "facebook": ["social-media-manager-agent", "community-manager-agent", "newsletter-strategist-agent"],
}
