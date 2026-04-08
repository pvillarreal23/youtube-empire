"""
Thumbnail Generator — Ideogram AI + A/B Testing

Generates 3 thumbnail variants per episode for YouTube's Test & Compare feature.
Uses Ideogram AI V2 API for photorealistic text-on-image thumbnails.

Thumbnail psychology (research-backed):
  - Face with emotion → 2-3x higher CTR than text-only
  - High contrast colors → stands out in suggested sidebar
  - Max 4 words of text → readable at mobile size (120x90px)
  - Bright/saturated → outperforms muted tones in dark mode
  - Brand consistency → cyan accent + dark bg = V-Real AI identity

Usage:
  from app.services.thumbnail_generator import generate_thumbnails
  paths = generate_thumbnails("ep001", THUMBNAIL_CONFIG)
"""
from __future__ import annotations

import os
import time
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import httpx

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


# ── Configuration ────────────────────────────────────────────────────────────

IDEOGRAM_API_KEY = os.getenv("IDEOGRAM_API_KEY", "")
OUTPUT_BASE = os.getenv("ASSET_DIR", os.path.expanduser("~/youtube-empire/assets"))

# Ideogram API settings
IDEOGRAM_API_URL = "https://api.ideogram.ai/generate"
IDEOGRAM_MODEL = "V_2"
IDEOGRAM_ASPECT = "ASPECT_16_9"  # YouTube thumbnail = 1280x720 = 16:9

# V-Real AI brand constraints for thumbnails
BRAND_STYLE = {
    "bg": "very dark navy blue (#0A0F1E)",
    "accent": "electric cyan (#00D4FF)",
    "secondary": "warm amber (#FFB347)",
    "text_color": "bold white with cyan glow",
    "mood": "cinematic, dramatic, documentary",
    "font_style": "bold sans-serif, impact-style",
}


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class ThumbnailVariant:
    """A single thumbnail variant for A/B testing."""
    variant_id: str           # "A", "B", "C"
    prompt: str               # Ideogram prompt
    emphasis: str             # What this variant tests: "face", "text", "data"
    file_path: str = ""
    ideogram_url: str = ""
    generated: bool = False


@dataclass
class ThumbnailConfig:
    """Complete thumbnail generation specification for an episode."""
    episode_id: str
    title: str                # Episode title (for text overlays)
    hook_text: str            # Max 4 words shown on thumbnail
    subtitle_text: str = ""   # Optional smaller text
    emotion: str = "shock"    # "shock", "fear", "curiosity", "urgency"
    scene_description: str = ""  # What the background should show
    data_point: str = ""      # Key stat to display (e.g. "43%")
    variants: list[ThumbnailVariant] = field(default_factory=list)


# ── Prompt Engineering ───────────────────────────────────────────────────────

def build_thumbnail_prompts(config: ThumbnailConfig) -> list[ThumbnailVariant]:
    """
    Generate 3 A/B test variant prompts optimized for YouTube CTR.

    Variant A: Emotion-first (face + reaction)
    Variant B: Text-first (bold typography)
    Variant C: Data-first (shocking statistic)

    Research: YouTube's Test & Compare needs exactly 3 variants.
    The algorithm shows each to ~33% of impressions and picks the winner.
    """
    base_style = (
        f"Cinematic documentary style, {BRAND_STYLE['bg']} background, "
        f"{BRAND_STYLE['accent']} accent lighting, "
        f"dramatic shadows, ultra high quality, photorealistic, 4K detail, "
        f"YouTube thumbnail style, professional photography"
    )

    variants = []

    # Variant A: Emotion-driven (face + shock/concern expression)
    variants.append(ThumbnailVariant(
        variant_id="A",
        prompt=(
            f"Professional woman looking at phone screen with {config.emotion} expression, "
            f"office background with dramatic blue-cyan lighting, "
            f"bold white text overlay '{config.hook_text}' in top portion, "
            f"clean modern documentary aesthetic, "
            f"{base_style}"
        ),
        emphasis="face_emotion",
    ))

    # Variant B: Typography-dominant (bold text, minimal imagery)
    variants.append(ThumbnailVariant(
        variant_id="B",
        prompt=(
            f"Dark cinematic background with {config.scene_description or 'abstract tech visualization'}, "
            f"massive bold white text '{config.hook_text}' centered, "
            f"electric cyan (#00D4FF) underline glow effect, "
            f"{'smaller amber text: ' + config.subtitle_text if config.subtitle_text else ''}, "
            f"clean minimalist documentary thumbnail, "
            f"{base_style}"
        ),
        emphasis="text_dominant",
    ))

    # Variant C: Data shock (big number + context)
    data_text = config.data_point or config.hook_text
    variants.append(ThumbnailVariant(
        variant_id="C",
        prompt=(
            f"Split screen effect: left side shows person at desk looking worried, "
            f"right side shows large glowing '{data_text}' statistic in electric cyan, "
            f"dark background with red warning undertones, "
            f"small white text '{config.hook_text}' at bottom, "
            f"data visualization documentary style, "
            f"{base_style}"
        ),
        emphasis="data_shock",
    ))

    return variants


# ── Generation ───────────────────────────────────────────────────────────────

def generate_single_thumbnail(variant: ThumbnailVariant, output_path: str) -> bool:
    """
    Generate a single thumbnail via Ideogram AI API.

    Returns True if successful, False if failed.
    """
    if not IDEOGRAM_API_KEY:
        print(f"[THUMBNAIL] ERROR: IDEOGRAM_API_KEY not set in .env")
        print(f"[THUMBNAIL] Get yours at: https://ideogram.ai/manage-api")
        return False

    try:
        response = httpx.post(
            IDEOGRAM_API_URL,
            headers={
                "Api-Key": IDEOGRAM_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "image_request": {
                    "prompt": variant.prompt,
                    "model": IDEOGRAM_MODEL,
                    "aspect_ratio": IDEOGRAM_ASPECT,
                    "magic_prompt_option": "AUTO",
                    "style_type": "REALISTIC",
                }
            },
            timeout=60,
        )
    except (httpx.ProxyError, httpx.ConnectError) as e:
        print(f"[THUMBNAIL] ERROR: Cannot reach Ideogram API — network blocked")
        print(f"[THUMBNAIL] Generate manually at ideogram.ai with this prompt:")
        print(f"[THUMBNAIL]   {variant.prompt[:200]}...")
        return False

    if response.status_code != 200:
        print(f"[THUMBNAIL] ERROR: Ideogram returned {response.status_code}")
        print(f"[THUMBNAIL] {response.text[:200]}")
        return False

    data = response.json()
    images = data.get("data", [])
    if not images:
        print(f"[THUMBNAIL] ERROR: No images returned")
        return False

    # Download the image
    image_url = images[0].get("url", "")
    if not image_url:
        print(f"[THUMBNAIL] ERROR: No URL in response")
        return False

    img_response = httpx.get(image_url, timeout=30, follow_redirects=True)
    if img_response.status_code != 200:
        print(f"[THUMBNAIL] ERROR: Could not download image")
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(img_response.content)

    size_kb = len(img_response.content) / 1024
    variant.file_path = output_path
    variant.ideogram_url = image_url
    variant.generated = True

    print(f"[THUMBNAIL] ✓ Variant {variant.variant_id} saved: {output_path} ({size_kb:.0f} KB)")
    return True


def generate_thumbnails(
    episode_id: str,
    config: ThumbnailConfig,
    notify_make_fn=None,
) -> list[str]:
    """
    Generate 3 A/B test thumbnail variants for an episode.

    Args:
        episode_id:     e.g. "ep001"
        config:         ThumbnailConfig with hook text, emotion, etc.
        notify_make_fn: Optional Make.com notification function

    Returns: List of file paths to generated thumbnails.
    """
    output_dir = os.path.join(OUTPUT_BASE, episode_id, "thumbnails")
    os.makedirs(output_dir, exist_ok=True)

    print(f"[THUMBNAIL] Generating 3 A/B variants for {episode_id}...")
    print(f"[THUMBNAIL]   Hook text: '{config.hook_text}'")
    print(f"[THUMBNAIL]   Emotion: {config.emotion}")

    # Build prompts
    variants = build_thumbnail_prompts(config)
    config.variants = variants

    generated_paths = []

    for variant in variants:
        output_path = os.path.join(output_dir, f"{episode_id}-thumb-{variant.variant_id}.jpg")

        print(f"[THUMBNAIL] Generating variant {variant.variant_id} ({variant.emphasis})...")
        success = generate_single_thumbnail(variant, output_path)

        if success:
            generated_paths.append(output_path)
        else:
            print(f"[THUMBNAIL] WARNING: Variant {variant.variant_id} failed")

        # Rate limit between requests
        time.sleep(2)

    # Notify Make.com
    if notify_make_fn and generated_paths:
        notify_make_fn("thumbnail", {
            "status": "generated",
            "episode_id": episode_id,
            "variants": len(generated_paths),
            "paths": generated_paths,
            "prompts": [v.prompt[:200] for v in variants],
        })

    # Save config for reference
    config_path = os.path.join(output_dir, f"{episode_id}-thumbnail-config.json")
    with open(config_path, "w") as f:
        json.dump({
            "episode_id": episode_id,
            "hook_text": config.hook_text,
            "emotion": config.emotion,
            "variants": [
                {
                    "id": v.variant_id,
                    "emphasis": v.emphasis,
                    "prompt": v.prompt,
                    "file_path": v.file_path,
                    "generated": v.generated,
                }
                for v in variants
            ],
        }, f, indent=2)

    print(f"[THUMBNAIL] ✓ Generated {len(generated_paths)}/3 thumbnails")
    print(f"[THUMBNAIL]   Upload all 3 to YouTube Studio → Test & Compare")
    return generated_paths


# ── Episode Configs ──────────────────────────────────────────────────────────

EP001_THUMBNAILS = ThumbnailConfig(
    episode_id="ep001",
    title="Half Her Team Was Gone by 10 AM",
    hook_text="GONE BY 10 AM",
    subtitle_text="AI replaced them",
    emotion="shock",
    scene_description="empty office cubicles with blue-cyan computer screens glowing",
    data_point="3.2M",
)

EP002_THUMBNAILS = ThumbnailConfig(
    episode_id="ep002",
    title="The Price of Waiting",
    hook_text="TOO LATE",
    subtitle_text="90 days ran out",
    emotion="fear",
    scene_description="clock showing 11:59 with red warning overlay",
    data_point="43%",
)


# ── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate YouTube thumbnails via Ideogram AI")
    parser.add_argument("--episode", choices=["ep001", "ep002"], default="ep001")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without generating")
    args = parser.parse_args()

    configs = {"ep001": EP001_THUMBNAILS, "ep002": EP002_THUMBNAILS}
    config = configs[args.episode]

    if args.dry_run:
        variants = build_thumbnail_prompts(config)
        for v in variants:
            print(f"\n── Variant {v.variant_id} ({v.emphasis}) ──")
            print(v.prompt)
    else:
        paths = generate_thumbnails(args.episode, config)
        if paths:
            print(f"\nUpload these to YouTube Studio → Customization → Test & Compare:")
            for p in paths:
                print(f"  {p}")
