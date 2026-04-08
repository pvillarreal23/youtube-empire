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
YOUTUBE_TITLE = "Half Her Team Was Gone by 10 AM [AI Documentary 2026]"
YOUTUBE_DESCRIPTION = """Something changed in 2025. Not gradually — overnight.

Sarah Chen walked into her marketing department on a Tuesday morning. By 10 AM, half her team's roles had been automated. Not because they were bad at their jobs — because the tools got that good, that fast.

This is the story of what happened next. Not just to Sarah — but to millions of professionals who woke up one morning and realized the rules had changed.

📌 CHAPTERS:
0:00 — The Morning Everything Changed
0:45 — What Sarah Saw
1:30 — The New Rules
3:15 — Mike's Warning
4:45 — David's Playbook
6:00 — The 90-Day Rule
7:30 — What The Data Says
8:30 — You're Not Paranoid

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
    "AI tools", "AI shift 2025", "marketing AI", "AI job loss",
    "AI transformation", "technology documentary", "faceless youtube",
    "AI voiceover", "Kling AI", "ElevenLabs", "AI video",
    "career AI", "AI automation", "AI salary", "early adopters AI",
    "AI professionals", "AI 2026", "the shift AI", "V-Real AI",
    "documentary 2026",
]

# ---------------------------------------------------------------------------
# Script Blocks (EP001 v8-FINAL)
# ---------------------------------------------------------------------------

SCRIPT_BLOCKS = [
    {
        "id": "block_1_hook",
        "title": "Hook + Setup + Sarah",
        "timestamp": "0:00-3:15",
        "text": (
            "No one sent an announcement. No one rang a bell. "
            "The rules just changed. "
            "And 3.2 million people found out the hard way — "
            "on an ordinary Tuesday morning, "
            "in an ordinary office, "
            "doing ordinary work. "
            "Sarah Chen ran digital marketing for a mid-size software company. "
            "Good team. Good numbers. Fourteen people who knew what they were doing. "
            "Then the platform updated. New tools, overnight. "
            "Tasks that took her team a full day? Done in eleven minutes. "
            "Not by replacing them. By making most of what they did... unnecessary. "
            "By Thursday, leadership had restructured. "
            "Half the team was reassigned. Two were let go. "
            "Sarah wasn't one of them. Not because she was lucky. "
            "Because she'd already been experimenting with the tools — for months. "
            "She didn't wait for permission. She didn't wait for a mandate. "
            "She just... started."
        ),
    },
    {
        "id": "block_2_mike",
        "title": "Mike's Story — The Cost of Waiting",
        "timestamp": "3:15-4:45",
        "text": (
            "Mike Rodriguez managed operations at the same company. "
            "Twenty-two years of experience. Respected. Reliable. "
            "He watched the tools arrive and thought: this is a phase. "
            "He wasn't lazy. He wasn't stupid. "
            "He just believed that deep expertise would always win. "
            "It used to. "
            "But the tools didn't care about seniority. "
            "They didn't care about process knowledge or institutional memory. "
            "They cared about who could use them. "
            "And Mike hadn't learned. "
            "Within ninety days, his role was absorbed into a system "
            "that required one person and a dashboard."
        ),
    },
    {
        "id": "block_3_david",
        "title": "David's Story — The Early Mover",
        "timestamp": "4:45-6:00",
        "text": (
            "David Park worked three floors up. Product strategy. "
            "Same company. Same Tuesday. Very different outcome. "
            "David had been testing AI tools since the beta releases. "
            "Not because he was told to. Because he was curious. "
            "When the restructuring hit, David wasn't just safe — "
            "he was promoted. "
            "He became the person who understood how the new tools "
            "connected to the old workflows. "
            "The bridge between what the company was and what it needed to become. "
            "His salary went up twenty-eight percent in three months. "
            "Not because he worked harder. "
            "Because he'd already done the work that mattered."
        ),
    },
    {
        "id": "block_4_framework",
        "title": "The Framework — The 90-Day Rule",
        "timestamp": "6:00-8:30",
        "text": (
            "Here's what the data actually shows. "
            "In the first ninety days after a major AI tool enters a field, "
            "three groups emerge. "
            "The first group — roughly fifteen percent — adopts immediately. "
            "They experiment. They break things. They figure it out. "
            "The second group — about sixty percent — watches. "
            "They wait for best practices. For training. For permission. "
            "The third group — the remaining twenty-five percent — resists. "
            "They argue it's overhyped. That the tools aren't ready. "
            "That real work requires human judgment. "
            "Twelve months later, the data is clear. "
            "Group one captured most of the new value. "
            "Their salaries increased. Their roles expanded. "
            "Their skills became the ones that mattered. "
            "Group two adapted — eventually. But they were playing catch-up. "
            "Competing for positions that group one had already defined. "
            "Group three? "
            "Many of them aren't in the same roles anymore. "
            "Not because they were bad at their jobs. "
            "Because the jobs changed, and they didn't. "
            "The barrier to entry didn't just lower. It evaporated. "
            "They no longer require mastery of execution. They require taste. "
            "Taste in what to build. Taste in what to ask. "
            "Taste in knowing what the tools can't do — and what only you can."
        ),
    },
    {
        "id": "block_5_close",
        "title": "Close — Brand Statement",
        "timestamp": "8:30-9:00",
        "text": (
            "You've felt it. That quiet hum in the background. "
            "The sense that something fundamental shifted — "
            "and most people haven't caught up yet. "
            "You're not paranoid. You're observant. "
            "This is V-Real AI."
        ),
    },
]

# ---------------------------------------------------------------------------
# Scene Descriptions (14 Scenes for Kling AI)
# ---------------------------------------------------------------------------

SCENE_FOOTAGE = [
    {
        "scene": 1,
        "description": "Close-up of smartphone screen lighting up with notification in dark office, blue glow on face",
        "camera": "Slow dolly in, shallow depth of field",
        "duration": 10,
        "mood": "ominous, anticipation",
    },
    {
        "scene": 2,
        "description": "Aerial shot of modern office building at dawn, golden light breaking through clouds",
        "camera": "Slow ascending crane shot",
        "duration": 10,
        "mood": "establishing, contemplative",
    },
    {
        "scene": 3,
        "description": "Woman (30s) working alone at laptop at midnight, city lights through window behind her",
        "camera": "Slow orbit around subject",
        "duration": 12,
        "mood": "determination, isolation",
    },
    {
        "scene": 4,
        "description": "Modern boardroom with AI analytics dashboard on large screen, empty chairs",
        "camera": "Slow push in toward screen",
        "duration": 8,
        "mood": "corporate, tension",
    },
    {
        "scene": 5,
        "description": "Man (50s) sitting alone at desk, colleagues visible through glass wall behind him, blurred",
        "camera": "Static with slow focus pull from background to subject",
        "duration": 10,
        "mood": "isolation, quiet desperation",
    },
    {
        "scene": 6,
        "description": "Hands typing rapidly on keyboard, holographic data visualizations rising from screen",
        "camera": "Close-up, shallow depth of field",
        "duration": 8,
        "mood": "intensity, innovation",
    },
    {
        "scene": 7,
        "description": "Executive handshake in corner office with city skyline view, warm sunlight",
        "camera": "Medium shot, golden hour lighting",
        "duration": 8,
        "mood": "achievement, new beginning",
    },
    {
        "scene": 8,
        "description": "Split screen: left side shows manual work (papers, calculator), right side shows AI dashboard",
        "camera": "Static, cinematic lighting",
        "duration": 10,
        "mood": "contrast, before/after",
    },
    {
        "scene": 9,
        "description": "Time-lapse of office floor transitioning from busy to half-empty, chairs pulled away",
        "camera": "Wide establishing shot, fixed position",
        "duration": 12,
        "mood": "transformation, loss",
    },
    {
        "scene": 10,
        "description": "Close-up of bar chart growing on screen, green bars overtaking red bars",
        "camera": "Slow push in with rack focus",
        "duration": 8,
        "mood": "data-driven, revelation",
    },
    {
        "scene": 11,
        "description": "Person walking through server room with blue LED lighting, reflections on floor",
        "camera": "Tracking shot, following from behind",
        "duration": 10,
        "mood": "technological, awe",
    },
    {
        "scene": 12,
        "description": "Group of diverse professionals in workshop, AI tools on multiple screens, collaborative energy",
        "camera": "Handheld, documentary style movement",
        "duration": 10,
        "mood": "hope, collaboration",
    },
    {
        "scene": 13,
        "description": "Single person standing at crossroads in futuristic corridor, one path dark, one bright",
        "camera": "Wide shot, symmetric composition",
        "duration": 10,
        "mood": "choice, metaphorical",
    },
    {
        "scene": 14,
        "description": "Cinematic close-up of eye reflecting blue AI interface, pupil dilating",
        "camera": "Extreme close-up, slow motion",
        "duration": 8,
        "mood": "intimate, revelatory — closing shot",
    },
]

# ---------------------------------------------------------------------------
# Video Assembly Configuration
# ---------------------------------------------------------------------------

TEXT_OVERLAYS = [
    {"text": "3.2 million people experienced this in 2025", "timestamp": "0:08"},
    {"text": "Done in 11 minutes", "timestamp": "1:15"},
    {"text": "28% salary increase for early adopters", "timestamp": "5:30"},
    {"text": "90 DAYS — the window that determines your outcome", "timestamp": "6:15"},
    {"text": "You're not paranoid. You're observant.", "timestamp": "8:40"},
]

LOWER_THIRDS = [
    {"name": "SARAH CHEN", "title": "VP of Marketing, Nexus Corp", "timestamp": "0:45"},
    {"name": "MIKE RODRIGUEZ", "title": "Operations Manager, 22 Years", "timestamp": "3:20"},
    {"name": "DAVID PARK", "title": "Product Strategy, Nexus Corp", "timestamp": "4:50"},
]

CHAPTERS = [
    {"time": "0:00", "title": "The Morning Everything Changed"},
    {"time": "0:45", "title": "Sarah Chen's Story"},
    {"time": "1:30", "title": "The New Rules"},
    {"time": "3:15", "title": "Mike's Warning"},
    {"time": "4:45", "title": "David's Playbook"},
    {"time": "6:00", "title": "The 90-Day Rule"},
    {"time": "6:30", "title": "Three Groups Emerge"},
    {"time": "7:30", "title": "What The Data Says"},
    {"time": "8:15", "title": "Taste Over Mastery"},
    {"time": "8:30", "title": "You're Not Paranoid"},
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
        "seo_filename": "half-her-team-was-gone-by-10am-ai-shift-2026.mp4",
    }

    # Save metadata to file
    metadata_file = OUTPUT_DIR / "youtube_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved: {metadata_file}")

    return metadata


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main():
    parser = argparse.ArgumentParser(description="EP001 Production Runner")
    parser.add_argument("--step", type=int, help="Run only a specific step (1-4)")
    parser.add_argument("--skip-voice", action="store_true", help="Skip voiceover generation")
    parser.add_argument("--skip-footage", action="store_true", help="Skip footage generation")
    parser.add_argument("--dry-run", action="store_true", help="Preview without generating")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info(f"V-REAL AI — {EPISODE_TITLE}")
    logger.info("Full Production Runner")
    logger.info("=" * 60)

    voiceover = None
    footage = []
    music = None

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
        assemble_video(voiceover, footage, music, dry_run=args.dry_run)

    # Step 4: Upload metadata
    if args.step is None or args.step == 4:
        prepare_upload_metadata()

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
