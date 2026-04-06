"""
Footage Auto-Sourcing Service

Automatically finds and downloads stock footage and AI-generated clips
based on script scene descriptions. Eliminates 1-2 hours of manual
browsing per episode.

Sources (in priority order per production bible):
  1. Kling AI — custom AI-generated scenes (hero moments)
  2. Pexels Video — free cinematic stock footage
  3. Local asset library — previously downloaded/generated clips

Rules:
  - NEVER use photos as video (except Ken Burns as last resort)
  - Minimum 1080p resolution
  - No generic "person typing on laptop" footage
  - Cinematic quality: good lighting, smooth motion, professional grade
"""
from __future__ import annotations

import os
import json
import httpx
import asyncio
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


# ── Configuration ────────────────────────────────────────────────────────────

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
KLING_API_KEY = os.getenv("KLING_API_KEY", "")
KLING_REFERRAL = "7B4U73LULN88"

ASSET_DIR = os.getenv("ASSET_DIR", os.path.expanduser("~/youtube-empire/assets"))
FOOTAGE_DIR = os.path.join(ASSET_DIR, "footage")
KLING_DIR = os.path.join(ASSET_DIR, "kling-ai")
MUSIC_DIR = os.path.join(ASSET_DIR, "music")

# Banned footage keywords (generic, overused, off-brand)
BANNED_KEYWORDS = [
    "person typing laptop", "handshake business", "team meeting generic",
    "stock photo", "thumbs up", "pointing at screen", "celebrating office",
    "generic robot", "matrix code", "binary numbers falling",
]

# V-Real AI visual palette preferences
VISUAL_PREFERENCES = {
    "ai_moments": ["technology", "data", "digital", "circuit", "neural", "hologram", "code"],
    "human_moments": ["person", "city", "workplace", "creative", "contemplation", "morning"],
    "transformation": ["sunrise", "growth", "change", "evolution", "building", "construction"],
    "tension": ["storm", "dark", "clock", "deadline", "competition", "speed"],
    "hope": ["light", "sunrise", "path", "door", "horizon", "breakthrough"],
}


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class FootageResult:
    """A single footage search result."""
    source: str                  # "pexels", "kling_ai", "local"
    url: str                     # Download URL or local path
    preview_url: str = ""        # Preview/thumbnail URL
    width: int = 1920
    height: int = 1080
    duration: float = 0.0
    description: str = ""
    tags: list[str] = field(default_factory=list)
    license: str = ""
    quality_score: float = 0.0   # 0-1 relevance/quality score
    local_path: str = ""         # Path after download


@dataclass
class SceneFootageRequest:
    """Request to find footage for a script scene."""
    scene_number: int
    description: str             # From [ANIM:] or [KLING-AI:] tag in script
    duration_needed: float       # seconds
    mood: str = ""               # "tension", "hope", "discovery", "urgency"
    prefer_source: str = "any"   # "kling_ai", "pexels", "local", "any"
    keywords: list[str] = field(default_factory=list)


@dataclass
class FootagePackage:
    """Complete footage package for an episode."""
    episode_id: str
    scenes: list[dict] = field(default_factory=list)  # scene_num -> FootageResult
    total_clips: int = 0
    sources_used: dict = field(default_factory=dict)   # source -> count
    missing_scenes: list[int] = field(default_factory=list)


# ── Pexels API ───────────────────────────────────────────────────────────────

async def search_pexels_videos(
    query: str,
    per_page: int = 10,
    min_duration: int = 3,
    min_width: int = 1920,
    orientation: str = "landscape",
) -> list[FootageResult]:
    """
    Search Pexels for free stock video footage.
    Returns HD/4K cinematic clips matching the query.
    """
    if not PEXELS_API_KEY:
        print("[FOOTAGE] WARNING: PEXELS_API_KEY not set. Add to .env file.")
        return []

    # Filter out banned keywords
    for banned in BANNED_KEYWORDS:
        if banned.lower() in query.lower():
            print(f"[FOOTAGE] Filtered banned keyword from query: {banned}")
            query = query.replace(banned, "").strip()

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(
            "https://api.pexels.com/videos/search",
            params={
                "query": query,
                "per_page": per_page,
                "min_duration": min_duration,
                "min_width": min_width,
                "orientation": orientation,
            },
            headers={"Authorization": PEXELS_API_KEY},
        )

        if response.status_code != 200:
            print(f"[FOOTAGE] Pexels API error: {response.status_code}")
            return []

        data = response.json()
        results = []

        for video in data.get("videos", []):
            # Find the highest quality video file
            best_file = None
            for vf in video.get("video_files", []):
                if vf.get("width", 0) >= min_width and vf.get("quality") == "hd":
                    if not best_file or vf.get("width", 0) > best_file.get("width", 0):
                        best_file = vf

            if not best_file:
                # Fallback to any HD file
                for vf in video.get("video_files", []):
                    if vf.get("quality") == "hd":
                        best_file = vf
                        break

            if not best_file:
                continue

            results.append(FootageResult(
                source="pexels",
                url=best_file.get("link", ""),
                preview_url=video.get("image", ""),
                width=best_file.get("width", 1920),
                height=best_file.get("height", 1080),
                duration=video.get("duration", 0),
                description=video.get("url", ""),
                license="Pexels License (free for commercial use)",
                quality_score=0.7,  # Base score, adjusted by relevance
            ))

        return results


async def download_pexels_clip(result: FootageResult, save_dir: str, filename: str) -> str:
    """Download a Pexels video clip to local storage."""
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)

    if os.path.exists(save_path):
        return save_path

    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        response = await client.get(result.url)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"[FOOTAGE] ✓ Downloaded: {filename} ({len(response.content) / 1024 / 1024:.1f} MB)")
            return save_path

    print(f"[FOOTAGE] ✗ Failed to download: {result.url}")
    return ""


# ── Kling AI ─────────────────────────────────────────────────────────────────

async def generate_kling_clip(
    prompt: str,
    duration: float = 5.0,
    aspect_ratio: str = "16:9",
    save_dir: str = "",
    filename: str = "",
) -> FootageResult:
    """
    Generate a custom video clip using Kling AI.
    For hero moments that stock footage can't provide.

    Note: Kling AI's API availability varies. This integrates with their
    public API when available, otherwise returns a placeholder for manual generation.
    """
    save_dir = save_dir or KLING_DIR
    os.makedirs(save_dir, exist_ok=True)

    if not KLING_API_KEY:
        # Return a placeholder — user generates manually via Kling AI web
        return FootageResult(
            source="kling_ai",
            url="",
            description=f"[MANUAL] Generate in Kling AI: {prompt}",
            duration=duration,
            quality_score=1.0,
            tags=["kling_ai", "custom", "manual_generation"],
            local_path="",
        )

    # Kling AI API integration (when API key is available)
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            "https://api.klingai.com/v1/videos/generations",
            headers={
                "Authorization": f"Bearer {KLING_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "prompt": prompt,
                "duration": str(int(duration)),
                "aspect_ratio": aspect_ratio,
                "model": "kling-v1",
            },
        )

        if response.status_code == 200:
            result_data = response.json()
            video_url = result_data.get("data", {}).get("video_url", "")

            if video_url and filename:
                save_path = os.path.join(save_dir, filename)
                dl_response = await client.get(video_url)
                with open(save_path, "wb") as f:
                    f.write(dl_response.content)

                return FootageResult(
                    source="kling_ai",
                    url=video_url,
                    duration=duration,
                    description=prompt,
                    quality_score=1.0,
                    local_path=save_path,
                )

    return FootageResult(
        source="kling_ai",
        url="",
        description=f"[GENERATION FAILED] Prompt: {prompt}",
        duration=duration,
        quality_score=0.0,
    )


# ── Local Asset Library ──────────────────────────────────────────────────────

def search_local_footage(
    keywords: list[str],
    min_duration: float = 2.0,
) -> list[FootageResult]:
    """
    Search the local asset library for previously downloaded/generated clips.
    Checks filename and any sidecar JSON metadata files.
    """
    results = []
    footage_path = Path(FOOTAGE_DIR)

    if not footage_path.exists():
        return results

    video_extensions = {".mp4", ".mov", ".webm", ".avi", ".mkv"}

    for file in footage_path.rglob("*"):
        if file.suffix.lower() not in video_extensions:
            continue

        # Check filename against keywords
        name_lower = file.stem.lower().replace("-", " ").replace("_", " ")
        match_score = sum(1 for kw in keywords if kw.lower() in name_lower) / max(len(keywords), 1)

        # Check sidecar metadata
        meta_file = file.with_suffix(".json")
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                meta_tags = [t.lower() for t in meta.get("tags", [])]
                meta_desc = meta.get("description", "").lower()
                tag_score = sum(1 for kw in keywords if kw.lower() in meta_tags or kw.lower() in meta_desc) / max(len(keywords), 1)
                match_score = max(match_score, tag_score)
            except (json.JSONDecodeError, IOError):
                pass

        if match_score > 0.2:
            results.append(FootageResult(
                source="local",
                url=str(file),
                local_path=str(file),
                description=file.stem,
                quality_score=match_score,
            ))

    # Sort by relevance
    results.sort(key=lambda r: r.quality_score, reverse=True)
    return results


# ── Scene-to-Keywords Mapping ────────────────────────────────────────────────

def extract_search_keywords(scene_description: str, mood: str = "") -> list[str]:
    """
    Convert a script scene description into effective search keywords.

    Example:
      "[ANIM: Cinematic city skyline at dawn, warm tones, hopeful]"
      → ["city skyline dawn", "cinematic sunrise city", "urban morning light"]
    """
    # Strip animation tags
    clean = scene_description
    for tag in ["[ANIM:", "[KLING-AI:", "[TEXT-ON-SCREEN:", "[TRANSITION:", "]"]:
        clean = clean.replace(tag, "")
    clean = clean.strip()

    keywords = [clean]

    # Add mood-based keywords
    if mood and mood in VISUAL_PREFERENCES:
        keywords.extend(VISUAL_PREFERENCES[mood][:3])

    # Add "cinematic" qualifier for better stock footage results
    keywords.append(f"cinematic {clean.split(',')[0].strip()}")

    return keywords


# ── Main Auto-Sourcing Pipeline ──────────────────────────────────────────────

async def source_footage_for_episode(
    episode_id: str,
    scene_requests: list[SceneFootageRequest],
) -> FootagePackage:
    """
    Main pipeline: automatically find footage for all scenes in an episode.

    Strategy:
      1. Check local library first (free, instant)
      2. Search Pexels for stock footage (free, fast)
      3. Queue Kling AI for hero moments (costs credits, highest quality)

    Returns a FootagePackage with clips for each scene.
    """
    package = FootagePackage(episode_id=episode_id)
    episode_footage_dir = os.path.join(FOOTAGE_DIR, episode_id)
    os.makedirs(episode_footage_dir, exist_ok=True)

    sources_count = {"local": 0, "pexels": 0, "kling_ai": 0, "missing": 0}

    for req in scene_requests:
        print(f"[FOOTAGE] Scene {req.scene_number}: {req.description[:60]}...")

        keywords = extract_search_keywords(req.description, req.mood)
        if req.keywords:
            keywords = req.keywords + keywords

        best_result = None

        # ── Priority 1: Kling AI for custom scenes ───────────────────────
        if req.prefer_source == "kling_ai" or "[KLING-AI:" in req.description:
            kling_result = await generate_kling_clip(
                prompt=req.description.replace("[KLING-AI:", "").replace("]", "").strip(),
                duration=min(req.duration_needed, 10),
                save_dir=episode_footage_dir,
                filename=f"scene_{req.scene_number:02d}_kling.mp4",
            )
            if kling_result.local_path or kling_result.description.startswith("[MANUAL]"):
                best_result = kling_result
                sources_count["kling_ai"] += 1

        # ── Priority 2: Local asset library ──────────────────────────────
        if not best_result:
            local_results = search_local_footage(keywords, min_duration=req.duration_needed * 0.5)
            if local_results:
                best_result = local_results[0]
                sources_count["local"] += 1
                print(f"[FOOTAGE]   Found local: {best_result.local_path}")

        # ── Priority 3: Pexels stock footage ─────────────────────────────
        if not best_result:
            for keyword in keywords[:3]:  # Try top 3 keyword variations
                pexels_results = await search_pexels_videos(
                    query=keyword,
                    per_page=5,
                    min_duration=max(3, int(req.duration_needed)),
                )
                if pexels_results:
                    # Pick best result
                    best_pexels = max(pexels_results, key=lambda r: r.duration)

                    # Download it
                    local_path = await download_pexels_clip(
                        best_pexels,
                        episode_footage_dir,
                        f"scene_{req.scene_number:02d}_pexels.mp4",
                    )
                    if local_path:
                        best_pexels.local_path = local_path
                        best_result = best_pexels
                        sources_count["pexels"] += 1
                        break

                # Small delay between API calls
                await asyncio.sleep(0.5)

        # ── Record result ────────────────────────────────────────────────
        if best_result:
            package.scenes.append({
                "scene_number": req.scene_number,
                "source": best_result.source,
                "local_path": best_result.local_path,
                "description": best_result.description,
                "quality_score": best_result.quality_score,
                "duration": best_result.duration,
                "needs_manual": best_result.description.startswith("[MANUAL]"),
            })
            package.total_clips += 1
        else:
            package.missing_scenes.append(req.scene_number)
            sources_count["missing"] += 1
            print(f"[FOOTAGE]   ✗ No footage found for scene {req.scene_number}")

    package.sources_used = sources_count

    # Summary
    print(f"\n[FOOTAGE] ═══ Episode {episode_id} Footage Package ═══")
    print(f"[FOOTAGE] Total clips: {package.total_clips}/{len(scene_requests)}")
    print(f"[FOOTAGE] Sources: {json.dumps(sources_count)}")
    if package.missing_scenes:
        print(f"[FOOTAGE] Missing scenes: {package.missing_scenes}")
    print(f"[FOOTAGE] Footage saved to: {episode_footage_dir}")

    # Save package manifest
    manifest_path = os.path.join(episode_footage_dir, "footage_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump({
            "episode_id": episode_id,
            "scenes": package.scenes,
            "sources_used": package.sources_used,
            "missing_scenes": package.missing_scenes,
        }, f, indent=2)

    return package
