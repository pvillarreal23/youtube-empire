"""
Media Pipeline Router

API endpoints for the automated production pipeline:
  - Video assembly (FFmpeg)
  - Footage sourcing (Pexels + Kling AI + local)
  - YouTube upload & management
  - Post-publish monitoring
"""
from __future__ import annotations

import os
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.services.video_assembler import (
    AssemblyProject, SceneClip, TextOverlay,
    assemble_video, create_project_from_script, cleanup_temp,
)
from app.services.footage_sourcer import (
    SceneFootageRequest,
    source_footage_for_episode,
    search_pexels_videos,
)
from app.services.youtube_uploader import (
    VideoMetadata, upload_video, set_video_public,
    schedule_video, get_video_performance,
    get_video_comments, build_description,
)
from app.services.post_publish_monitor import (
    MonitoredVideo, run_monitoring_cycle, generate_debrief,
    classify_comment,
)


router = APIRouter(prefix="/api/media", tags=["media"])

# In-memory store for monitored videos (production would use DB)
_monitored_videos: dict[str, MonitoredVideo] = {}


# ── Request/Response Models ──────────────────────────────────────────────────

class AssembleRequest(BaseModel):
    episode_id: str
    title: str
    voice_audio_path: str
    music_path: Optional[str] = None
    scenes: list[dict] = Field(default_factory=list)
    text_overlays: list[dict] = Field(default_factory=list)

class AssembleFromScriptRequest(BaseModel):
    episode_id: str
    title: str
    voice_audio_path: str
    clips_dir: str
    music_path: Optional[str] = None
    scene_descriptions: list[dict] = Field(default_factory=list)

class FootageRequest(BaseModel):
    episode_id: str
    scenes: list[dict] = Field(default_factory=list)

class UploadRequest(BaseModel):
    video_path: str
    title: str
    description: str
    tags: list[str] = Field(default_factory=list)
    thumbnail_path: Optional[str] = None
    publish_at: Optional[str] = None
    chapters: list[dict] = Field(default_factory=list)

class MonitorRequest(BaseModel):
    video_id: str
    title: str
    episode_id: str
    published_at: str


# ── Video Assembly Endpoints ─────────────────────────────────────────────────

@router.post("/assemble")
async def assemble_episode(data: AssembleRequest, background_tasks: BackgroundTasks):
    """
    Assemble a complete video from voice audio + clips + music.
    Runs in background — returns immediately with status.
    """
    project = AssemblyProject(
        episode_id=data.episode_id,
        title=data.title,
        voice_audio_path=data.voice_audio_path,
        music_path=data.music_path,
    )

    for s in data.scenes:
        project.scenes.append(SceneClip(
            scene_number=s.get("scene_number", 0),
            video_path=s.get("video_path", ""),
            start_time=s.get("start_time", 0),
            end_time=s.get("end_time", 10),
            motion=s.get("motion", "zoom_in"),
            description=s.get("description", ""),
        ))

    for t in data.text_overlays:
        project.text_overlays.append(TextOverlay(
            text=t.get("text", ""),
            start_time=t.get("start_time", 0),
            end_time=t.get("end_time", 5),
            position=t.get("position", "center"),
            font_size=t.get("font_size", 48),
        ))

    background_tasks.add_task(assemble_video, project)
    return {
        "status": "assembling",
        "episode_id": data.episode_id,
        "message": f"Video assembly started for '{data.title}'. Check output directory when complete.",
    }


@router.post("/assemble-from-script")
async def assemble_from_script(data: AssembleFromScriptRequest, background_tasks: BackgroundTasks):
    """
    Assemble video directly from script scene descriptions.
    Automatically matches clips from the clips directory.
    """
    project = create_project_from_script(
        episode_id=data.episode_id,
        title=data.title,
        voice_audio=data.voice_audio_path,
        scene_descriptions=data.scene_descriptions,
        clips_dir=data.clips_dir,
        music_path=data.music_path,
    )

    background_tasks.add_task(assemble_video, project)
    return {
        "status": "assembling",
        "episode_id": data.episode_id,
        "scenes_found": len(project.scenes),
        "text_overlays": len(project.text_overlays),
    }


# ── Footage Sourcing Endpoints ───────────────────────────────────────────────

@router.post("/footage/source")
async def source_footage(data: FootageRequest):
    """
    Auto-source footage for all scenes in an episode.
    Checks local library → Pexels → Kling AI.
    """
    requests = [
        SceneFootageRequest(
            scene_number=s.get("scene_number", 0),
            description=s.get("description", ""),
            duration_needed=s.get("duration", 5),
            mood=s.get("mood", ""),
            keywords=s.get("keywords", []),
            prefer_source=s.get("prefer_source", "any"),
        )
        for s in data.scenes
    ]

    package = await source_footage_for_episode(data.episode_id, requests)
    return {
        "episode_id": data.episode_id,
        "total_clips": package.total_clips,
        "sources_used": package.sources_used,
        "missing_scenes": package.missing_scenes,
        "scenes": package.scenes,
    }


@router.get("/footage/search")
async def search_footage(query: str, per_page: int = 10):
    """Search Pexels for stock footage by keyword."""
    results = await search_pexels_videos(query, per_page=per_page)
    return {
        "query": query,
        "results": [
            {
                "source": r.source,
                "url": r.url,
                "preview": r.preview_url,
                "duration": r.duration,
                "resolution": f"{r.width}x{r.height}",
            }
            for r in results
        ],
    }


# ── YouTube Upload Endpoints ─────────────────────────────────────────────────

@router.post("/youtube/upload")
async def youtube_upload(data: UploadRequest):
    """
    Upload video to YouTube (always as PRIVATE first).
    Pedro must approve before making public.
    """
    metadata = VideoMetadata(
        title=data.title,
        description=data.description,
        tags=data.tags,
        thumbnail_path=data.thumbnail_path,
        publish_at=data.publish_at,
        chapters=data.chapters,
        privacy_status="private",
    )

    result = upload_video(data.video_path, metadata)
    return {
        "video_id": result.video_id,
        "url": result.url,
        "status": result.status,
        "privacy": result.privacy,
        "publish_at": result.publish_at,
    }


@router.post("/youtube/{video_id}/publish")
async def youtube_publish(video_id: str):
    """Make a private video public (Pedro's approval step)."""
    set_video_public(video_id)
    return {"video_id": video_id, "status": "public"}


@router.post("/youtube/{video_id}/schedule")
async def youtube_schedule(video_id: str, publish_at: str):
    """Schedule a private video to auto-publish."""
    schedule_video(video_id, publish_at)
    return {"video_id": video_id, "scheduled_for": publish_at}


@router.get("/youtube/{video_id}/performance")
async def youtube_performance(video_id: str):
    """Get current performance metrics for a video."""
    perf = get_video_performance(video_id)
    return perf.__dict__


@router.get("/youtube/{video_id}/comments")
async def youtube_comments(video_id: str, max_results: int = 50):
    """Get and analyze comments on a video."""
    comments = get_video_comments(video_id, max_results=max_results)
    analyzed = [classify_comment(c).__dict__ for c in comments]
    return {
        "video_id": video_id,
        "total": len(analyzed),
        "comments": analyzed,
        "summary": {
            "questions": len([c for c in analyzed if c["category"] == "question"]),
            "positive": len([c for c in analyzed if c["category"] == "positive"]),
            "negative": len([c for c in analyzed if c["category"] == "negative"]),
            "suggestions": len([c for c in analyzed if c["category"] == "suggestion"]),
        },
    }


# ── Post-Publish Monitoring Endpoints ────────────────────────────────────────

@router.post("/monitor/start")
async def start_monitoring(data: MonitorRequest):
    """Start monitoring a published video's performance and comments."""
    video = MonitoredVideo(
        video_id=data.video_id,
        title=data.title,
        episode_id=data.episode_id,
        published_at=data.published_at,
    )
    _monitored_videos[data.video_id] = video
    return {
        "status": "monitoring_started",
        "video_id": data.video_id,
        "title": data.title,
    }


@router.post("/monitor/{video_id}/check")
async def run_check(video_id: str):
    """Run a monitoring cycle — check performance + process comments."""
    video = _monitored_videos.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not being monitored. Call /monitor/start first.")

    result = await run_monitoring_cycle(video)
    return result


@router.post("/monitor/{video_id}/debrief")
async def create_debrief(video_id: str, report_type: str = "48h"):
    """Generate a post-publish debrief report."""
    video = _monitored_videos.get(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not being monitored.")

    debrief = await generate_debrief(video, report_type)
    return debrief.__dict__


@router.get("/monitor/active")
async def list_monitored():
    """List all videos currently being monitored."""
    return {
        "count": len(_monitored_videos),
        "videos": [
            {
                "video_id": v.video_id,
                "title": v.title,
                "episode_id": v.episode_id,
                "checks": len(v.checks),
                "comments_processed": len(v.comments_processed),
                "debrief_generated": v.debrief_generated,
            }
            for v in _monitored_videos.values()
        ],
    }
