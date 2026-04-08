"""
Video generation service for V-Real AI.

Style: Documentary — AI voiceover + stock footage + text overlays + captions.

Pipeline:
  1. Parse script for sections, visual cues ([B-ROLL:], [GRAPHIC:], etc.)
  2. Generate voiceover via ElevenLabs
  3. Source stock footage via Pexels matching B-roll cues
  4. Assemble video via Creatomate (or Shotstack)
  5. Return video URL for YouTube upload
"""

from __future__ import annotations

import re
import json
import httpx
from app.config import ELEVENLABS_API_KEY, PEXELS_API_KEY, CREATOMATE_API_KEY


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
        sfx = re.findall(r'\[SFX:\s*(.+?)\]', line)
        music = re.findall(r'\[MUSIC:\s*(.+?)\]', line)

        if broll or graphic or screen or cut:
            for cue in broll:
                current_section["visuals"].append({"type": "b-roll", "description": cue})
            for cue in graphic:
                current_section["visuals"].append({"type": "graphic", "description": cue})
            for cue in screen:
                current_section["visuals"].append({"type": "screen-record", "description": cue})
            for cue in cut:
                current_section["visuals"].append({"type": "cut", "description": cue})

        # Section break detection
        if line.startswith("[SECTION") or line.startswith("[ACT") or line.startswith("[HOOK") or line.startswith("[CONCLUSION"):
            if current_section["text"]:
                sections.append(current_section)
                current_section = {"text": [], "visuals": []}
            continue

        # Clean line of cue brackets for spoken text
        clean = re.sub(r'\[.+?\]', '', line).strip()
        if clean and not clean.startswith("#"):
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


# --- Pexels Stock Footage ---

async def search_stock_footage(query: str, per_page: int = 3) -> list[dict]:
    """
    Search Pexels for stock video clips matching a description.
    Returns list of {url, width, height, duration} dicts.
    """
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
        # Get the HD file
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


async def get_footage_for_cues(visuals: list[dict]) -> list[dict]:
    """Get stock footage for each visual cue in a script section."""
    footage = []
    for cue in visuals:
        if cue["type"] == "b-roll":
            clips = await search_stock_footage(cue["description"])
            if clips:
                footage.append({**clips[0], "cue": cue["description"]})
    return footage


# --- Video Assembly via Creatomate ---

async def assemble_video(
    voiceover_url: str,
    footage_clips: list[dict],
    title: str,
    captions: list[dict] | None = None,
) -> str:
    """
    Assemble final video using Creatomate API.

    Takes voiceover audio + stock footage clips + text overlays
    and produces a final rendered video.

    Returns the URL of the rendered video.

    If you prefer Shotstack, swap the API call — same concept.
    """
    # Build Creatomate template elements
    elements = []

    # Background footage layer
    for i, clip in enumerate(footage_clips):
        elements.append({
            "type": "video",
            "source": clip["url"],
            "trim_duration": clip.get("duration", 10),
        })

    # Voiceover audio layer
    elements.append({
        "type": "audio",
        "source": voiceover_url,
    })

    # Title card
    elements.append({
        "type": "text",
        "text": title,
        "font_size": "8 vmin",
        "font_weight": "700",
        "color": "#ffffff",
        "background_color": "rgba(0,0,0,0.6)",
        "duration": 4,
    })

    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(
            "https://api.creatomate.com/v1/renders",
            headers={
                "Authorization": f"Bearer {CREATOMATE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "output_format": "mp4",
                "width": 1920,
                "height": 1080,
                "elements": elements,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    # Creatomate returns a render ID — poll for completion
    render_id = data[0]["id"] if isinstance(data, list) else data["id"]

    for _ in range(120):
        import asyncio
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
                raise Exception(f"Video render failed: {status_data.get('error_message')}")

    raise Exception("Video render timed out")


# --- Full Pipeline ---

async def generate_video_from_script(script: str, title: str) -> dict:
    """
    Full video generation pipeline:
    1. Parse script for spoken text + visual cues
    2. Generate voiceover
    3. Source stock footage
    4. Assemble video
    Returns {video_url, voiceover_url, footage_used}
    """
    parsed = parse_script_cues(script)

    # Generate voiceover
    audio_bytes = await generate_voiceover(parsed["full_spoken_text"])

    # For now, save audio and get URL (in production, upload to S3/GCS)
    # This is a placeholder — in production you'd upload to cloud storage
    voiceover_url = ""  # Replace with actual upload

    # Get stock footage for all visual cues
    all_cues = []
    for section in parsed["sections"]:
        all_cues.extend(section["visuals"])

    footage = await get_footage_for_cues(all_cues)

    # Assemble video
    video_url = await assemble_video(
        voiceover_url=voiceover_url,
        footage_clips=footage,
        title=title,
    )

    return {
        "video_url": video_url,
        "footage_used": [f["cue"] for f in footage],
        "sections_parsed": len(parsed["sections"]),
        "spoken_word_count": len(parsed["full_spoken_text"].split()),
    }
