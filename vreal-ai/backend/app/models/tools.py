from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean
from app.database import Base


class AITool(Base):
    """Registry of all AI tools and services the empire uses."""
    __tablename__ = "ai_tools"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # voice, video, image, text, analytics, publishing, automation
    description = Column(Text, default="")
    website = Column(String, default="")
    api_key_env = Column(String, default="")  # Environment variable name for API key
    make_scenario_id = Column(String, default="")  # Make.com scenario ID
    make_webhook = Column(String, default="")  # Make.com webhook URL
    status = Column(String, default="pending_setup")  # active, pending_setup, disabled
    managed_by = Column(String, default="")  # Which agent primarily uses this
    icon = Column(String, default="")  # Emoji icon
    config = Column(JSON, default=dict)  # Tool-specific configuration


# All AI tools and services organized by category
DEFAULT_TOOLS = [
    # === VOICE GENERATION ===
    {"name": "ElevenLabs", "category": "voice", "icon": "🎙️",
     "description": "AI voice cloning and text-to-speech. Creates natural voiceovers for videos.",
     "website": "https://elevenlabs.io", "api_key_env": "ELEVENLABS_API_KEY",
     "managed_by": "video-editor-agent",
     "config": {"voices": ["narrator", "energetic", "calm"], "output": "mp3", "models": ["eleven_multilingual_v2"]}},

    {"name": "Play.ht", "category": "voice", "icon": "🔊",
     "description": "Ultra-realistic AI voices. Good for long-form narration.",
     "website": "https://play.ht", "api_key_env": "PLAYHT_API_KEY",
     "managed_by": "video-editor-agent",
     "config": {"use_case": "backup_voice_provider"}},

    # === VIDEO GENERATION & EDITING ===
    {"name": "InVideo AI", "category": "video", "icon": "🎬",
     "description": "AI video editor — combines voiceover, stock footage, captions, and music automatically.",
     "website": "https://invideo.io", "api_key_env": "INVIDEO_API_KEY",
     "managed_by": "video-editor-agent",
     "config": {"templates": ["youtube_long", "youtube_short", "instagram_reel"]}},

    {"name": "Lumen5", "category": "video", "icon": "💡",
     "description": "Turn blog posts and scripts into videos with AI. Great for repurposing content.",
     "website": "https://lumen5.com", "api_key_env": "LUMEN5_API_KEY",
     "managed_by": "video-editor-agent",
     "config": {"use_case": "script_to_video", "styles": ["corporate", "casual", "bold"]}},

    {"name": "D-ID", "category": "video", "icon": "🧑‍💻",
     "description": "AI avatar video generator. Creates talking head videos from text.",
     "website": "https://d-id.com", "api_key_env": "DID_API_KEY",
     "managed_by": "video-editor-agent",
     "config": {"use_case": "talking_head_avatar", "avatars": ["presenter_male", "presenter_female"]}},

    {"name": "Pictory", "category": "video", "icon": "🎞️",
     "description": "Auto-create short highlight videos from long content. Great for clips and Shorts.",
     "website": "https://pictory.ai", "api_key_env": "PICTORY_API_KEY",
     "managed_by": "shorts-and-clips-agent",
     "config": {"use_case": "long_to_short_clips"}},

    {"name": "CapCut", "category": "video", "icon": "✂️",
     "description": "AI-powered video editing with auto-captions, transitions, and effects.",
     "website": "https://capcut.com", "api_key_env": "",
     "managed_by": "shorts-and-clips-agent",
     "config": {"use_case": "shorts_editing", "auto_captions": True}},

    # === IMAGE & THUMBNAIL GENERATION ===
    {"name": "Midjourney", "category": "image", "icon": "🎨",
     "description": "AI image generation for thumbnails, channel art, and social media visuals.",
     "website": "https://midjourney.com", "api_key_env": "MIDJOURNEY_API_KEY",
     "managed_by": "thumbnail-designer-agent",
     "config": {"styles": ["photorealistic", "illustration", "3d_render"], "aspect_ratios": ["16:9", "1:1", "9:16"]}},

    {"name": "DALL-E 3", "category": "image", "icon": "🖼️",
     "description": "OpenAI image generation. Precise prompt following for thumbnails.",
     "website": "https://openai.com", "api_key_env": "OPENAI_API_KEY",
     "managed_by": "thumbnail-designer-agent",
     "config": {"use_case": "thumbnail_generation", "size": "1792x1024"}},

    {"name": "Canva", "category": "image", "icon": "🎯",
     "description": "Design platform for thumbnails, social posts, and brand assets.",
     "website": "https://canva.com", "api_key_env": "CANVA_API_KEY",
     "managed_by": "thumbnail-designer-agent",
     "config": {"templates": ["youtube_thumbnail", "instagram_post", "facebook_cover"]}},

    {"name": "Leonardo AI", "category": "image", "icon": "🦁",
     "description": "AI image generation with fine-tuned models. Good for consistent brand visuals.",
     "website": "https://leonardo.ai", "api_key_env": "LEONARDO_API_KEY",
     "managed_by": "thumbnail-designer-agent",
     "config": {"use_case": "brand_consistent_images"}},

    # === TEXT & CONTENT ===
    {"name": "Claude (Anthropic)", "category": "text", "icon": "🧠",
     "description": "Powers all 32 agents. Script writing, research, analysis, strategy.",
     "website": "https://console.anthropic.com", "api_key_env": "ANTHROPIC_API_KEY",
     "managed_by": "ceo-agent", "status": "active",
     "config": {"model": "claude-sonnet-4-20250514", "max_tokens": 4096}},

    {"name": "Perplexity", "category": "text", "icon": "🔍",
     "description": "AI search engine for real-time research and fact-checking.",
     "website": "https://perplexity.ai", "api_key_env": "PERPLEXITY_API_KEY",
     "managed_by": "senior-researcher-agent",
     "config": {"use_case": "real_time_research"}},

    # === ANALYTICS ===
    {"name": "TubeBuddy", "category": "analytics", "icon": "📊",
     "description": "YouTube SEO and analytics tool. Keyword research, tag optimization.",
     "website": "https://tubebuddy.com", "api_key_env": "TUBEBUDDY_API_KEY",
     "managed_by": "seo-specialist-agent",
     "config": {"features": ["keyword_explorer", "tag_optimizer", "ab_testing"]}},

    {"name": "VidIQ", "category": "analytics", "icon": "📈",
     "description": "YouTube analytics and optimization. Competitor tracking, trend alerts.",
     "website": "https://vidiq.com", "api_key_env": "VIDIQ_API_KEY",
     "managed_by": "data-analyst-agent",
     "config": {"features": ["daily_ideas", "competitor_tracking", "keyword_tools"]}},

    {"name": "Social Blade", "category": "analytics", "icon": "📉",
     "description": "Social media statistics and analytics tracking across platforms.",
     "website": "https://socialblade.com", "api_key_env": "",
     "managed_by": "data-analyst-agent",
     "config": {"platforms": ["youtube", "instagram", "tiktok", "twitter"]}},

    # === PUBLISHING ===
    {"name": "YouTube Data API", "category": "publishing", "icon": "📺",
     "description": "Upload videos, manage playlists, update metadata via YouTube API.",
     "website": "https://console.cloud.google.com", "api_key_env": "YOUTUBE_API_KEY",
     "managed_by": "workflow-orchestrator-agent",
     "config": {"scopes": ["upload", "metadata", "playlists", "analytics"]}},

    {"name": "Meta Graph API", "category": "publishing", "icon": "📘",
     "description": "Publish to Instagram and Facebook programmatically.",
     "website": "https://developers.facebook.com", "api_key_env": "META_API_KEY",
     "managed_by": "social-media-manager-agent",
     "config": {"platforms": ["instagram", "facebook"]}},

    {"name": "TikTok API", "category": "publishing", "icon": "📱",
     "description": "Upload and manage TikTok content programmatically.",
     "website": "https://developers.tiktok.com", "api_key_env": "TIKTOK_API_KEY",
     "managed_by": "shorts-and-clips-agent",
     "config": {"features": ["video_upload", "analytics"]}},

    # === AUTOMATION ===
    {"name": "Make.com", "category": "automation", "icon": "⚡",
     "description": "Automation platform connecting all tools. Central nervous system of the empire.",
     "website": "https://make.com", "api_key_env": "MAKE_API_KEY", "status": "active",
     "managed_by": "workflow-orchestrator-agent",
     "config": {"team_id": "2078612", "scenarios": [
         "research_pipeline", "script_to_sheets", "voiceover_generation",
         "thumbnail_generation", "video_assembly", "seo_optimization",
         "youtube_upload", "social_distribution", "newsletter_send",
         "analytics_pull", "sheets_update", "notify_pedro"
     ]}},

    # === EMAIL & NEWSLETTER ===
    {"name": "ConvertKit", "category": "email", "icon": "✉️",
     "description": "Email marketing platform for newsletter and automation sequences.",
     "website": "https://convertkit.com", "api_key_env": "CONVERTKIT_API_KEY",
     "managed_by": "newsletter-strategist-agent",
     "config": {"features": ["broadcasts", "sequences", "forms", "segments"]}},

    {"name": "Beehiiv", "category": "email", "icon": "🐝",
     "description": "Newsletter platform with built-in growth tools and monetization.",
     "website": "https://beehiiv.com", "api_key_env": "BEEHIIV_API_KEY",
     "managed_by": "newsletter-strategist-agent",
     "config": {"features": ["newsletter", "website", "ad_network", "referral_program"]}},
]

# Make.com scenario map — what each scenario does and which tools it connects
MAKE_SCENARIOS = {
    "research_pipeline": {
        "name": "Research Pipeline",
        "icon": "🔍",
        "description": "Trend Researcher → Claude analyzes → Google Sheets stores results",
        "tools": ["Claude", "Google Sheets", "Perplexity"],
        "trigger": "Webhook from agents",
        "agent": "trend-researcher-agent",
    },
    "script_to_sheets": {
        "name": "Script to Sheets",
        "icon": "📝",
        "description": "Scriptwriter produces script → stored in Google Sheets → notifies editor",
        "tools": ["Claude", "Google Sheets"],
        "trigger": "Webhook from scriptwriter",
        "agent": "scriptwriter-agent",
    },
    "voiceover_generation": {
        "name": "Voiceover Generation",
        "icon": "🎙️",
        "description": "Script → ElevenLabs generates MP3 → stores in Google Drive → notifies editor",
        "tools": ["ElevenLabs", "Google Drive"],
        "trigger": "Webhook from editor",
        "agent": "video-editor-agent",
    },
    "thumbnail_generation": {
        "name": "Thumbnail Generation",
        "icon": "🎨",
        "description": "Thumbnail brief → Midjourney/DALL-E generates options → stores in Drive",
        "tools": ["Midjourney", "DALL-E 3", "Google Drive"],
        "trigger": "Webhook from designer",
        "agent": "thumbnail-designer-agent",
    },
    "video_assembly": {
        "name": "Video Assembly",
        "icon": "🎬",
        "description": "Voiceover + footage + captions → InVideo/Lumen5 assembles → exports MP4",
        "tools": ["InVideo AI", "Lumen5", "Google Drive"],
        "trigger": "Webhook from editor",
        "agent": "video-editor-agent",
    },
    "seo_optimization": {
        "name": "SEO Optimization",
        "icon": "🔎",
        "description": "SEO package → updates YouTube metadata (title, description, tags, chapters)",
        "tools": ["YouTube Data API", "TubeBuddy"],
        "trigger": "Webhook from SEO agent",
        "agent": "seo-specialist-agent",
    },
    "youtube_upload": {
        "name": "YouTube Upload",
        "icon": "📺",
        "description": "Final video + metadata → uploads to YouTube → schedules publish time",
        "tools": ["YouTube Data API", "Google Drive"],
        "trigger": "Webhook (requires Pedro approval)",
        "agent": "workflow-orchestrator-agent",
    },
    "social_distribution": {
        "name": "Social Distribution",
        "icon": "📣",
        "description": "Video published → auto-post to Instagram, TikTok, Facebook, Twitter, LinkedIn, Threads, Snapchat",
        "tools": ["Meta Graph API", "TikTok API", "Buffer/Hootsuite"],
        "trigger": "YouTube publish event",
        "agent": "social-media-manager-agent",
    },
    "newsletter_send": {
        "name": "Newsletter Send",
        "icon": "✉️",
        "description": "Newsletter draft → ConvertKit/Beehiiv sends to subscriber list",
        "tools": ["ConvertKit", "Beehiiv"],
        "trigger": "Webhook (requires Pedro approval)",
        "agent": "newsletter-strategist-agent",
    },
    "analytics_pull": {
        "name": "Analytics Pull",
        "icon": "📊",
        "description": "Pull YouTube Analytics, social stats → store in Sheets → generate report",
        "tools": ["YouTube Data API", "Social Blade", "Google Sheets"],
        "trigger": "Daily cron",
        "agent": "data-analyst-agent",
    },
    "shorts_pipeline": {
        "name": "Shorts Pipeline",
        "icon": "📱",
        "description": "Long video → Pictory extracts clips → CapCut adds captions → publish to TikTok/Reels/Shorts",
        "tools": ["Pictory", "CapCut", "TikTok API", "Meta Graph API"],
        "trigger": "After long video publishes",
        "agent": "shorts-and-clips-agent",
    },
    "avatar_video": {
        "name": "Avatar Video",
        "icon": "🧑‍💻",
        "description": "Script → D-ID generates talking avatar video → can be used as intro/outro or standalone",
        "tools": ["D-ID", "ElevenLabs"],
        "trigger": "Webhook from editor",
        "agent": "video-editor-agent",
    },
}
