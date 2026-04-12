#!/usr/bin/env python3
"""EP001 — "The Shift" — Full Production Runner

End-to-end production script that generates voiceover, AI footage,
music, and assembles the final video for YouTube upload.

Usage:
    python produce_ep001.py [--step STEP] [--skip-voice] [--skip-footage] [--dry-run]

Steps:
    1. Generate voiceover (ElevenLabs — Julian voice)
    2. Generate B-roll footage (Kling AI via fal.ai + Pexels fallback)
    2.5. Source background music
    3. Assemble video (18-step pipeline)
    4. Upload to YouTube (unlisted for review)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path

import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

EPISODE_ID = "ep001"
EPISODE_TITLE = "EP001 — The Shift"
CHANNEL = "V-Real AI"

OUTPUT_DIR = Path("output/ep001")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VOICE_DIR = OUTPUT_DIR / "voice"
VOICE_DIR.mkdir(exist_ok=True)
VISUALS_DIR = OUTPUT_DIR / "visuals"
VISUALS_DIR.mkdir(exist_ok=True)
MUSIC_DIR = OUTPUT_DIR / "music"
MUSIC_DIR.mkdir(exist_ok=True)

# ElevenLabs settings (LOCKED)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = "CJK4w2V6sbgFJY05zTGt"  # Julian — Deep, Rich and Mature
ELEVENLABS_MODEL = "eleven_multilingual_v2"
VOICE_SETTINGS = {
    "stability": 0.65,
    "similarity_boost": 0.75,
    "style": 0.0,
    "use_speaker_boost": False,
}

# fal.ai settings
FAL_API_KEY = os.getenv("FAL_API_KEY", "")

# YouTube metadata
YOUTUBE_TITLE = "9 Years of Skill. Replaced in 20 Minutes. [AI Documentary 2026]"
YOUTUBE_DESCRIPTION = """No one sent an announcement. No one rang a bell. The rules just changed.

A designer in Austin spent 9 years mastering her craft. Then a client sent one message: "We used an AI tool and got something we're happy with."

This is what happened next — and why it matters for everyone.

📌 CHAPTERS:
0:00 — The Shift
0:45 — Mara's Story
3:00 — Intelligence Without Taste
4:15 — The New Business Model
5:00 — It's Happening Everywhere
6:15 — The Window Is Still Open
7:30 — This Is V-Real AI

🔗 TOOLS WE USE:
• AI Video: Kling AI (referral link in pinned comment)
• Voiceover: ElevenLabs
• Music: Epidemic Sound

📧 Newsletter: [Coming soon]

—
V-Real AI — You're not paranoid. You're observant.

#ai #artificialintelligence #aidocumentary #thefutureofwork #aitools #technology2026
"""

YOUTUBE_TAGS = [
    "AI", "artificial intelligence", "AI documentary", "future of work",
    "AI tools", "AI design", "AI replacing jobs", "AI transformation",
    "technology documentary", "faceless youtube", "AI voiceover",
    "Kling AI", "ElevenLabs", "AI video", "graphic design AI",
    "career AI", "AI automation", "AI freelancer", "Midjourney",
    "AI professionals", "AI 2026", "the shift AI", "V-Real AI",
    "documentary 2026", "AI taste", "creative direction AI",
]

# ---------------------------------------------------------------------------
# Script Blocks (EP001 v8-FINAL)
# ---------------------------------------------------------------------------

# Script blocks from ep001-the-shift-v10.md (LOCKED — Mara's story)
SCRIPT_BLOCKS = [
    {
        "id": "block_1_hook",
        "title": "Hook + The Shift",
        "timestamp": "0:00-0:45",
        "text": (
            "No one sent an announcement. No one rang a bell. "
            "The rules just changed. "
            "Not gradually. Not eventually. All at once. "
            "Half the tasks that used to take years to master — "
            "writing, designing, coding, analyzing — "
            "they no longer require mastery of execution. "
            "They require taste. "
            "The barrier to entry didn't just lower. It evaporated."
        ),
    },
    {
        "id": "block_2_mara_intro",
        "title": "Mara's Story — The Designer",
        "timestamp": "0:45-3:00",
        "text": (
            "Six months ago, a designer in Austin — "
            "let's call her Mara — "
            "was billing forty hours a week for brand packages. "
            "Logo. Colors. Typography. Mockups. "
            "She was good. She'd been doing it for nine years. "
            "Then one of her clients sent a message. "
            "Polite. Almost apologetic. "
            "We used an AI tool and got something we're happy with. "
            "Nine years of craft. Replaced by a prompt and twenty minutes. "
            "Now here's where most people think this story goes. "
            "She panics. She pivots. She learns to code or starts a podcast about reinvention. "
            "That's not what happened."
        ),
    },
    {
        "id": "block_3_mara_pivot",
        "title": "Intelligence Without Taste",
        "timestamp": "3:00-4:15",
        "text": (
            "Mara spent two weeks learning every AI design tool she could find. "
            "Midjourney. Adobe Firefly. Figma's AI features. Runway. "
            "Not as replacements. As raw material. "
            "She realized something that most people still haven't figured out. "
            "The tools can execute. They have the intelligence. "
            "But they can't choose. "
            "They don't have taste. "
            "They don't have judgment. "
            "They don't know what actually matters."
        ),
    },
    {
        "id": "block_4_new_model",
        "title": "The New Business Model",
        "timestamp": "4:15-5:00",
        "text": (
            "Mara stopped selling forty-hour brand packages. "
            "She started selling creative direction — powered by AI. "
            "Same clients. Higher rates. "
            "A three thousand dollar brand package became a seven thousand five hundred dollar strategy engagement "
            "that she delivered in a third of the time. "
            "Not because she worked harder. "
            "Not because she learned a secret. "
            "Because she understood the shift before her competition did."
        ),
    },
    {
        "id": "block_5_everywhere",
        "title": "It's Happening Everywhere",
        "timestamp": "5:00-6:15",
        "text": (
            "And this is the part that keeps me up at night. "
            "Because what happened to Mara? It's happening everywhere. "
            "To writers. To developers. To marketers. "
            "To analysts, consultants, and project managers. "
            "Not in five years. Not in some theoretical future boardroom. "
            "Right now. This quarter. This month. "
            "And here's what nobody's saying out loud. "
            "The gap between people who adapted early "
            "and people who are just starting to notice? "
            "It's already enormous. "
            "Not because the early ones are smarter. "
            "Not because they work harder. "
            "Because they adapted sooner. "
            "And catching up is harder than starting early ever was."
        ),
    },
    {
        "id": "block_6_window",
        "title": "The Window Is Still Open",
        "timestamp": "6:15-7:30",
        "text": (
            "But here's the thing about this moment. "
            "The window is still open. "
            "Not wide open. Not forever. "
            "But if you're hearing this — you're early enough. "
            "The tools that Mara used? They're available to you right now. "
            "Most of them cost less than your streaming subscriptions. "
            "A fifty dollar a month stack can do what a five thousand dollar a month team did two years ago. "
            "The question isn't whether AI will change your work. "
            "That's already settled. "
            "The question is whether you'll be the one directing it — "
            "or the one it replaces."
        ),
    },
    {
        "id": "block_7_close",
        "title": "This Is V-Real AI",
        "timestamp": "7:30-9:00",
        "text": (
            "This channel exists for the people who choose to move. "
            "No fluff. No theory. Just leverage. "
            "Every week we break down what's actually changing, "
            "what tools are actually worth your time, "
            "and how the people who are winning right now are doing it. "
            "If that's you — subscribe. "
            "Because next week, we're going deeper. "
            "You're not paranoid. You're observant. "
            "This is V-Real AI."
        ),
    },
]

# ---------------------------------------------------------------------------
# Scene Descriptions (14 Scenes for Kling AI)
# ---------------------------------------------------------------------------

# Scene descriptions matched to ep001-the-shift-v10.md (14 animation scenes)
SCENE_FOOTAGE = [
    {
        "scene": 1,
        "description": "Black void with neural pathways igniting in darkness, lines of light branching like synapses",
        "camera": "Slow push in through digital void",
        "duration": 12,
        "mood": "ominous, anticipation — opening",
    },
    {
        "scene": 2,
        "description": "Neural pathways accelerating, branching and multiplying exponentially, filling frame with light",
        "camera": "Camera pulls back as scale becomes overwhelming",
        "duration": 10,
        "mood": "overwhelming, exponential",
    },
    {
        "scene": 3,
        "description": "Human figure made of light standing at crossroads, two paths stretching ahead — one bright, one dimming",
        "camera": "Wide establishing shot, symmetric composition",
        "duration": 10,
        "mood": "choice, metaphorical",
    },
    {
        "scene": 4,
        "description": "Woman designer at desk, 4 AM warm light through window, two monitors, coffee, deeply focused",
        "camera": "Slow orbit around subject, intimate",
        "duration": 12,
        "mood": "determination, warmth — Mara's introduction",
    },
    {
        "scene": 5,
        "description": "Chat message notification appearing on screen, glowing softly against dark interface",
        "camera": "Close-up push in on screen, shallow depth of field",
        "duration": 8,
        "mood": "tension, loss — the message",
    },
    {
        "scene": 6,
        "description": "Time-lapse of designer's screen filling with AI experiments, tools and designs flowing across monitors",
        "camera": "Slow orbit, accelerating time-lapse",
        "duration": 12,
        "mood": "transformation, intensity — Mara learning AI",
    },
    {
        "scene": 7,
        "description": "Abstract visualization: rivers of AI output being shaped and directed by human hands, curating the exceptional",
        "camera": "Cinematic slow motion, depth layers",
        "duration": 10,
        "mood": "empowerment, revelation — taste over execution",
    },
    {
        "scene": 8,
        "description": "Hands reaching into streams of AI output, selecting only exceptional pieces and discarding mediocre ones",
        "camera": "Close-up with shallow depth of field",
        "duration": 8,
        "mood": "decisive, quality — creative direction",
    },
    {
        "scene": 9,
        "description": "Animated bar chart: old revenue ($3K) vs new revenue ($7.5K), time bar shrinking to one-third",
        "camera": "Data visualization, clean motion graphics",
        "duration": 10,
        "mood": "proof, data-driven — the results",
    },
    {
        "scene": 10,
        "description": "Dark map with thousands of glowing nodes, each representing someone at the AI crossroads, most standing still",
        "camera": "Slow pull back revealing massive scale",
        "duration": 12,
        "mood": "vast, sobering — the global picture",
    },
    {
        "scene": 11,
        "description": "Chain reaction across the map: clusters lighting up as each profession is named — writers, developers, marketers",
        "camera": "Dynamic tracking across the map surface",
        "duration": 10,
        "mood": "urgent, spreading — it's everywhere",
    },
    {
        "scene": 12,
        "description": "Two nodes side by side: one moving forward growing brighter, one frozen dimming — the gap widening",
        "camera": "Split focus, contrast composition",
        "duration": 10,
        "mood": "contrast, warning — the enormous gap",
    },
    {
        "scene": 13,
        "description": "Dimming nodes re-brightening slowly, one by one, ripple of light spreading — hope returning",
        "camera": "Wide shot with slow push in as light spreads",
        "duration": 10,
        "mood": "hope, possibility — the window is open",
    },
    {
        "scene": 14,
        "description": "Figure from opening steps forward onto bright path, dissolves into particles that reform as V-Real AI logo",
        "camera": "Cinematic wide to close, particle transformation",
        "duration": 10,
        "mood": "resolution, brand — closing shot",
    },
]

# ---------------------------------------------------------------------------
# Video Assembly Configuration
# ---------------------------------------------------------------------------

TEXT_OVERLAYS = [
    {"text": "The barrier evaporated.", "timestamp": "0:30"},
    {"text": "9 years. 20 minutes.", "timestamp": "1:45"},
    {"text": "Intelligence without taste is noise.", "timestamp": "3:30"},
    {"text": "$3,000 → $7,500 | One-third the time", "timestamp": "4:30"},
    {"text": "The gap is already enormous.", "timestamp": "5:45"},
    {"text": "$50/month = what $5,000/month bought in 2024", "timestamp": "6:45"},
    {"text": "You're not paranoid. You're observant.", "timestamp": "8:15"},
]

LOWER_THIRDS = [
    # v10 uses "Mara" as a pseudonym — no formal lower third needed
    # but adding subtle context text for key moments
]

CHAPTERS = [
    {"time": "0:00", "title": "The Shift"},
    {"time": "0:45", "title": "Mara's Story"},
    {"time": "3:00", "title": "Intelligence Without Taste"},
    {"time": "4:15", "title": "The New Business Model"},
    {"time": "5:00", "title": "It's Happening Everywhere"},
    {"time": "6:15", "title": "The Window Is Still Open"},
    {"time": "7:30", "title": "This Is V-Real AI"},
]


# ---------------------------------------------------------------------------
# Step 1: Voiceover Generation (ElevenLabs)
# ---------------------------------------------------------------------------


async def generate_voiceover(dry_run: bool = False) -> Path | None:
    """Generate all voiceover blocks using ElevenLabs API."""
    logger.info("=" * 60)
    logger.info("STEP 1: VOICEOVER GENERATION (ElevenLabs)")
    logger.info("=" * 60)

    if not ELEVENLABS_API_KEY:
        logger.error("ELEVENLABS_API_KEY not set — skipping voiceover generation")
        return None

    if dry_run:
        logger.info("[DRY RUN] Would generate %d voiceover blocks", len(SCRIPT_BLOCKS))
        return None

    block_files = []

    async with httpx.AsyncClient(timeout=120) as client:
        for block in SCRIPT_BLOCKS:
            logger.info(f"Generating: {block['title']} ({block['timestamp']})")
            output_file = VOICE_DIR / f"{block['id']}.mp3"

            try:
                resp = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
                    headers={
                        "xi-api-key": ELEVENLABS_API_KEY,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": block["text"],
                        "model_id": ELEVENLABS_MODEL,
                        "voice_settings": VOICE_SETTINGS,
                    },
                )
                resp.raise_for_status()

                output_file.write_bytes(resp.content)
                logger.info(f"  Saved: {output_file} ({len(resp.content) / 1024:.1f} KB)")
                block_files.append(output_file)

            except Exception as e:
                logger.error(f"  Failed: {e}")
                continue

    # Concatenate all blocks
    if block_files:
        final_voice = VOICE_DIR / "ep001_voiceover_full.mp3"
        concat_list = VOICE_DIR / "concat.txt"
        with open(concat_list, "w") as f:
            for bf in block_files:
                f.write(f"file '{bf.absolute()}'\n")

        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
             "-c", "copy", str(final_voice)],
            capture_output=True,
        )
        logger.info(f"Final voiceover: {final_voice}")
        return final_voice

    return None


# ---------------------------------------------------------------------------
# Step 2: B-Roll Footage (Kling AI via fal.ai)
# ---------------------------------------------------------------------------


async def generate_footage(dry_run: bool = False) -> list[Path]:
    """Generate all B-roll footage using Kling AI via fal.ai."""
    logger.info("=" * 60)
    logger.info("STEP 2: B-ROLL FOOTAGE (Kling AI via fal.ai)")
    logger.info("=" * 60)

    if not FAL_API_KEY:
        logger.error("FAL_API_KEY not set — skipping footage generation")
        return []

    if dry_run:
        logger.info("[DRY RUN] Would generate %d scenes", len(SCENE_FOOTAGE))
        return []

    # Import from our AI media generator service
    sys.path.insert(0, str(Path(__file__).parent / "backend"))
    from app.services.ai_media_generator import SceneSpec, generate_episode_media

    scenes = [
        SceneSpec(
            scene_number=s["scene"],
            description=s["description"],
            visual_type="ai_video",
            duration=s["duration"],
            camera_motion=s["camera"],
            mood=s["mood"],
        )
        for s in SCENE_FOOTAGE
    ]

    result = await generate_episode_media(scenes=scenes, episode_id=EPISODE_ID, max_concurrent=3)

    logger.info(f"Generated {len(result.assets)} scenes, ${result.total_cost:.2f} total")
    if result.errors:
        logger.warning(f"Errors: {result.errors}")

    # Download assets to local directory
    footage_files = []
    async with httpx.AsyncClient(timeout=60) as client:
        for i, asset in enumerate(result.assets):
            if asset.url:
                output_file = VISUALS_DIR / f"scene_{i + 1:02d}.mp4"
                try:
                    resp = await client.get(asset.url)
                    resp.raise_for_status()
                    output_file.write_bytes(resp.content)
                    footage_files.append(output_file)
                    logger.info(f"  Downloaded scene {i + 1}: {output_file}")
                except Exception as e:
                    logger.error(f"  Failed to download scene {i + 1}: {e}")

    return footage_files


# ---------------------------------------------------------------------------
# Step 2.5: Background Music
# ---------------------------------------------------------------------------


async def source_music(dry_run: bool = False) -> Path | None:
    """Source background music for the episode."""
    logger.info("=" * 60)
    logger.info("STEP 2.5: BACKGROUND MUSIC")
    logger.info("=" * 60)

    if dry_run:
        logger.info("[DRY RUN] Would source cinematic documentary music")
        return None

    # Generate ambient pad as fallback using FFmpeg
    music_file = MUSIC_DIR / "ep001_ambient.wav"
    logger.info("Generating ambient pad with FFmpeg (fallback)")

    # Generate a dark cinematic drone/pad
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "anoisesrc=d=600:c=pink:r=48000:a=0.02",
            "-af", (
                "lowpass=f=200,"
                "highpass=f=40,"
                "afade=t=in:st=0:d=3,"
                "afade=t=out:st=597:d=3,"
                "volume=-30dB"
            ),
            str(music_file),
        ],
        capture_output=True,
    )

    if music_file.exists():
        logger.info(f"Music: {music_file}")
        return music_file

    logger.warning("Music generation failed")
    return None


# ---------------------------------------------------------------------------
# Step 3: Video Assembly
# ---------------------------------------------------------------------------


def assemble_video(
    voiceover: Path | None,
    footage: list[Path],
    music: Path | None,
    dry_run: bool = False,
) -> Path | None:
    """Assemble final video using the 18-step pipeline."""
    logger.info("=" * 60)
    logger.info("STEP 3: VIDEO ASSEMBLY (18-Step Pipeline)")
    logger.info("=" * 60)

    if dry_run:
        logger.info("[DRY RUN] Would assemble video with %d scenes", len(footage))
        return None

    if not footage:
        logger.error("No footage available — cannot assemble")
        return None

    sys.path.insert(0, str(Path(__file__).parent / "backend"))
    from app.services.video_assembler import (
        AssemblyConfig,
        AudioLayer,
        VisualSegment,
        assemble_video as run_assembly,
    )

    # Build visual segments
    visual_segments = []
    for i, f in enumerate(footage):
        scene_data = SCENE_FOOTAGE[i] if i < len(SCENE_FOOTAGE) else {}
        visual_segments.append(
            VisualSegment(
                file_path=str(f),
                start_time=0,
                duration=scene_data.get("duration", 10),
                segment_type="video",
                transition_in="fade" if i == 0 else "cut",
                ken_burns=False,
            )
        )

    # Build audio layers
    audio_layers = []
    if voiceover and voiceover.exists():
        audio_layers.append(
            AudioLayer(
                file_path=str(voiceover),
                layer_type="voice",
                target_lufs=-14.0,
            )
        )
    if music and music.exists():
        audio_layers.append(
            AudioLayer(
                file_path=str(music),
                layer_type="music",
                target_lufs=-28.0,
                duck_under_voice=True,
                duck_amount_db=-8.0,
            )
        )

    config = AssemblyConfig(
        episode_id=EPISODE_ID,
        title="The Shift",
        channel=CHANNEL,
        visual_segments=visual_segments,
        resolution=(1920, 1080),
        fps=24,
        audio_layers=audio_layers,
        target_lufs=-14.0,
        true_peak=-1.0,
        codec="libx264",
        preset="slow",
        crf=18,
        metadata={
            "title": YOUTUBE_TITLE,
            "artist": "V-Real AI",
            "comment": "Produced by V-Real AI agent pipeline",
        },
    )

    output_path = run_assembly(config)

    if output_path:
        logger.info(f"Final video: {output_path}")
        return Path(output_path)

    logger.error("Assembly failed")
    return None


# ---------------------------------------------------------------------------
# Step 4: YouTube Upload Metadata
# ---------------------------------------------------------------------------


def prepare_upload_metadata() -> dict:
    """Prepare YouTube upload metadata."""
    logger.info("=" * 60)
    logger.info("STEP 4: YOUTUBE UPLOAD METADATA")
    logger.info("=" * 60)

    metadata = {
        "title": YOUTUBE_TITLE,
        "description": YOUTUBE_DESCRIPTION,
        "tags": YOUTUBE_TAGS,
        "category": "27",  # Education
        "privacy_status": "unlisted",  # Review before making public
        "chapters": CHAPTERS,
        "pinned_comment": (
            "Is AI making your job easier... or making you replaceable? "
            "Drop your honest answer below. No judgment."
        ),
        "seo_filename": "9-years-of-skill-replaced-in-20-minutes-ai-documentary-2026.mp4",
    }

    # Save metadata to file
    metadata_file = OUTPUT_DIR / "youtube_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved: {metadata_file}")

    return metadata


# ---------------------------------------------------------------------------
# Step 5: Shorts Extraction
# ---------------------------------------------------------------------------

# Timestamps for best Shorts clips (9:16 vertical, 15-60 seconds)
SHORTS_CLIPS = [
    {
        "id": "short_1_hook",
        "title": "9 Years of Skill Replaced in 20 Minutes #ai #shorts",
        "start": "0:00",
        "end": "0:30",
        "hook_text": "9 years. 20 minutes.",
    },
    {
        "id": "short_2_taste",
        "title": "AI Has Intelligence But Not This #ai #shorts",
        "start": "3:00",
        "end": "3:45",
        "hook_text": "Intelligence without taste is noise.",
    },
    {
        "id": "short_3_revenue",
        "title": "$3K to $7.5K — How She Did It With AI #ai #shorts",
        "start": "4:15",
        "end": "4:55",
        "hook_text": "$3,000 → $7,500",
    },
    {
        "id": "short_4_gap",
        "title": "The Gap Is Already Enormous #ai #shorts",
        "start": "5:20",
        "end": "5:55",
        "hook_text": "The gap is already enormous.",
    },
    {
        "id": "short_5_window",
        "title": "$50/Month Does What $5K Used To #ai #shorts",
        "start": "6:30",
        "end": "7:10",
        "hook_text": "$50/month = $5,000 in 2024",
    },
]


def extract_shorts(video_path: Path | None, dry_run: bool = False) -> list[Path]:
    """Extract vertical Shorts clips from the main video."""
    logger.info("=" * 60)
    logger.info("STEP 5: SHORTS EXTRACTION (9:16 Vertical)")
    logger.info("=" * 60)

    if dry_run:
        logger.info("[DRY RUN] Would extract %d Shorts clips", len(SHORTS_CLIPS))
        return []

    if not video_path or not video_path.exists():
        logger.error("No video file to extract Shorts from")
        return []

    shorts_dir = OUTPUT_DIR / "shorts"
    shorts_dir.mkdir(exist_ok=True)
    extracted = []

    for clip in SHORTS_CLIPS:
        output_file = shorts_dir / f"{clip['id']}.mp4"
        logger.info(f"Extracting: {clip['title']} ({clip['start']}-{clip['end']})")

        # Convert timestamp to seconds
        def ts_to_sec(ts: str) -> float:
            parts = ts.split(":")
            return int(parts[0]) * 60 + float(parts[1])

        start_sec = ts_to_sec(clip["start"])
        duration_sec = ts_to_sec(clip["end"]) - start_sec

        # Extract and reformat to 9:16 vertical with caption overlay
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-ss", str(start_sec),
                "-i", str(video_path),
                "-t", str(duration_sec),
                "-vf", (
                    "crop=ih*9/16:ih,"  # Center crop to 9:16
                    "scale=1080:1920,"
                    f"drawtext=text='{clip['hook_text']}':"
                    "fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                    "fontsize=64:fontcolor=white:borderw=3:bordercolor=black:"
                    "x=(w-text_w)/2:y=h*0.75:enable='between(t,0,3)'"
                ),
                "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                "-c:a", "aac", "-b:a", "192k",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and output_file.exists():
            extracted.append(output_file)
            logger.info(f"  Saved: {output_file}")
        else:
            logger.warning(f"  Failed: {result.stderr[:200] if result.stderr else 'unknown error'}")

    logger.info(f"Extracted {len(extracted)}/{len(SHORTS_CLIPS)} Shorts")

    # Save shorts metadata
    shorts_meta = OUTPUT_DIR / "shorts_metadata.json"
    with open(shorts_meta, "w") as f:
        json.dump(SHORTS_CLIPS, f, indent=2)

    return extracted


# ---------------------------------------------------------------------------
# Step 6: Post-Publish Monitoring
# ---------------------------------------------------------------------------


def generate_post_publish_checklist() -> dict:
    """Generate the post-publish monitoring checklist and debrief template."""
    logger.info("=" * 60)
    logger.info("STEP 6: POST-PUBLISH MONITORING CHECKLIST")
    logger.info("=" * 60)

    checklist = {
        "episode": EPISODE_ID,
        "title": YOUTUBE_TITLE,
        "first_30_min": [
            "Share to Twitter with hook line + link",
            "Share to LinkedIn with professional angle",
            "Share to Instagram story with key visual",
            "Pin comment with engagement question",
        ],
        "first_hour": [
            "Heart first 20-30 comments",
            "Reply to every early comment",
            "Check initial view velocity",
        ],
        "at_24_hours": [
            "Check CTR — if below 4%, consider thumbnail swap",
            "Check average view duration — target 40%+",
            "Check subscriber conversion rate",
            "Review top traffic source",
            "Post community tab teaser for next episode",
        ],
        "at_48_hours": [
            "Complete EPISODE_DEBRIEF_LOG.md entry",
            "Record: views, CTR, AVD, AVD%, subs gained",
            "Identify biggest drop-off point + hypothesis",
            "Document 3 things to do differently next episode",
            "Document 3 things to keep / double down on",
            "Confirm Shorts distributed (5 clips to YT/TikTok/Reels)",
        ],
        "distribution_checklist": [
            "[ ] YouTube (full episode)",
            "[ ] YouTube Shorts (5 clips)",
            "[ ] TikTok (re-formatted clips)",
            "[ ] Instagram Reels (re-formatted clips)",
            "[ ] LinkedIn (professional angle post)",
            "[ ] Twitter/X (hook + link)",
            "[ ] Newsletter (episode summary)",
        ],
        "benchmarks": {
            "target_ctr": "6-10% (early channel)",
            "target_avd_pct": "40%+",
            "target_subs_conversion": "1-3%",
            "thumbnail_swap_threshold": "CTR < 4% at 24h",
        },
    }

    checklist_file = OUTPUT_DIR / "post_publish_checklist.json"
    with open(checklist_file, "w") as f:
        json.dump(checklist, f, indent=2)
    logger.info(f"Checklist saved: {checklist_file}")

    return checklist


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main():
    parser = argparse.ArgumentParser(description="EP001 Production Runner")
    parser.add_argument("--step", type=int, help="Run only a specific step (1-6)")
    parser.add_argument("--skip-voice", action="store_true", help="Skip voiceover generation")
    parser.add_argument("--skip-footage", action="store_true", help="Skip footage generation")
    parser.add_argument("--dry-run", action="store_true", help="Preview without generating")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"V-REAL AI — {EPISODE_TITLE}")
    logger.info("Full Production Runner (Steps 1-6)")
    logger.info("=" * 60)

    voiceover = None
    footage = []
    music = None
    final_video = None

    # Step 1: Voiceover
    if not args.skip_voice and (args.step is None or args.step == 1):
        voiceover = await generate_voiceover(dry_run=args.dry_run)

    # Step 2: Footage
    if not args.skip_footage and (args.step is None or args.step == 2):
        footage = await generate_footage(dry_run=args.dry_run)

    # Step 2.5: Music
    if args.step is None or args.step == 2:
        music = await source_music(dry_run=args.dry_run)

    # Step 3: Assembly
    if args.step is None or args.step == 3:
        final_video = assemble_video(voiceover, footage, music, dry_run=args.dry_run)

    # Step 4: Upload metadata
    if args.step is None or args.step == 4:
        prepare_upload_metadata()

    # Step 5: Shorts extraction
    if args.step is None or args.step == 5:
        # Try to find the assembled video if we didn't just build it
        if not final_video:
            candidate = Path("output/assembled/ep001_final.mp4")
            if candidate.exists():
                final_video = candidate
        extract_shorts(final_video, dry_run=args.dry_run)

    # Step 6: Post-publish monitoring checklist
    if args.step is None or args.step == 6:
        generate_post_publish_checklist()

    logger.info("=" * 60)
    logger.info("PRODUCTION COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info("Next steps:")
    logger.info("  1. Review assembled video")
    logger.info("  2. Generate thumbnail (3 concepts)")
    logger.info("  3. Upload to YouTube (unlisted)")
    logger.info("  4. Review and make public")
    logger.info("  5. Execute first-48h launch strategy")


if __name__ == "__main__":
    asyncio.run(main())
