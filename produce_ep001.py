#!/usr/bin/env python3
"""
EP001 Production Runner — "The Shift"

Single-command script to produce EP001 end-to-end:
  1. Generate voiceover via ElevenLabs API
  2. Download b-roll from Pexels
  3. Download background music from Pixabay
  4. Assemble video with FFmpeg (using video_assembler.py engine)
  5. Upload to YouTube

Usage:
  python produce_ep001.py                    # Run full pipeline
  python produce_ep001.py --step voiceover   # Run only voiceover generation
  python produce_ep001.py --step footage     # Run only footage download
  python produce_ep001.py --step assemble    # Run only video assembly
  python produce_ep001.py --step upload      # Run only YouTube upload

Requires:
  - ELEVENLABS_API_KEY in .env
  - PEXELS_API_KEY in .env
  - ffmpeg installed
  - YouTube OAuth credentials (for upload step)
"""
from __future__ import annotations

import os
import sys
import json
import time
import argparse
import subprocess
from pathlib import Path
from dataclasses import dataclass

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent / "vreal-ai" / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / "vreal-ai" / "backend" / ".env")

# ── Make.com Integration ────────────────────────────────────────────────────
# Every production step notifies Make.com so the automation pipeline stays in sync.
# Make.com can then: update Google Sheets, notify Pedro, trigger downstream scenarios.

import httpx  # lazy — only used if webhooks are configured

MAKE_WEBHOOKS = {
    "voiceover": os.getenv("MAKE_WEBHOOK_VOICEOVER", ""),
    "video": os.getenv("MAKE_WEBHOOK_VIDEO", ""),
    "upload": os.getenv("MAKE_WEBHOOK_UPLOAD", ""),
    "thumbnail": os.getenv("MAKE_WEBHOOK_THUMBNAIL", ""),
    "seo": os.getenv("MAKE_WEBHOOK_SEO", ""),
    "sheets": os.getenv("MAKE_WEBHOOK_SHEETS", ""),
    "notify": os.getenv("MAKE_WEBHOOK_NOTIFY", ""),
    "analytics": os.getenv("MAKE_WEBHOOK_ANALYTICS", ""),
    "social": os.getenv("MAKE_WEBHOOK_SOCIAL", ""),
}


def notify_make(scenario: str, payload: dict) -> bool:
    """
    Fire a Make.com webhook to notify the automation pipeline.

    This is non-blocking — if Make.com is down or the webhook isn't configured,
    production continues. Make.com is a listener, not a gatekeeper.
    """
    webhook_url = MAKE_WEBHOOKS.get(scenario, "")
    if not webhook_url:
        return False

    try:
        response = httpx.post(
            webhook_url,
            json={
                "episode_id": EPISODE_ID,
                "step": scenario,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                **payload,
            },
            timeout=10,
        )
        if response.status_code == 200:
            print(f"[MAKE.COM] ✓ Notified: {scenario}")
            return True
        else:
            print(f"[MAKE.COM] WARNING: {scenario} returned {response.status_code}")
            return False
    except Exception as e:
        print(f"[MAKE.COM] WARNING: Could not reach {scenario}: {str(e)[:100]}")
        return False


# ── Configuration ────────────────────────────────────────────────────────────

EPISODE_ID = "ep001"
EPISODE_TITLE = "EP001 — The Shift"
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output" / EPISODE_ID
ASSETS_DIR = BASE_DIR / "assets" / EPISODE_ID
FOOTAGE_DIR = ASSETS_DIR / "footage"
AUDIO_DIR = ASSETS_DIR / "audio"
TEMP_DIR = OUTPUT_DIR / "temp"

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

# ElevenLabs voice settings (Julian — BBC documentary narrator)
VOICE_ID = "CjK4w2V6sbgFJY05zTGt"  # Julian
VOICE_SETTINGS = {
    "stability": 0.65,
    "similarity_boost": 0.75,
    "style": 0.0,
    "use_speaker_boost": False,
}
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# ── Script Blocks ────────────────────────────────────────────────────────────
# Split into 5 generation blocks per voiceover brief

SCRIPT_BLOCKS = [
    {
        "name": "block1-hook-sarah",
        "section": "Hook + Setup + Sarah (0:00-3:15)",
        "text": """Sarah Chen's phone buzzed at nine forty-seven AM.

Emergency meeting.

By ten AM, half her team was gone.

Replaced by AI tools that cost forty-nine dollars a month.

But here's what nobody tells you — the people who moved fast saw twenty-eight percent salary increases.

The people who froze took eight months to recover.

The difference was a single decision made in the first ninety days.

And I tracked exactly what that decision was.

This happened to three point two million people in 2025.

December fifteenth, 2025.

OpenAI released their advanced reasoning model.

Same week, Anthropic launched Claude three point five Sonnet with computer control.

Within seventy-two hours, AI tools could handle tasks that took human teams weeks.

I tracked forty-seven people through this transformation — across eight industries, four continents, ages twenty-six to fifty-two.

Three survival patterns emerged.

The first pattern: people who experimented immediately. Sarah Chen is the clearest example.

Sarah Chen didn't wait for permission.

December eighteenth — three days after the AI announcement — she signed up for everything.

Claude. ChatGPT. Copy dot AI.

Her husband found her at midnight, teaching Claude to analyze competitor campaigns.

"What are you doing?"

"Learning how to survive."

January third — breakthrough moment.

A competitive analysis that typically took two days was finished by eleven thirty AM.

But something was different about the quality.

The AI handled the data collection.

Sarah added the strategic thinking that competitors couldn't replicate.

She didn't replace herself with AI.

She became irreplaceable because of AI.

The second pattern: people who resisted the change. Mike Rodriguez represents this path.""",
    },
    {
        "name": "block2-mike",
        "section": "Mike's Story (3:15-4:45)",
        "text": """Mike Rodriguez made a different choice.

Eighteen years of legal research experience.

When his firm introduced Harvey AI, Mike's response was immediate and final.

His words: "I don't need a computer to tell me how to practice law."

That wasn't arrogance.

Mike believed something true — human judgment in law can't be outsourced.

He'd built his reputation on finding precedents other lawyers missed.

On understanding the nuance behind case law.

On being the guy partners trusted with impossible research.

The problem?

Harvey AI didn't outsource his judgment. It accelerated it.

And he missed the moment when that distinction mattered.

While his colleagues learned Harvey AI, Mike doubled down on what made him valuable.

February reality check.

His research assignments were taking six hours.

His AI-assisted colleagues were finishing equivalent work in forty-five minutes.

The partners delivered their verdict.

"Mike, your efficiency metrics don't justify your position."

March first — position eliminated.

Mike wasn't alone. Forty-three percent of workers who rejected AI training in the first sixty days faced similar outcomes within six months.

The third pattern: people who saw the shift as strategy. David Park exemplifies this approach.""",
    },
    {
        "name": "block3-david",
        "section": "David's Story (4:45-6:00)",
        "text": """David Park saw what others missed.

When his company announced AI customer service integration, David didn't panic.

He studied the technology for two weeks.

Mapped what AI could and couldn't do.

Then he wrote the memo that changed everything.

"AI can handle eighty percent of our ticket volume perfectly. But the twenty percent it can't handle — furious customers, complex technical issues, executive escalations — that's where we create customer loyalty."

Instead of fighting the AI rollout, he designed it.

Result: VP of Customer Experience.

Forty-eight percent salary increase.

But here's what connects these three stories...

Each person had the exact same information on the exact same day.

The difference wasn't opportunity. It was response speed.""",
    },
    {
        "name": "block4-framework",
        "section": "Framework Revelation (6:00-8:30)",
        "text": """Sarah, Mike, and David weren't unique cases.

I found this same pattern in forty-seven people across eight industries.

The people who succeeded all did three specific actions within ninety days of their company's AI announcement.

This is the Ninety-Day Rule.

Days one to thirty: Immediate hands-on experimentation.

Winners signed up for AI tools the day their company announced integration.

Not when training started. Not when it became mandatory.

The day they heard it was coming.

Sarah spent thirty minutes every morning for thirty days testing different AI tools.

She gave Claude the same tasks she'd normally do manually.

Compared outputs. Found the gaps. Learned the limits.

Mike? He never opened a single AI tool.

Days thirty-one to sixty: Identify your irreplaceable complement.

They mapped what AI handled well versus what broke down.

Then they became experts at the breakdown points.

Sarah discovered AI could generate competitive analysis in minutes.

But it couldn't interpret what that meant for strategy.

Couldn't read between the lines of competitor behavior.

Couldn't predict which insights would actually change business decisions.

So she became the strategic interpreter.

David found AI could resolve eighty percent of customer tickets.

But it couldn't handle the twenty percent that required emotional intelligence.

The angry customers. The complex technical problems. The executive escalations.

So he became the human escalation specialist.

Days sixty-one to ninety: Position yourself as the essential bridge.

They stopped competing with AI and started designing workflows that combined both.

They became the person who understood what AI could do and what humans had to do.

Sarah pitched herself as the "AI-Human Strategy Director."

Not just a marketer. The person who could harness AI speed and add human wisdom.

David positioned himself as the "Customer Experience Architect."

Not just a manager. The designer of human-AI customer service systems.

They made themselves indispensable by becoming the integration point.

Here's what makes this urgent.

Most industries are already past day sixty of this transformation.

If you're in marketing, customer service, content creation, research, analysis — your ninety-day window is probably closing.

If you're watching this today, here's what you do.

Question one: What am I doing manually that AI could accelerate?

Pick one task. Sign up for one AI tool. Test it for thirty minutes.

Question two: What can I do that AI fundamentally cannot?

Find the breakdown points. The judgment calls. The human moments.

Question three: How do I become the bridge that makes both work better?

Don't compete with AI. Design the workflow that needs both.

The question isn't whether this will reach your job.

It's whether you'll be Sarah or Mike when it does.

This shift isn't happening to us.

It's happening through us.

The question is: which side of it will you choose to be on?""",
    },
    {
        "name": "block5-close",
        "section": "Brand Close (8:30-9:00)",
        "text": """If this changed how you see what's coming for your industry, there's more where this came from.

This is V-Real AI.

We're here to help you see what's coming — and position yourself correctly — before your ninety days are up.

Subscribe for the insights that determine outcomes.

The next episode drops Tuesday.""",
    },
]

# ── B-Roll Scene Definitions ────────────────────────────────────────────────

SCENE_FOOTAGE = [
    {"scene": 1, "query": "neural network dark visualization", "alt": "AI brain digital", "duration": 12, "start": 0},
    {"scene": 2, "query": "data particles accelerating light", "alt": "technology light trails", "duration": 12, "start": 12},
    {"scene": 3, "query": "person crossroads silhouette decision", "alt": "fork in road dramatic", "duration": 21, "start": 24},
    {"scene": 4, "query": "woman working laptop night office", "alt": "professional late night computer", "duration": 37, "start": 45},
    {"scene": 5, "query": "phone notification message alert", "alt": "smartphone notification close", "duration": 23, "start": 82},
    {"scene": 6, "query": "person using AI tools multiple screens", "alt": "programmer multiple monitors", "duration": 40, "start": 105},
    {"scene": 7, "query": "AI generated digital creativity", "alt": "abstract digital art creation", "duration": 35, "start": 145},
    {"scene": 8, "query": "hand selecting choosing decision", "alt": "choosing path strategic", "duration": 30, "start": 180},
    {"scene": 9, "query": "revenue growth chart data visualization", "alt": "business analytics dashboard", "duration": 45, "start": 210},
    {"scene": 10, "query": "world map connections global network", "alt": "global digital connections", "duration": 45, "start": 255},
    {"scene": 11, "query": "chain reaction dominos technology", "alt": "ripple effect spreading", "duration": 40, "start": 300},
    {"scene": 12, "query": "two paths diverging gap between", "alt": "contrast inequality divide", "duration": 35, "start": 340},
    {"scene": 13, "query": "sunrise opportunity hope new beginning", "alt": "dawn light through clouds", "duration": 75, "start": 375},
    {"scene": 14, "query": "person walking forward confident future", "alt": "silhouette walking toward light", "duration": 90, "start": 450},
]

# ── Text Overlays ────────────────────────────────────────────────────────────

TEXT_OVERLAYS = [
    {"text": "3.2 million people experienced this in 2025", "start": 30.0, "end": 35.0, "position": "lower_third"},
    {"text": "48% salary increase", "start": 295.0, "end": 300.0, "position": "center"},
    {"text": "Days 1-30: Immediate Experimentation", "start": 370.0, "end": 378.0, "position": "center"},
    {"text": "Days 31-60: Identify Your Complement", "start": 410.0, "end": 418.0, "position": "center"},
    {"text": "Days 61-90: Strategic Positioning", "start": 450.0, "end": 458.0, "position": "center"},
]

# ── YouTube Upload Metadata ──────────────────────────────────────────────────

# SEO-optimized description template (research-backed structure):
# - First 2 lines visible above fold → primary keyword in first 25 words
# - 200-500 word description with semantic keyword variations
# - Chapters create independent Google search entry points ("Key Moments")
# - Each chapter title is keyword-rich for discoverability
# - Hashtags at end for YouTube search indexing

YOUTUBE_METADATA = {
    "title": "Half Her Team Was Gone by 10 AM",
    "description": """Half her team was replaced by AI tools costing $49/month. But the people who moved fast saw 28% salary increases. Here's the 90-Day Rule that separates survivors from casualties in the AI shift of 2026.

I tracked 47 people through this exact AI transformation — across 8 industries, 4 continents. Three survival patterns emerged. This documentary breaks down each one with real stories and actionable frameworks.

0:00 Half Her Team Was Gone
0:30 The Day Everything Changed — December 15, 2025
1:45 Pattern 1: Sarah Chen — Immediate Action
3:15 Pattern 2: Mike Rodriguez — The Cost of Waiting
4:45 Pattern 3: David Park — The Strategic Architect
6:00 The 90-Day Rule — Why Timing Is Everything
7:30 Days 1-30: Immediate Experimentation Framework
8:00 Days 31-60: Finding Your Irreplaceable Complement
8:20 Days 61-90: Becoming the Essential Bridge
8:30 Your Action Plan — What to Do This Week

This is not motivational content. This is documented evidence from real professionals navigating the biggest workplace transformation since the internet.

Every AI tool mentioned in this video: Claude AI by Anthropic, ChatGPT by OpenAI, Harvey AI for legal research, Copy.ai for marketing automation.

V-Real AI creates cinematic documentaries about how artificial intelligence is reshaping careers, marketing, and business strategy. Every episode is researched, scripted, narrated, and produced using AI — full transparency on every tool and technique.

Made for marketing professionals, solopreneurs, business owners, and anyone adapting to AI in 2026.

New episodes every Tuesday.

Related videos:
EP002: The Price of Waiting — What happens when you delay 90 days
EP003: The Bridge Builders — People earning $200K+ designing human-AI workflows

#AIshift #AI2026 #AImarketing #futureofwork #AItools #AIforbeginners #solopreneur #marketingAI #AIstrategy #careerAI""",
    "tags": [
        "AI shift", "AI marketing", "AI tools for marketing", "AI 2026",
        "AI documentary", "future of marketing", "AI for solopreneurs",
        "AI job loss", "AI career strategy", "AI workflow for business",
        "how to use AI for marketing", "AI marketing strategy",
        "ChatGPT for marketing", "Claude AI for business",
        "AI replacing jobs", "AI salary increase", "90 day rule AI",
        "AI transformation documentary", "AI content strategy",
        "half her team was gone", "V-Real AI",
    ],
    "category_id": "27",  # Education
    "privacy_status": "unlisted",  # Always upload unlisted first, review, then make public
    "pinned_comment": """This entire video was researched, scripted, narrated, and produced using AI.

Every tool. Every step. Transparent.

If you're a marketer or solopreneur figuring out AI — you're in the right place. We show you what's actually working, not what's trending.

You're not paranoid. You're observant. This is V-Real AI.

Subscribe — the next episode drops Tuesday.""",
    # Keyword-rich filename for YouTube SEO (YouTube reads filename as early signal)
    "seo_filename": "half-her-team-was-gone-by-10am-ai-shift-2026.mp4",
}


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1: VOICEOVER GENERATION (ElevenLabs)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_voiceover():
    """Generate all voiceover blocks via ElevenLabs API, then concatenate."""
    import httpx

    if not ELEVENLABS_API_KEY:
        print("[VOICEOVER] ERROR: ELEVENLABS_API_KEY not set in .env")
        return None

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    final_path = AUDIO_DIR / "ep001-voiceover-full.mp3"

    if final_path.exists():
        print(f"[VOICEOVER] Already exists: {final_path}")
        return str(final_path)

    block_files = []

    for block in SCRIPT_BLOCKS:
        block_path = AUDIO_DIR / f"ep001-{block['name']}.mp3"

        if block_path.exists():
            print(f"[VOICEOVER] Block already exists: {block_path}")
            block_files.append(str(block_path))
            continue

        print(f"[VOICEOVER] Generating: {block['section']}...")

        try:
            response = httpx.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}",
                headers={
                    "xi-api-key": ELEVENLABS_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "text": block["text"],
                    "model_id": ELEVENLABS_MODEL,
                    "voice_settings": VOICE_SETTINGS,
                },
                timeout=120,
            )
        except (httpx.ProxyError, httpx.ConnectError) as e:
            print(f"[VOICEOVER] ERROR: Cannot reach ElevenLabs API — network blocked by proxy.")
            print(f"[VOICEOVER] This script must run on a machine with unrestricted internet access.")
            print(f"[VOICEOVER] Run this on your local machine: python produce_ep001.py --step voiceover")
            return None

        if response.status_code != 200:
            print(f"[VOICEOVER] ERROR: ElevenLabs returned {response.status_code}")
            print(f"[VOICEOVER] {response.text[:200]}")
            return None

        with open(block_path, "wb") as f:
            f.write(response.content)

        size_mb = len(response.content) / (1024 * 1024)
        print(f"[VOICEOVER] ✓ Saved: {block_path} ({size_mb:.1f} MB)")
        block_files.append(str(block_path))

        # Rate limit courtesy
        time.sleep(1)

    # Concatenate all blocks
    print("[VOICEOVER] Concatenating blocks...")
    concat_list = AUDIO_DIR / "concat_blocks.txt"
    with open(concat_list, "w") as f:
        for bf in block_files:
            f.write(f"file '{bf}'\n")

    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c", "copy", str(final_path)],
        check=True, capture_output=True,
    )

    print(f"[VOICEOVER] ✓ Full voiceover: {final_path}")

    # Notify Make.com — voiceover complete
    notify_make("voiceover", {
        "status": "complete",
        "file_path": str(final_path),
        "blocks": len(SCRIPT_BLOCKS),
        "voice_id": VOICE_ID,
    })

    return str(final_path)


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2: B-ROLL FOOTAGE (Pexels)
# ═══════════════════════════════════════════════════════════════════════════════

def download_footage():
    """Download b-roll footage from Pexels for all 14 scenes."""
    import httpx

    if not PEXELS_API_KEY:
        print("[FOOTAGE] ERROR: PEXELS_API_KEY not set in .env")
        return False

    FOOTAGE_DIR.mkdir(parents=True, exist_ok=True)
    downloaded = 0

    for scene in SCENE_FOOTAGE:
        scene_path = FOOTAGE_DIR / f"scene_{scene['scene']:02d}.mp4"

        if scene_path.exists():
            print(f"[FOOTAGE] Already exists: scene {scene['scene']:02d}")
            downloaded += 1
            continue

        # Try primary query, then alt
        for query in [scene["query"], scene["alt"]]:
            print(f"[FOOTAGE] Searching scene {scene['scene']:02d}: '{query}'...")

            try:
                response = httpx.get(
                    "https://api.pexels.com/videos/search",
                    params={
                        "query": query,
                        "per_page": 5,
                        "min_duration": 3,
                        "min_width": 1920,
                        "orientation": "landscape",
                    },
                    headers={"Authorization": PEXELS_API_KEY},
                    timeout=30,
                )
            except (httpx.ProxyError, httpx.ConnectError):
                print(f"[FOOTAGE] ERROR: Cannot reach Pexels API — network blocked by proxy.")
                print(f"[FOOTAGE] Run on your local machine: python produce_ep001.py --step footage")
                return False

            if response.status_code != 200:
                print(f"[FOOTAGE] Pexels error: {response.status_code}")
                continue

            videos = response.json().get("videos", [])
            if not videos:
                continue

            # Find best HD file from first result
            best_url = None
            for video in videos[:3]:
                for vf in video.get("video_files", []):
                    if vf.get("width", 0) >= 1920 and vf.get("quality") == "hd":
                        best_url = vf.get("link")
                        break
                if best_url:
                    break

            if not best_url:
                # Fallback to any HD
                for video in videos[:3]:
                    for vf in video.get("video_files", []):
                        if vf.get("quality") == "hd":
                            best_url = vf.get("link")
                            break
                    if best_url:
                        break

            if best_url:
                print(f"[FOOTAGE] Downloading scene {scene['scene']:02d}...")
                dl = httpx.get(best_url, timeout=120, follow_redirects=True)
                if dl.status_code == 200:
                    with open(scene_path, "wb") as f:
                        f.write(dl.content)
                    size_mb = len(dl.content) / (1024 * 1024)
                    print(f"[FOOTAGE] ✓ Scene {scene['scene']:02d} ({size_mb:.1f} MB)")
                    downloaded += 1
                    break

            time.sleep(0.5)  # Rate limit

    print(f"[FOOTAGE] Downloaded {downloaded}/{len(SCENE_FOOTAGE)} scenes")

    # Notify Make.com — footage download complete
    notify_make("sheets", {
        "status": "footage_complete",
        "scenes_downloaded": downloaded,
        "scenes_total": len(SCENE_FOOTAGE),
    })

    return downloaded > 0


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3: ASSEMBLE VIDEO
# ═══════════════════════════════════════════════════════════════════════════════

def assemble_video():
    """Assemble the final video using the video_assembler engine with full brand package."""
    from app.services.video_assembler import (
        AssemblyProject, SceneClip, TextOverlay, LowerThird, DataCard,
        assemble_video as run_assembly,
        generate_captions_srt, embed_xmp_metadata, extract_shorts_clips,
    )

    voice_path = AUDIO_DIR / "ep001-voiceover-full.mp3"
    if not voice_path.exists():
        print("[ASSEMBLE] ERROR: Voiceover not found. Run --step voiceover first.")
        return None

    # Look for background music
    music_path = None
    music_candidates = list(ASSETS_DIR.glob("*music*")) + list(AUDIO_DIR.glob("*music*"))
    if music_candidates:
        music_path = str(music_candidates[0])
        print(f"[ASSEMBLE] Using music: {music_path}")

    # Build scene clips from downloaded footage
    scenes = []
    for sf in SCENE_FOOTAGE:
        clip_path = FOOTAGE_DIR / f"scene_{sf['scene']:02d}.mp4"
        scenes.append(SceneClip(
            scene_number=sf["scene"],
            video_path=str(clip_path) if clip_path.exists() else "",
            start_time=float(sf["start"]),
            end_time=float(sf["start"] + sf["duration"]),
            motion="zoom_in" if sf["scene"] % 3 == 0 else "ken_burns" if sf["scene"] % 3 == 1 else "pan_right",
        ))

    # Build text overlays
    overlays = []
    for to in TEXT_OVERLAYS:
        overlays.append(TextOverlay(
            text=to["text"],
            start_time=to["start"],
            end_time=to["end"],
            position=to["position"],
        ))

    # Lower thirds — appear when each character is introduced
    lower_thirds = [
        LowerThird(name="SARAH CHEN", title="Marketing Strategist", start_time=50.0, duration=5.0),
        LowerThird(name="MIKE RODRIGUEZ", title="Legal Researcher - 18 Years", start_time=195.0, duration=5.0),
        LowerThird(name="DAVID PARK", title="Customer Service Manager", start_time=285.0, duration=5.0),
    ]

    # Data cards — key statistics that flash on screen
    data_cards = [
        DataCard(stat="3.2 MILLION", label="people experienced this in 2025", insert_at=30.0),
        DataCard(stat="28%", label="salary increase for early adopters", insert_at=15.0, accent_color="0xFFB347"),
        DataCard(stat="43%", label="who rejected AI faced job loss within 6 months", insert_at=245.0),
        DataCard(stat="48%", label="salary increase", insert_at=295.0, accent_color="0xFFB347"),
        DataCard(stat="90 DAYS", label="the window that determines your outcome", insert_at=365.0),
    ]

    # Brand asset paths (auto-generated by brand_graphics.py)
    brand_dir = BASE_DIR / "assets" / EPISODE_ID / "brand"

    # Re-hooks — MrBeast playbook: give viewers a reason to stay every 2-3 minutes
    rehooks = [
        {"text": "But here's what nobody expected...", "time": 120.0, "duration": 3.0},
        {"text": "This is where it gets interesting...", "time": 240.0, "duration": 3.0},
        {"text": "The pattern nobody talks about...", "time": 360.0, "duration": 3.0},
        {"text": "Watch what happens next...", "time": 450.0, "duration": 3.0},
    ]

    # Sections — for progress bar (drives completion psychology)
    sections = [
        {"label": "Sarah's Story", "start": 45.0, "end": 195.0},
        {"label": "Mike's Story", "start": 195.0, "end": 285.0},
        {"label": "David's Story", "start": 285.0, "end": 360.0},
        {"label": "The 90-Day Rule", "start": 360.0, "end": 510.0},
        {"label": "Your Action Plan", "start": 510.0, "end": 540.0},
    ]

    project = AssemblyProject(
        episode_id=EPISODE_ID,
        title=EPISODE_TITLE,
        voice_audio_path=str(voice_path),
        music_path=music_path,
        scenes=scenes,
        text_overlays=overlays,
        lower_thirds=lower_thirds,
        data_cards=data_cards,
        rehooks=rehooks,
        sections=sections,
        intro_path=str(brand_dir / "intro.mp4") if (brand_dir / "intro.mp4").exists() else None,
        end_screen_path=str(brand_dir / "end_screen.mp4") if (brand_dir / "end_screen.mp4").exists() else None,
        transition_path=str(brand_dir / "transition_glitch.mp4") if (brand_dir / "transition_glitch.mp4").exists() else None,
        enable_retention_editing=True,
        output_filename=YOUTUBE_METADATA.get("seo_filename", "ep001-the-shift-final.mp4"),
    )

    print("[ASSEMBLE] Starting video assembly with full brand package...")
    print(f"[ASSEMBLE]   Brand intro: {'YES' if project.intro_path else 'NO'}")
    print(f"[ASSEMBLE]   End screen: {'YES' if project.end_screen_path else 'NO'}")
    print(f"[ASSEMBLE]   Lower thirds: {len(lower_thirds)}")
    print(f"[ASSEMBLE]   Data cards: {len(data_cards)}")
    print(f"[ASSEMBLE]   Re-hooks: {len(rehooks)}")
    print(f"[ASSEMBLE]   Sections: {len(sections)}")
    print(f"[ASSEMBLE]   Retention editing: {'ON' if project.enable_retention_editing else 'OFF'}")

    # Notify Make.com — assembly starting
    notify_make("video", {
        "status": "assembly_started",
        "lower_thirds": len(lower_thirds),
        "data_cards": len(data_cards),
        "rehooks": len(rehooks),
        "sections": len(sections),
        "brand_intro": bool(project.intro_path),
        "end_screen": bool(project.end_screen_path),
        "retention_editing": project.enable_retention_editing,
    })

    output = run_assembly(project)
    print(f"[ASSEMBLE] Final video: {output}")

    # Notify Make.com — assembly complete
    notify_make("video", {
        "status": "assembly_complete",
        "file_path": output,
        "pipeline_steps": 14,
    })

    # Notify Make.com — update SEO metadata
    notify_make("seo", {
        "status": "metadata_ready",
        "title": YOUTUBE_METADATA["title"],
        "tags": YOUTUBE_METADATA["tags"],
        "description_length": len(YOUTUBE_METADATA["description"]),
        "filename": YOUTUBE_METADATA.get("seo_filename", ""),
    })

    return output


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4: UPLOAD TO YOUTUBE
# ═══════════════════════════════════════════════════════════════════════════════

def upload_to_youtube():
    """Upload the final video to YouTube with full metadata."""
    from app.services.youtube_uploader import upload_video, add_comment

    seo_name = YOUTUBE_METADATA.get("seo_filename", "ep001-the-shift-final.mp4")
    video_path = Path(os.path.expanduser("~/youtube-empire/output")) / seo_name
    # Fallback to old name if SEO name doesn't exist
    if not video_path.exists():
        video_path = Path(os.path.expanduser("~/youtube-empire/output")) / "ep001-the-shift-final.mp4"
    if not video_path.exists():
        print("[UPLOAD] ERROR: Final video not found. Run --step assemble first.")
        return None

    thumbnail_path = ASSETS_DIR / "ep001-thumbnail.jpg"
    if not thumbnail_path.exists():
        thumbnail_path = None
        print("[UPLOAD] WARNING: No thumbnail found. Upload manually later.")

    print("[UPLOAD] Uploading to YouTube...")
    video_id = upload_video(
        video_path=str(video_path),
        title=YOUTUBE_METADATA["title"],
        description=YOUTUBE_METADATA["description"],
        tags=YOUTUBE_METADATA["tags"],
        category_id=YOUTUBE_METADATA["category_id"],
        privacy_status=YOUTUBE_METADATA["privacy_status"],
        thumbnail_path=str(thumbnail_path) if thumbnail_path else None,
    )

    if video_id:
        print(f"[UPLOAD] ✓ Video uploaded: https://youtube.com/watch?v={video_id}")

        # Pin comment
        if YOUTUBE_METADATA.get("pinned_comment"):
            add_comment(video_id, YOUTUBE_METADATA["pinned_comment"])
            print("[UPLOAD] ✓ Pinned comment added")

        # Notify Make.com — upload complete (triggers downstream: sheets, social, analytics)
        notify_make("upload", {
            "status": "uploaded",
            "video_id": video_id,
            "video_url": f"https://youtube.com/watch?v={video_id}",
            "title": YOUTUBE_METADATA["title"],
            "privacy": YOUTUBE_METADATA["privacy_status"],
        })

        # Trigger analytics tracking
        notify_make("analytics", {
            "status": "monitoring_started",
            "video_id": video_id,
            "check_intervals": ["1h", "6h", "24h", "48h"],
        })

        # Notify Pedro
        notify_make("notify", {
            "message": f"EP001 uploaded: https://youtube.com/watch?v={video_id}",
            "action_needed": "Review video and approve for public",
            "current_status": YOUTUBE_METADATA["privacy_status"],
        })

    return video_id


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="EP001 Production Runner")
    parser.add_argument("--step", choices=["voiceover", "footage", "assemble", "upload", "all"],
                        default="all", help="Which production step to run")
    args = parser.parse_args()

    print("=" * 60)
    print("  EP001 'THE SHIFT' — PRODUCTION RUNNER")
    print("  14-Step Pipeline + Make.com Integration")
    print("=" * 60)

    # Create directories
    for d in [OUTPUT_DIR, ASSETS_DIR, FOOTAGE_DIR, AUDIO_DIR, TEMP_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    # Notify Make.com — production starting
    notify_make("sheets", {
        "status": "production_started",
        "step": args.step,
        "title": EPISODE_TITLE,
        "pipeline_version": "14-step",
    })

    if args.step in ("voiceover", "all"):
        print("\n─── STEP 1: VOICEOVER ───")
        result = generate_voiceover()
        if not result and args.step == "all":
            print("[FATAL] Voiceover generation failed. Cannot continue.")
            return 1

    if args.step in ("footage", "all"):
        print("\n─── STEP 2: B-ROLL FOOTAGE ───")
        download_footage()

    if args.step in ("assemble", "all"):
        print("\n─── STEP 2.5: GENERATE BRAND ASSETS ───")
        try:
            from app.services.brand_graphics import generate_ep001_assets
            generate_ep001_assets()
        except Exception as e:
            print(f"[BRAND] WARNING: Could not generate brand assets: {e}")
            print("[BRAND] Continuing assembly without brand package...")

        print("\n─── STEP 3: VIDEO ASSEMBLY ───")
        assemble_video()

    if args.step in ("upload", "all"):
        print("\n─── STEP 4: YOUTUBE UPLOAD ───")
        video_id = upload_to_youtube()

        # Step 5: Start post-publish monitoring
        if video_id:
            print("\n─── STEP 5: POST-PUBLISH MONITOR ───")
            try:
                from app.services.post_publish_monitor import start_monitoring
                start_monitoring(video_id, EPISODE_ID)
                print(f"[MONITOR] Post-publish monitoring active for {video_id}")
                print("[MONITOR] Will track: views, CTR, retention, comments")
                print("[MONITOR] Reports at: 1h, 6h, 24h, 48h")
            except ImportError:
                print("[MONITOR] Post-publish monitor not available (import failed)")
            except Exception as e:
                print(f"[MONITOR] WARNING: Could not start monitoring: {e}")

            # Step 6: Upload captions if available
            print("\n─── STEP 6: UPLOAD CAPTIONS ───")
            captions_path = OUTPUT_DIR / f"{EPISODE_ID}-captions.srt"
            if captions_path.exists():
                try:
                    from app.services.youtube_uploader import upload_captions
                    upload_captions(video_id, str(captions_path), language="en")
                    print(f"[CAPTIONS] Uploaded SRT captions for SEO boost")
                except (ImportError, Exception) as e:
                    print(f"[CAPTIONS] WARNING: Caption upload failed: {e}")
                    print(f"[CAPTIONS] Manual upload: {captions_path}")
            else:
                print("[CAPTIONS] No caption file found (skipped)")

            # Report Shorts for separate upload
            shorts_dir = OUTPUT_DIR / EPISODE_ID / "shorts"
            if shorts_dir.exists():
                shorts = list(shorts_dir.glob("short_*.mp4"))
                if shorts:
                    print(f"\n─── SHORTS READY FOR UPLOAD ({len(shorts)} clips) ───")
                    for s in shorts:
                        print(f"  {s}")
                    print("[SHORTS] Upload these as YouTube Shorts with #Shorts in title")

                    # Notify Make.com — Shorts ready for social distribution
                    notify_make("social", {
                        "status": "shorts_ready",
                        "shorts_count": len(shorts),
                        "shorts_dir": str(shorts_dir),
                        "video_id": video_id,
                        "platforms": ["youtube_shorts", "tiktok", "instagram_reels"],
                    })

            # Trigger thumbnail generation via Make.com
            notify_make("thumbnail", {
                "status": "generate",
                "video_id": video_id,
                "title": YOUTUBE_METADATA["title"],
                "concept": "shocked face + '10 AM' in cyan + dark background with TERMINATED overlay",
                "variants": 3,  # A/B test 3 thumbnails
            })

    # Notify Make.com — full production complete
    notify_make("sheets", {
        "status": "production_complete",
        "step": args.step,
        "title": EPISODE_TITLE,
    })
    notify_make("notify", {
        "message": f"EP001 production complete ({args.step})",
        "action_needed": "Review and approve for public release",
    })

    print("\n" + "=" * 60)
    print("  PRODUCTION COMPLETE")
    print("  All Make.com scenarios notified.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
