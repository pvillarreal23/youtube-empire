"""
YouTube Upload & Management Service

Automates the entire YouTube upload process:
  - Upload video with metadata (title, description, tags, thumbnail)
  - Schedule publish time
  - Set chapters, end screens, cards
  - Monitor post-publish performance
  - Auto-generate performance reports

Requires YouTube Data API v3 credentials.
Setup: https://console.cloud.google.com → APIs → YouTube Data API v3
"""
from __future__ import annotations

import os
import json
import pickle
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

# Google API imports — lazy loaded to avoid cryptography conflicts on some systems
# These are only needed when actually uploading to YouTube
def _import_google():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    return Request, Credentials, InstalledAppFlow, build, MediaFileUpload


# ── Configuration ────────────────────────────────────────────────────────────

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly",
]

CREDENTIALS_FILE = os.getenv("YOUTUBE_CREDENTIALS", os.path.expanduser("~/youtube-empire/credentials/youtube_oauth.json"))
TOKEN_FILE = os.getenv("YOUTUBE_TOKEN", os.path.expanduser("~/youtube-empire/credentials/youtube_token.pickle"))

# V-Real AI channel defaults
CHANNEL_DEFAULTS = {
    "category_id": "28",          # Science & Technology
    "default_language": "en",
    "privacy_status": "private",  # Always upload as private first
    "license": "youtube",
    "embeddable": True,
    "public_stats_viewable": True,
}

# Kling AI affiliate link for descriptions
KLING_AFFILIATE = {
    "code": "7B4U73LULN88",
    "url": "https://klingai.com/?ref=7B4U73LULN88",
    "text": "Try Kling AI (my affiliate link): https://klingai.com/?ref=7B4U73LULN88",
}


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class VideoMetadata:
    """Complete YouTube video metadata."""
    title: str
    description: str
    tags: list[str] = field(default_factory=list)
    category_id: str = CHANNEL_DEFAULTS["category_id"]
    privacy_status: str = CHANNEL_DEFAULTS["privacy_status"]
    publish_at: Optional[str] = None        # ISO 8601 for scheduled publish
    thumbnail_path: Optional[str] = None
    playlist_id: Optional[str] = None
    default_language: str = "en"
    chapters: list[dict] = field(default_factory=list)  # [{"time": "0:00", "title": "Intro"}, ...]
    made_for_kids: bool = False


@dataclass
class UploadResult:
    """Result of a YouTube upload."""
    video_id: str
    url: str
    status: str
    title: str
    privacy: str
    publish_at: Optional[str] = None


@dataclass
class VideoPerformance:
    """Post-publish performance metrics."""
    video_id: str
    title: str
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    subscribers_gained: int = 0
    average_view_duration: float = 0.0
    average_view_percentage: float = 0.0
    click_through_rate: float = 0.0
    impressions: int = 0
    estimated_revenue: float = 0.0
    top_traffic_sources: list[dict] = field(default_factory=list)
    audience_retention_curve: list[float] = field(default_factory=list)
    fetched_at: str = ""


# ── Authentication ───────────────────────────────────────────────────────────

def get_youtube_service():
    """
    Authenticate and return YouTube API service.
    First run requires browser-based OAuth. After that, token is cached.
    """
    Request, Credentials, InstalledAppFlow, build, MediaFileUpload = _import_google()
    creds = None

    # Load cached token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # Refresh or get new credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"YouTube OAuth credentials not found at {CREDENTIALS_FILE}.\n"
                    "1. Go to https://console.cloud.google.com\n"
                    "2. Enable YouTube Data API v3\n"
                    "3. Create OAuth 2.0 credentials (Desktop app)\n"
                    "4. Download JSON and save to the path above"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Cache the token
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build("youtube", "v3", credentials=creds)


# ── Upload ───────────────────────────────────────────────────────────────────

def build_description(
    description: str,
    chapters: list[dict] = None,
    include_affiliate: bool = True,
) -> str:
    """
    Build full YouTube description with chapters, links, and affiliate.

    Format:
      Hook line
      ---
      Body description
      ---
      Chapters (if provided)
      ---
      Links & affiliate
      ---
      Hashtags
    """
    parts = [description.strip()]

    # Add chapters
    if chapters:
        chapter_lines = "\n".join(f"{c['time']} {c['title']}" for c in chapters)
        parts.append(f"\n\n📑 Chapters:\n{chapter_lines}")

    # Add affiliate links
    if include_affiliate:
        parts.append(f"\n\n🔗 Tools mentioned:\n{KLING_AFFILIATE['text']}")

    # Add channel links
    parts.append(
        "\n\n---\n"
        "🔔 Subscribe for more: @VRealAI\n"
        "No fluff. No theory. Just leverage.\n"
        "\n#AI #AITools #VRealAI #ArtificialIntelligence"
    )

    return "\n".join(parts)


def upload_video(video_path: str, metadata: VideoMetadata) -> UploadResult:
    """
    Upload a video to YouTube with full metadata.

    Always uploads as PRIVATE first for review.
    Call set_video_public() after manual review to publish.
    """
    youtube = get_youtube_service()

    # Build description
    full_description = build_description(
        metadata.description,
        metadata.chapters,
        include_affiliate=True,
    )

    # Video body
    body = {
        "snippet": {
            "title": metadata.title[:100],  # YouTube max title length
            "description": full_description[:5000],  # YouTube max
            "tags": metadata.tags[:500],  # YouTube max tags
            "categoryId": metadata.category_id,
            "defaultLanguage": metadata.default_language,
        },
        "status": {
            "privacyStatus": metadata.privacy_status,
            "madeForKids": metadata.made_for_kids,
            "selfDeclaredMadeForKids": metadata.made_for_kids,
            "license": CHANNEL_DEFAULTS["license"],
            "embeddable": CHANNEL_DEFAULTS["embeddable"],
            "publicStatsViewable": CHANNEL_DEFAULTS["public_stats_viewable"],
        },
    }

    # Scheduled publish
    if metadata.publish_at and metadata.privacy_status == "private":
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = metadata.publish_at

    # Upload
    _, _, _, _, MediaFileUpload = _import_google()
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024,  # 10MB chunks
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    print(f"[UPLOADER] Uploading: {metadata.title}")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[UPLOADER] Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    print(f"[UPLOADER] ✓ Upload complete: https://youtube.com/watch?v={video_id}")

    # Set thumbnail if provided
    if metadata.thumbnail_path and os.path.exists(metadata.thumbnail_path):
        set_thumbnail(video_id, metadata.thumbnail_path)

    # Add to playlist if specified
    if metadata.playlist_id:
        add_to_playlist(video_id, metadata.playlist_id)

    return UploadResult(
        video_id=video_id,
        url=f"https://youtube.com/watch?v={video_id}",
        status="uploaded",
        title=metadata.title,
        privacy=metadata.privacy_status,
        publish_at=metadata.publish_at,
    )


def set_thumbnail(video_id: str, thumbnail_path: str):
    """Upload a custom thumbnail for a video."""
    youtube = get_youtube_service()
    _, _, _, _, MediaFileUpload = _import_google()
    media = MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
    youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
    print(f"[UPLOADER] ✓ Thumbnail set for {video_id}")


def add_to_playlist(video_id: str, playlist_id: str):
    """Add a video to a playlist."""
    youtube = get_youtube_service()
    youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {"kind": "youtube#video", "videoId": video_id},
            }
        },
    ).execute()
    print(f"[UPLOADER] ✓ Added to playlist {playlist_id}")


def set_video_public(video_id: str) -> dict:
    """Make a private video public (after Pedro's review)."""
    youtube = get_youtube_service()
    response = youtube.videos().update(
        part="status",
        body={"id": video_id, "status": {"privacyStatus": "public"}},
    ).execute()
    print(f"[UPLOADER] ✓ Video is now PUBLIC: https://youtube.com/watch?v={video_id}")
    return response


def schedule_video(video_id: str, publish_time: str) -> dict:
    """Schedule a private video to auto-publish at a specific time."""
    youtube = get_youtube_service()
    response = youtube.videos().update(
        part="status",
        body={
            "id": video_id,
            "status": {
                "privacyStatus": "private",
                "publishAt": publish_time,
            },
        },
    ).execute()
    print(f"[UPLOADER] ✓ Scheduled for {publish_time}")
    return response


# ── Post-Publish Analytics ───────────────────────────────────────────────────

def get_video_performance(video_id: str) -> VideoPerformance:
    """
    Fetch performance metrics for a published video.
    Use this for the 48-hour post-publish debrief.
    """
    youtube = get_youtube_service()

    # Get basic stats
    stats = youtube.videos().list(
        part="statistics,snippet",
        id=video_id,
    ).execute()

    if not stats.get("items"):
        raise ValueError(f"Video {video_id} not found")

    item = stats["items"][0]
    snippet = item["snippet"]
    statistics = item["statistics"]

    return VideoPerformance(
        video_id=video_id,
        title=snippet.get("title", ""),
        views=int(statistics.get("viewCount", 0)),
        likes=int(statistics.get("likeCount", 0)),
        comments=int(statistics.get("commentCount", 0)),
        fetched_at=datetime.now(timezone.utc).isoformat(),
    )


def get_video_analytics(video_id: str, days: int = 7) -> dict:
    """
    Fetch detailed YouTube Analytics for a video.
    Requires YouTube Analytics API (separate from Data API).

    Returns retention curve, traffic sources, demographics.
    """
    # YouTube Analytics API requires separate OAuth scope
    # This is a placeholder — full implementation needs youtubeAnalytics.readonly scope
    return {
        "video_id": video_id,
        "note": "Full analytics requires YouTube Analytics API setup. Add scope: https://www.googleapis.com/auth/yt-analytics.readonly",
        "basic_stats": get_video_performance(video_id).__dict__,
    }


def generate_48h_debrief(video_id: str) -> dict:
    """
    Generate the 48-hour post-publish debrief report.

    This feeds back into the agent system:
    - Data Analyst processes the numbers
    - Reflection Council identifies learnings
    - Content VP adjusts strategy
    """
    perf = get_video_performance(video_id)

    debrief = {
        "video_id": video_id,
        "title": perf.title,
        "metrics": {
            "views": perf.views,
            "likes": perf.likes,
            "comments": perf.comments,
            "like_ratio": perf.likes / max(perf.views, 1),
        },
        "benchmarks": {
            "views_48h_target": 500,      # Realistic for new channel
            "like_ratio_target": 0.05,    # 5% like rate
            "comment_rate_target": 0.01,  # 1% comment rate
        },
        "assessment": {},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Auto-assess against benchmarks
    debrief["assessment"]["views"] = "above" if perf.views >= 500 else "below"
    debrief["assessment"]["engagement"] = "above" if (perf.likes / max(perf.views, 1)) >= 0.05 else "below"

    return debrief


# ── Comment Monitoring ───────────────────────────────────────────────────────

def get_video_comments(video_id: str, max_results: int = 50) -> list[dict]:
    """
    Fetch comments for a video. Used by Community Manager agent
    for engagement monitoring and response.
    """
    youtube = get_youtube_service()

    response = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        order="time",
        textFormat="plainText",
    ).execute()

    comments = []
    for item in response.get("items", []):
        snippet = item["snippet"]["topLevelComment"]["snippet"]
        comments.append({
            "comment_id": item["id"],
            "author": snippet["authorDisplayName"],
            "text": snippet["textDisplay"],
            "likes": snippet["likeCount"],
            "published_at": snippet["publishedAt"],
            "is_question": "?" in snippet["textDisplay"],
        })

    return comments


def add_comment(video_id: str, comment_text: str) -> dict:
    """Add a top-level comment on a video (e.g. for pinned comment)."""
    youtube = get_youtube_service()

    response = youtube.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text,
                    }
                },
            }
        },
    ).execute()

    comment_id = response["snippet"]["topLevelComment"]["id"]
    print(f"[UPLOADER] ✓ Comment added: {comment_id}")
    return {"comment_id": comment_id, "text": comment_text}


def reply_to_comment(comment_id: str, reply_text: str) -> dict:
    """Reply to a YouTube comment (requires approval from Community Manager)."""
    youtube = get_youtube_service()

    response = youtube.comments().insert(
        part="snippet",
        body={
            "snippet": {
                "parentId": comment_id,
                "textOriginal": reply_text,
            }
        },
    ).execute()

    return {"reply_id": response["id"], "text": reply_text}


def upload_captions(video_id: str, captions_path: str, language: str = "en", name: str = "English") -> dict:
    """
    Upload an SRT caption file for a video.

    Captions boost SEO — every word becomes searchable by YouTube.
    Discovery Digital Networks study: +7.32% views from captions.
    """
    youtube = get_youtube_service()
    _, _, _, _, MediaFileUpload = _import_google()

    media = MediaFileUpload(captions_path, mimetype="application/x-subrip")

    response = youtube.captions().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "language": language,
                "name": name,
                "isDraft": False,
            }
        },
        media_body=media,
    ).execute()

    print(f"[UPLOADER] ✓ Captions uploaded for {video_id} ({language})")
    return {"caption_id": response["id"], "language": language}
