"""
AI Media Generator — Unified interface for AI video + image generation

Uses fal.ai as the API aggregator (600+ models, 30-50% cheaper than direct APIs).
Provides access to:
  - Kling AI v2.0 — cinematic AI video clips
  - Flux 2 Pro — photorealistic still images (for Ken Burns)
  - Runway Gen-4.5 — highest quality AI video (optional)
  - Luma Ray3 — atmospheric/environmental footage (optional)

Cost per episode (~10 min documentary):
  - 14 AI video clips: ~$2-3
  - 15 stills for Ken Burns: ~$0.45
  - Total media generation: ~$3-4

Usage:
  from app.services.ai_media_generator import generate_video_clip, generate_still_image
  clip_path = generate_video_clip("ep001", 1, "Woman typing at laptop...", duration=8)
  still_path = generate_still_image("ep001", 5, "Dramatic office panorama...", style="cinematic")
"""
from __future__ import annotations

import os
import time
import json
import subprocess
from pathlib import Path
from typing import Optional

import httpx

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


# ── Configuration ────────────────────────────────────────────────────────────

FAL_API_KEY = os.getenv("FAL_API_KEY", "")
KLING_API_KEY = os.getenv("KLING_API_KEY", "")
RUNWAY_API_KEY = os.getenv("RUNWAY_API_KEY", "")

ASSET_DIR = os.getenv("ASSET_DIR", os.path.expanduser("~/youtube-empire/assets"))

# fal.ai endpoints (unified API)
FAL_BASE = "https://queue.fal.run"
FAL_MODELS = {
    "kling_v2": "fal-ai/kling-video/v2/master",       # Kling AI v2 — cinematic video
    "flux_pro": "fal-ai/flux-pro/v1.1",                 # Flux 2 Pro — photorealistic stills
    "flux_schnell": "fal-ai/flux/schnell",               # Flux Schnell — fast drafts
    "runway_gen4": "fal-ai/runway-gen4/turbo/image-to-video",  # Runway Gen-4.5
    "luma_ray": "fal-ai/luma-dream-machine",             # Luma Dream Machine
}

# V-Real AI visual style directive (appended to all prompts)
STYLE_SUFFIX = (
    ", cinematic documentary style, shallow depth of field, "
    "dramatic lighting, dark moody atmosphere, teal and amber color palette, "
    "4K quality, film grain, professional photography"
)


# ── Video Generation ─────────────────────────────────────────────────────────

def generate_video_clip(
    episode_id: str,
    scene_num: int,
    prompt: str,
    duration: int = 8,
    model: str = "kling_v2",
    aspect_ratio: str = "16:9",
) -> Optional[str]:
    """
    Generate a cinematic AI video clip.

    Priority: fal.ai (Kling v2) → direct Kling API → None

    Args:
        episode_id: e.g. "ep001"
        scene_num:  Scene number for filename
        prompt:     Detailed visual prompt
        duration:   Clip length in seconds (5-10 for Kling)
        model:      Model key from FAL_MODELS
        aspect_ratio: "16:9" for landscape, "9:16" for Shorts

    Returns: Path to generated MP4, or None if all attempts fail.
    """
    output_dir = os.path.join(ASSET_DIR, episode_id, "footage")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"scene_{scene_num:02d}.mp4")

    if os.path.exists(output_path):
        print(f"[AI-MEDIA] Scene {scene_num:02d} already exists: {output_path}")
        return output_path

    full_prompt = prompt + STYLE_SUFFIX

    # Try 1: fal.ai (unified API — cheapest & fastest)
    if FAL_API_KEY:
        result = _fal_generate_video(full_prompt, duration, model, aspect_ratio)
        if result:
            _download_file(result, output_path)
            print(f"[AI-MEDIA] ✓ Scene {scene_num:02d} generated via fal.ai ({model})")
            return output_path

    # Try 2: Direct Kling API
    if KLING_API_KEY:
        result = _kling_direct_generate(full_prompt, duration, aspect_ratio)
        if result:
            _download_file(result, output_path)
            print(f"[AI-MEDIA] ✓ Scene {scene_num:02d} generated via Kling direct API")
            return output_path

    print(f"[AI-MEDIA] ✗ Scene {scene_num:02d} — no AI video API available")
    return None


def _fal_generate_video(prompt: str, duration: int, model: str, aspect_ratio: str) -> Optional[str]:
    """Generate video via fal.ai queue API."""
    model_id = FAL_MODELS.get(model, FAL_MODELS["kling_v2"])

    try:
        # Submit to queue
        response = httpx.post(
            f"{FAL_BASE}/{model_id}",
            headers={
                "Authorization": f"Key {FAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "duration": str(min(duration, 10)),
                "aspect_ratio": aspect_ratio,
            },
            timeout=30,
        )

        if response.status_code not in (200, 201):
            print(f"[FAL] Submit failed: {response.status_code}")
            return None

        data = response.json()

        # If result is immediate
        video_url = data.get("video", {}).get("url") or data.get("url", "")
        if video_url:
            return video_url

        # If queued, poll for result
        request_id = data.get("request_id", "")
        if request_id:
            return _fal_poll_result(model_id, request_id)

    except Exception as e:
        print(f"[FAL] Error: {str(e)[:200]}")

    return None


def _fal_poll_result(model_id: str, request_id: str, max_wait: int = 300) -> Optional[str]:
    """Poll fal.ai queue for completed result."""
    status_url = f"{FAL_BASE}/{model_id}/requests/{request_id}/status"
    result_url = f"{FAL_BASE}/{model_id}/requests/{request_id}"

    start = time.time()
    while time.time() - start < max_wait:
        try:
            status = httpx.get(
                status_url,
                headers={"Authorization": f"Key {FAL_API_KEY}"},
                timeout=15,
            )
            if status.status_code == 200:
                data = status.json()
                state = data.get("status", "")

                if state == "COMPLETED":
                    # Fetch result
                    result = httpx.get(
                        result_url,
                        headers={"Authorization": f"Key {FAL_API_KEY}"},
                        timeout=15,
                    )
                    if result.status_code == 200:
                        result_data = result.json()
                        return (
                            result_data.get("video", {}).get("url")
                            or result_data.get("url", "")
                        )

                elif state in ("FAILED", "CANCELLED"):
                    print(f"[FAL] Generation {state}")
                    return None

        except Exception:
            pass

        time.sleep(5)

    print(f"[FAL] Timed out after {max_wait}s")
    return None


def _kling_direct_generate(prompt: str, duration: int, aspect_ratio: str) -> Optional[str]:
    """Generate video via direct Kling AI API."""
    try:
        response = httpx.post(
            "https://api.klingai.com/v1/videos/generations",
            headers={
                "Authorization": f"Bearer {KLING_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "duration": str(min(duration, 10)),
                "aspect_ratio": aspect_ratio,
                "model": "kling-v2.0",
            },
            timeout=120,
        )

        if response.status_code != 200:
            return None

        data = response.json()
        video_url = data.get("data", {}).get("video_url", "")
        if video_url:
            return video_url

        # Poll for async result
        task_id = data.get("data", {}).get("task_id", "")
        if task_id:
            for _ in range(30):
                time.sleep(10)
                status = httpx.get(
                    f"https://api.klingai.com/v1/videos/generations/{task_id}",
                    headers={"Authorization": f"Bearer {KLING_API_KEY}"},
                    timeout=30,
                )
                if status.status_code == 200:
                    s_data = status.json()
                    if s_data.get("data", {}).get("status") == "completed":
                        return s_data.get("data", {}).get("video_url", "")
                    elif s_data.get("data", {}).get("status") == "failed":
                        return None

    except Exception as e:
        print(f"[KLING] Error: {str(e)[:200]}")

    return None


# ── Still Image Generation ───────────────────────────────────────────────────

def generate_still_image(
    episode_id: str,
    scene_num: int,
    prompt: str,
    style: str = "cinematic",
    model: str = "flux_pro",
) -> Optional[str]:
    """
    Generate a photorealistic still image via Flux 2 Pro.

    These stills are used with Ken Burns (zoom/pan) effects to create
    engaging motion from static images — a ColdFusion signature technique.

    Args:
        episode_id: e.g. "ep001"
        scene_num:  Scene number for filename
        prompt:     Detailed visual prompt
        style:      "cinematic", "documentary", "dramatic"
        model:      "flux_pro" (quality) or "flux_schnell" (speed)

    Returns: Path to generated image, or None.
    """
    output_dir = os.path.join(ASSET_DIR, episode_id, "stills")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"still_{scene_num:02d}.jpg")

    if os.path.exists(output_path):
        print(f"[AI-MEDIA] Still {scene_num:02d} already exists")
        return output_path

    if not FAL_API_KEY:
        print("[AI-MEDIA] No FAL_API_KEY — cannot generate stills")
        return None

    full_prompt = prompt + STYLE_SUFFIX
    model_id = FAL_MODELS.get(model, FAL_MODELS["flux_pro"])

    try:
        response = httpx.post(
            f"{FAL_BASE}/{model_id}",
            headers={
                "Authorization": f"Key {FAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": full_prompt,
                "image_size": "landscape_16_9",
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "num_images": 1,
                "enable_safety_checker": False,
            },
            timeout=60,
        )

        if response.status_code not in (200, 201):
            print(f"[FAL] Image generation failed: {response.status_code}")
            return None

        data = response.json()

        # Check for immediate result
        images = data.get("images", [])
        if images:
            image_url = images[0].get("url", "")
            if image_url:
                _download_file(image_url, output_path)
                print(f"[AI-MEDIA] ✓ Still {scene_num:02d} generated via Flux 2 Pro")
                return output_path

        # Check for queued result
        request_id = data.get("request_id", "")
        if request_id:
            result_url = _fal_poll_result(model_id, request_id, max_wait=60)
            if result_url:
                _download_file(result_url, output_path)
                print(f"[AI-MEDIA] ✓ Still {scene_num:02d} generated via Flux 2 Pro")
                return output_path

    except Exception as e:
        print(f"[AI-MEDIA] Still generation error: {str(e)[:200]}")

    return None


def still_to_video(
    image_path: str,
    output_path: str,
    duration: float = 8.0,
    motion: str = "ken_burns",
) -> str:
    """
    Convert a still image to video with Ken Burns motion effect.

    This is a ColdFusion signature technique — photorealistic stills
    with slow zoom/pan create a cinematic feel without AI video costs.

    Args:
        image_path: Path to source image
        output_path: Output video path
        duration: Clip duration in seconds
        motion: "ken_burns", "zoom_in", "zoom_out", "pan_left", "pan_right"
    """
    fps = 30
    frames = int(duration * fps)

    motion_filters = {
        "ken_burns": (
            f"scale=8000:-1,zoompan="
            f"z='min(zoom+0.001,1.3)':"
            f"x='iw/2-(iw/zoom/2)+{50}*on/{frames}':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=3840x2160:fps={fps}"
        ),
        "zoom_in": (
            f"scale=8000:-1,zoompan="
            f"z='min(zoom+0.0015,1.5)':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=3840x2160:fps={fps}"
        ),
        "zoom_out": (
            f"scale=8000:-1,zoompan="
            f"z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=3840x2160:fps={fps}"
        ),
        "pan_left": (
            f"scale=8000:-1,zoompan="
            f"z='1.2':"
            f"x='iw/2-(iw/zoom/2)-{200}*on/{frames}':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=3840x2160:fps={fps}"
        ),
        "pan_right": (
            f"scale=8000:-1,zoompan="
            f"z='1.2':"
            f"x='iw/2-(iw/zoom/2)+{200}*on/{frames}':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={frames}:s=3840x2160:fps={fps}"
        ),
    }

    vf = motion_filters.get(motion, motion_filters["ken_burns"])

    subprocess.run(
        [
            "ffmpeg", "-y", "-loop", "1", "-i", image_path,
            "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-pix_fmt", "yuv420p", "-t", str(duration),
            "-an", output_path,
        ],
        check=True, capture_output=True, timeout=120,
    )
    return output_path


# ── Utilities ────────────────────────────────────────────────────────────────

def _download_file(url: str, output_path: str) -> bool:
    """Download a file from URL."""
    try:
        response = httpx.get(url, timeout=120, follow_redirects=True)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"[DOWNLOAD] Failed: {str(e)[:100]}")
    return False


# ── Batch Generation ─────────────────────────────────────────────────────────

def generate_episode_media(
    episode_id: str,
    scenes: list[dict],
    notify_make_fn=None,
) -> dict:
    """
    Generate all AI media for an episode.

    For each scene, tries:
      1. AI video clip (Kling v2 via fal.ai)
      2. AI still image + Ken Burns motion (Flux 2 Pro via fal.ai)
      3. Skip (assembly will use branded background)

    Args:
        episode_id: e.g. "ep001"
        scenes: Scene definitions with kling_prompt or query fields
        notify_make_fn: Optional Make.com notifier

    Returns: Dict with stats on what was generated.
    """
    stats = {"video_clips": 0, "stills": 0, "skipped": 0, "total": len(scenes)}

    for scene in scenes:
        scene_num = scene.get("scene", 0)
        prompt = scene.get("kling_prompt", scene.get("query", ""))

        # Try video clip first
        clip = generate_video_clip(episode_id, scene_num, prompt,
                                   duration=min(scene.get("duration", 8), 10))
        if clip:
            stats["video_clips"] += 1
            time.sleep(2)  # Rate limit
            continue

        # Fall back to still + Ken Burns
        still = generate_still_image(episode_id, scene_num, prompt)
        if still:
            output_dir = os.path.join(ASSET_DIR, episode_id, "footage")
            video_from_still = os.path.join(output_dir, f"scene_{scene_num:02d}.mp4")
            try:
                still_to_video(still, video_from_still,
                               duration=scene.get("duration", 8),
                               motion="ken_burns" if scene_num % 3 == 0 else "zoom_in")
                stats["stills"] += 1
            except Exception:
                stats["skipped"] += 1
            time.sleep(1)
            continue

        stats["skipped"] += 1

    print(f"[AI-MEDIA] Episode {episode_id} media generation complete:")
    print(f"[AI-MEDIA]   Video clips: {stats['video_clips']}")
    print(f"[AI-MEDIA]   Stills→Ken Burns: {stats['stills']}")
    print(f"[AI-MEDIA]   Skipped: {stats['skipped']}")

    if notify_make_fn:
        notify_make_fn("video", {
            "status": "media_generated",
            "episode_id": episode_id,
            **stats,
        })

    return stats
