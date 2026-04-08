"""Video Pipeline API — endpoints for AI media generation and video assembly."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/video", tags=["video-pipeline"])


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class GenerateVideoRequest(BaseModel):
    prompt: str
    duration: float = 5.0
    aspect_ratio: str = "16:9"


class GenerateImageRequest(BaseModel):
    prompt: str
    width: int = 1344
    height: int = 768
    style: str = "photorealistic"


class StillToVideoRequest(BaseModel):
    image_url: str
    motion_type: str = "ken_burns"
    duration: float = 5.0


class GenerateCaptionsRequest(BaseModel):
    audio_url: str
    language: str = "en"


class SceneRequest(BaseModel):
    scene_number: int
    description: str
    visual_type: str = "ai_video"
    duration: float = 5.0
    camera_motion: str = ""
    mood: str = ""
    aspect_ratio: str = "16:9"


class GenerateEpisodeRequest(BaseModel):
    episode_id: str = "ep001"
    scenes: list[SceneRequest]
    max_concurrent: int = 3


class MediaAssetResponse(BaseModel):
    media_type: str
    url: str | None = None
    file_path: str | None = None
    prompt: str = ""
    duration: float | None = None
    cost: float = 0.0
    source: str = ""


class EpisodeGenerationResponse(BaseModel):
    total_assets: int
    total_cost: float
    generation_time: float
    errors: list[str]
    assets: list[MediaAssetResponse]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/generate/clip", response_model=MediaAssetResponse)
async def generate_video_clip(req: GenerateVideoRequest):
    """Generate an AI video clip using Kling v2 / Runway Gen-4."""
    from app.services.ai_media_generator import generate_video_clip as gen_clip

    try:
        asset = await gen_clip(
            prompt=req.prompt,
            duration=req.duration,
            aspect_ratio=req.aspect_ratio,
        )
        return MediaAssetResponse(
            media_type=asset.media_type.value,
            url=asset.url,
            prompt=asset.prompt,
            duration=asset.duration,
            cost=asset.cost,
            source=asset.source,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/image", response_model=MediaAssetResponse)
async def generate_image(req: GenerateImageRequest):
    """Generate a photorealistic image using Flux 2 Pro."""
    from app.services.ai_media_generator import generate_still_image

    try:
        asset = await generate_still_image(
            prompt=req.prompt,
            width=req.width,
            height=req.height,
            style=req.style,
        )
        return MediaAssetResponse(
            media_type=asset.media_type.value,
            url=asset.url,
            prompt=asset.prompt,
            cost=asset.cost,
            source=asset.source,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/still-to-video", response_model=MediaAssetResponse)
async def still_to_video(req: StillToVideoRequest):
    """Convert a still image to video with Ken Burns / parallax motion."""
    from app.services.ai_media_generator import still_to_video as s2v

    try:
        asset = await s2v(
            image_url=req.image_url,
            motion_type=req.motion_type,
            duration=req.duration,
        )
        return MediaAssetResponse(
            media_type=asset.media_type.value,
            url=asset.url,
            duration=asset.duration,
            cost=asset.cost,
            source=asset.source,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/captions", response_model=MediaAssetResponse)
async def generate_captions(req: GenerateCaptionsRequest):
    """Generate captions using AssemblyAI."""
    from app.services.ai_media_generator import generate_captions as gen_caps

    try:
        asset = await gen_caps(
            audio_url=req.audio_url,
            language=req.language,
        )
        return MediaAssetResponse(
            media_type=asset.media_type.value,
            cost=asset.cost,
            source=asset.source,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/episode", response_model=EpisodeGenerationResponse)
async def generate_episode(req: GenerateEpisodeRequest):
    """Batch generate all AI media for an episode."""
    from app.services.ai_media_generator import (
        SceneSpec,
        generate_episode_media,
    )

    scenes = [
        SceneSpec(
            scene_number=s.scene_number,
            description=s.description,
            visual_type=s.visual_type,
            duration=s.duration,
            camera_motion=s.camera_motion,
            mood=s.mood,
            aspect_ratio=s.aspect_ratio,
        )
        for s in req.scenes
    ]

    try:
        result = await generate_episode_media(
            scenes=scenes,
            episode_id=req.episode_id,
            max_concurrent=req.max_concurrent,
        )
        return EpisodeGenerationResponse(
            total_assets=len(result.assets),
            total_cost=result.total_cost,
            generation_time=result.generation_time,
            errors=result.errors,
            assets=[
                MediaAssetResponse(
                    media_type=a.media_type.value,
                    url=a.url,
                    file_path=a.file_path,
                    prompt=a.prompt,
                    duration=a.duration,
                    cost=a.cost,
                    source=a.source,
                )
                for a in result.assets
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pipeline/status")
async def pipeline_status():
    """Check video pipeline health and available services."""
    import shutil

    from app.config import ASSEMBLYAI_API_KEY, FAL_API_KEY

    ffmpeg_available = shutil.which("ffmpeg") is not None
    ffprobe_available = shutil.which("ffprobe") is not None

    return {
        "fal_ai_configured": bool(FAL_API_KEY),
        "assemblyai_configured": bool(ASSEMBLYAI_API_KEY),
        "ffmpeg_available": ffmpeg_available,
        "ffprobe_available": ffprobe_available,
        "services": {
            "video_generation": "ready" if FAL_API_KEY else "needs_api_key",
            "image_generation": "ready" if FAL_API_KEY else "needs_api_key",
            "caption_generation": "ready" if ASSEMBLYAI_API_KEY else "needs_api_key",
            "video_assembly": "ready" if ffmpeg_available else "needs_ffmpeg",
        },
    }
