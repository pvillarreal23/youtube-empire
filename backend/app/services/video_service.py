"""
Video generation service for V-Real AI.

Style: Documentary — AI voiceover + Kling AI-generated footage + text overlays + captions.

Pipeline:
  1. Parse script for sections, visual cues ([B-ROLL:], [GRAPHIC:], etc.)
  2. Generate voiceover via ElevenLabs
  3. Generate custom video scenes via Kling AI matching visual cues
  4. Fall back to Pexels stock footage if Kling is unavailable
  5. Assemble video via Creatomate (or Shotstack)
  6. Return video URL for YouTube upload

Tools:
  - ElevenLabs: AI voiceover (deep, documentary narration)
  - Kling AI: Custom AI-generated video scenes (primary)
  - Pexels: Stock footage fallback (secondary)
  - Creatomate: Video assembly + text overlays + captions
  - Canva: Thumbnails + banner + profile pic (handled separately)
"""

from __future__ import annotations

import re
import asyncio
import httpx
from app.config import ELEVENLABS_API_KEY, PEXELS_API_KEY, CREATOMATE_API_KEY, KLING_API_KEY


# --- Script Parser ---

def parse_script_cues(script: str) -> dict:
    """Extract spoken text and visual cues from a script."""
    lines = script.split("\n")
    sections = []
    current_section = {"text": [], "visuals": []}

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Extract visual cues
        broll = re.findall(r'\[B-ROLL:\s*(.+?)\]', line)
        graphic = re.findall(r'\[GRAPHIC:\s*(.+?)\]', line)
        screen = re.findall(r'\[SCREEN RECORD:\s*(.+?)\]', line)
        cut = re.findall(r'\[CUT TO:\s*(.+?)\]', line)

        if broll or graphic or screen or cut:
            for cue in broll:
                current_section["visuals"].append({"type": "b-roll", "description": cue})
            for cue in graphic:
                current_section["visuals"].append({"type": "graphic", "description": cue})
            for cue in screen:
                current_section["visuals"].append({"type": "screen-record", "description": cue})
            for cue in cut:
                current_section["visuals"].append({"type": "cut", "description": cue})

        # Also parse scene descriptions in brackets (like the Wake Up script has)
        scene_desc = re.findall(r'^\[([A-Z][^]]+)\]$', line)
        if scene_desc and not any(line.startswith(f"[{t}") for t in ["B-ROLL", "GRAPHIC", "SCREEN", "CUT", "SFX", "MUSIC", "SECTION", "ACT", "HOOK", "CONCLUSION"]):
            current_section["visuals"].append({"type": "scene", "description": scene_desc[0]})

        # Section break detection
        if line.startswith("[SECTION") or line.startswith("[ACT") or line.startswith("[HOOK") or line.startswith("[CONCLUSION") or line.startswith("## ["):
            if current_section["text"]:
                sections.append(current_section)
                current_section = {"text": [], "visuals": []}
            continue

        # Clean line of cue brackets for spoken text
        clean = re.sub(r'\[.+?\]', '', line).strip()
        # Remove markdown and quote marks for spoken text
        clean = clean.strip('"').strip('#').strip()
        if clean and not clean.startswith("#") and len(clean) > 3:
            current_section["text"].append(clean)

    if current_section["text"]:
        sections.append(current_section)

    return {
        "sections": sections,
        "full_spoken_text": " ".join(
            " ".join(s["text"]) for s in sections
        ),
    }


# --- ElevenLabs Voiceover ---

async def generate_voiceover(text: str, voice_id: str = "pNInz6obpgDQGcFmaJgB") -> bytes:
    """
    Generate voiceover audio from text using ElevenLabs.

    Default voice: "Adam" — deep, authoritative, documentary style.
    Other good options:
      - "ErXwobaYiN019PkySvjV" = Antoni (warm, conversational)
      - "VR6AewLTigWG4xSOukaG" = Arnold (deep, serious)
      - "pNInz6obpgDQGcFmaJgB" = Adam (deep, narration)

    Returns raw MP3 bytes.
    """
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.75,
                    "style": 0.3,
                },
            },
        )
        resp.raise_for_status()
        return resp.content


# --- Kling AI Video Generation ---

async def generate_kling_scene(prompt: str, duration: int = 5) -> dict | None:
    """
    Generate a video scene using Kling AI.

    Args:
        prompt: Scene description (e.g. "Person lying in bed, alarm ringing, dark room, gray light through blinds")
        duration: Clip duration in seconds (5 or 10)

    Returns:
        {"url": "...", "duration": N} or None if generation fails
    """
    if not KLING_API_KEY:
        return None

    async with httpx.AsyncClient(timeout=300) as client:
        # Create video generation task
        resp = await client.post(
            "https://api.klingai.com/v1/videos/text2video",
            headers={
                "Authorization": f"Bearer {KLING_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "duration": str(duration),
                "aspect_ratio": "16:9",
                "mode": "quality",  # "quality" for best results, "speed" for faster
            },
        )
        resp.raise_for_status()
        data = resp.json()
        task_id = data.get("data", {}).get("task_id")

        if not task_id:
            return None

        # Poll for completion (Kling can take 2-5 minutes per clip)
        for _ in range(60):
            await asyncio.sleep(5)
            status_resp = await client.get(
                f"https://api.klingai.com/v1/videos/text2video/{task_id}",
                headers={"Authorization": f"Bearer {KLING_API_KEY}"},
            )
            status_data = status_resp.json()
            task_status = status_data.get("data", {}).get("task_status")

            if task_status == "succeed":
                videos = status_data.get("data", {}).get("task_result", {}).get("videos", [])
                if videos:
                    return {
                        "url": videos[0]["url"],
                        "duration": duration,
                    }
                return None

            if task_status == "failed":
                return None

    return None


async def generate_scenes_for_cues(visuals: list[dict]) -> list[dict]:
    """
    Generate video scenes for each visual cue.
    Uses Kling AI for custom scenes, falls back to Pexels stock footage.
    """
    scenes = []

    for cue in visuals:
        description = cue["description"]

        # Build a cinematic prompt for Kling
        kling_prompt = (
            f"Cinematic documentary style, 4K, moody lighting, shallow depth of field. "
            f"Scene: {description}. "
            f"Color grade: dark tones, slight blue/purple tint, high contrast."
        )

        # Try Kling first
        scene = await generate_kling_scene(kling_prompt)
        if scene:
            scenes.append({**scene, "cue": description, "source": "kling"})
            continue

        # Fall back to Pexels stock footage
        stock = await _search_pexels(description)
        if stock:
            scenes.append({**stock[0], "cue": description, "source": "pexels"})

    return scenes


# --- Pexels Stock Footage (fallback) ---

async def _search_pexels(query: str, per_page: int = 3) -> list[dict]:
    """Search Pexels for stock video clips. Used as fallback when Kling is unavailable."""
    if not PEXELS_API_KEY:
        return []

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "per_page": per_page, "orientation": "landscape"},
        )
        resp.raise_for_status()
        data = resp.json()

    clips = []
    for video in data.get("videos", []):
        for file in video.get("video_files", []):
            if file.get("quality") == "hd":
                clips.append({
                    "url": file["link"],
                    "width": file.get("width", 1920),
                    "height": file.get("height", 1080),
                    "duration": video.get("duration", 10),
                })
                break
    return clips


# --- Video Assembly ---
# Uses Remotion (primary) or Creatomate (fallback)

async def assemble_video_remotion(
    voiceover_path: str,
    scenes: list[dict],
    title: str,
    captions: list[dict] | None = None,
) -> str:
    """
    Assemble video using Remotion (React-based video renderer).
    Renders locally via CLI — full control over titles, transitions, captions.
    Returns path to the rendered MP4 file.
    """
    import json
    import subprocess
    from pathlib import Path

    video_dir = Path(__file__).resolve().parent.parent.parent.parent / "video"

    # Build input props for Remotion
    props = {
        "title": title,
        "voiceoverUrl": voiceover_path,
        "scenes": [
            {
                "id": f"scene-{i}",
                "type": s.get("type", "b-roll"),
                "description": s.get("cue", ""),
                "videoUrl": s["url"],
                "duration": s.get("duration", 10),
                "textOverlay": s.get("text_overlay"),
            }
            for i, s in enumerate(scenes)
        ],
        "captions": captions or [],
        "durationInSeconds": sum(s.get("duration", 10) for s in scenes) + 4,
    }

    props_path = video_dir / "out" / "props.json"
    props_path.parent.mkdir(parents=True, exist_ok=True)
    props_path.write_text(json.dumps(props))

    output_path = video_dir / "out" / "episode.mp4"

    # Calculate total frames
    total_frames = int(props["durationInSeconds"] * 30)

    result = subprocess.run(
        [
            "npx", "remotion", "render",
            "VRealEpisode",
            str(output_path),
            "--props", str(props_path),
            "--frames", f"0-{total_frames}",
        ],
        cwd=str(video_dir),
        capture_output=True,
        text=True,
        timeout=1800,  # 30 minute timeout
    )

    if result.returncode != 0:
        raise Exception(f"Remotion render failed: {result.stderr[:500]}")

    return str(output_path)


async def assemble_video_creatomate(
    voiceover_url: str,
    scenes: list[dict],
    title: str,
) -> str:
    """
    Assemble video using Creatomate API (cloud fallback).
    Returns URL of the rendered video.
    """
    elements = []

    for scene in scenes:
        elements.append({
            "type": "video",
            "source": scene["url"],
            "trim_duration": scene.get("duration", 10),
        })

    elements.append({"type": "audio", "source": voiceover_url})
    elements.append({
        "type": "text", "text": title,
        "font_size": "8 vmin", "font_weight": "700",
        "color": "#ffffff", "background_color": "rgba(0,0,0,0.6)",
        "duration": 4,
    })

    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(
            "https://api.creatomate.com/v1/renders",
            headers={
                "Authorization": f"Bearer {CREATOMATE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"output_format": "mp4", "width": 1920, "height": 1080, "elements": elements},
        )
        resp.raise_for_status()
        data = resp.json()

    render_id = data[0]["id"] if isinstance(data, list) else data["id"]

    for _ in range(120):
        await asyncio.sleep(5)
        async with httpx.AsyncClient(timeout=30) as client:
            status_resp = await client.get(
                f"https://api.creatomate.com/v1/renders/{render_id}",
                headers={"Authorization": f"Bearer {CREATOMATE_API_KEY}"},
            )
            status_data = status_resp.json()
            if status_data.get("status") == "succeeded":
                return status_data["url"]
            if status_data.get("status") == "failed":
                raise Exception(f"Creatomate render failed: {status_data.get('error_message')}")

    raise Exception("Creatomate render timed out")


# --- Full Pipeline ---

async def generate_video_from_script(script: str, title: str) -> dict:
    """
    Full video generation pipeline:
    1. Parse script for spoken text + visual cues
    2. Generate voiceover via ElevenLabs
    3. Generate custom scenes via Kling AI (fall back to Pexels)
    4. Assemble video via Remotion (fall back to Creatomate)
    Returns {video_url, scenes_generated, sections_parsed, spoken_word_count, renderer}
    """
    from pathlib import Path

    parsed = parse_script_cues(script)

    # Generate voiceover
    audio_bytes = await generate_voiceover(parsed["full_spoken_text"])

    # Save voiceover to video/public for Remotion access
    video_dir = Path(__file__).resolve().parent.parent.parent.parent / "video"
    voiceover_path = video_dir / "public" / "voiceover" / "episode.mp3"
    voiceover_path.parent.mkdir(parents=True, exist_ok=True)
    voiceover_path.write_bytes(audio_bytes)

    # Generate scenes for all visual cues
    all_cues = []
    for section in parsed["sections"]:
        all_cues.extend(section["visuals"])

    scenes = await generate_scenes_for_cues(all_cues)

    # Download scene videos to video/public for Remotion access
    footage_dir = video_dir / "public" / "footage"
    footage_dir.mkdir(parents=True, exist_ok=True)
    for i, scene in enumerate(scenes):
        local_path = footage_dir / f"scene-{i}.mp4"
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.get(scene["url"])
            if resp.status_code == 200:
                local_path.write_bytes(resp.content)
                scene["local_path"] = str(local_path)

    # Try Remotion first (local render, full control)
    renderer = "remotion"
    try:
        video_url = await assemble_video_remotion(
            voiceover_path=str(voiceover_path),
            scenes=scenes,
            title=title,
        )
    except Exception:
        # Fall back to Creatomate (cloud render)
        renderer = "creatomate"
        video_url = await assemble_video_creatomate(
            voiceover_url=str(voiceover_path),
            scenes=scenes,
            title=title,
        )

    return {
        "video_url": video_url,
        "scenes_generated": [
            {"cue": s["cue"], "source": s.get("source", "unknown")}
            for s in scenes
        ],
        "sections_parsed": len(parsed["sections"]),
        "spoken_word_count": len(parsed["full_spoken_text"].split()),
        "renderer": renderer,
    }
