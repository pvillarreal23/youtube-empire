"""
V-Real AI Brand Graphics Generator

Generates all branded motion graphics elements using FFmpeg:
  - Animated intro (3s logo reveal)
  - Lower thirds (name/title cards)
  - Data visualization cards (stat callouts)
  - Scene transitions (glitch/wipe)
  - End screen (subscribe CTA)
  - Retention editing helpers (zoom punches, flash cuts)

All elements use the V-Real AI brand palette:
  - Background: #0A0F1E (dark navy)
  - Accent Blue: #00D4FF (electric cyan)
  - Accent Amber: #FFB347 (warm amber)
  - Text: #FFFFFF / #C8C8C8

These are generated as standalone clips that get composited
into the main video during assembly.
"""
from __future__ import annotations

import os
import subprocess
import json
from pathlib import Path
from typing import Optional

# Brand constants
BRAND_BG = "0x0A0F1E"
BRAND_BLUE = "0x00D4FF"
BRAND_AMBER = "0xFFB347"
BRAND_WHITE = "0xFFFFFF"
BRAND_GRAY = "0xC8C8C8"

# Video specs (match assembler)
W, H, FPS = 1920, 1080, 30

ASSETS_DIR = os.path.expanduser("~/youtube-empire/assets/brand")
os.makedirs(ASSETS_DIR, exist_ok=True)


def _run_ffmpeg(cmd: list[str], desc: str = "") -> bool:
    """Run FFmpeg command with error handling."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[BRAND-GFX] ERROR {desc}: {e.stderr[:500]}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 1. ANIMATED BRAND INTRO (3 seconds)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_intro(output_path: Optional[str] = None, duration: float = 3.0) -> str:
    """
    Generate a 3-second animated brand intro.

    Visual sequence:
      0.0-0.5s: Black screen, subtle particle noise fades in
      0.5-1.5s: Cyan horizontal line draws across center, expands
      1.5-2.2s: "V-REAL AI" text fades in above line, subtitle below
      2.2-2.8s: Hold
      2.8-3.0s: Quick fade to content

    Uses drawtext with alpha animation and drawbox for the line.
    """
    if output_path is None:
        output_path = os.path.join(ASSETS_DIR, "intro.mp4")

    frames = int(duration * FPS)

    # Complex filtergraph for animated intro
    # Layer 1: Dark background with subtle grain
    # Layer 2: Animated cyan line expanding from center
    # Layer 3: V-REAL AI text with fade-in
    # Layer 4: Subtitle with delayed fade-in
    filter_complex = (
        # Base: dark background
        f"color=c={BRAND_BG}:s={W}x{H}:d={duration}:r={FPS}[bg];"

        # Grain overlay for texture
        f"nullsrc=s={W}x{H}:d={duration}:r={FPS},"
        f"geq=random(1)*20:128:128,"
        f"format=yuv420p,"
        f"colorbalance=bs=-0.9:gs=-0.9:rs=-0.8[grain];"

        # Merge bg + grain
        f"[bg][grain]blend=all_mode=addition:all_opacity=0.08[textured];"

        # Cyan accent line - horizontal, expanding from center
        # drawbox: x starts at center, expands outward
        f"[textured]drawbox="
        f"x='if(lt(t,0.5),{W//2},max(0,{W//2}-({W//2}*(t-0.5)/1.0)))':"
        f"y={H//2 - 1}:"
        f"w='if(lt(t,0.5),0,min({W},2*{W//2}*(t-0.5)/1.0))':"
        f"h=3:"
        f"color={BRAND_BLUE}@1.0:"
        f"t=fill:"
        f"enable='gte(t,0.3)'[lined];"

        # V-REAL AI title text
        f"[lined]drawtext="
        f"text='V - R E A L   A I':"
        f"fontsize=72:"
        f"fontcolor={BRAND_WHITE}:"
        f"x=(w-text_w)/2:"
        f"y=(h/2)-80:"
        f"alpha='if(lt(t,1.5),0,min(1,(t-1.5)/0.4))*if(gt(t,{duration-0.3}),max(0,1-(t-{duration-0.3})/0.3),1)'[titled];"

        # Subtitle
        f"[titled]drawtext="
        f"text='INSIGHTS THAT DETERMINE OUTCOMES':"
        f"fontsize=24:"
        f"fontcolor={BRAND_GRAY}:"
        f"x=(w-text_w)/2:"
        f"y=(h/2)+40:"
        f"alpha='if(lt(t,1.8),0,min(1,(t-1.8)/0.4))*if(gt(t,{duration-0.3}),max(0,1-(t-{duration-0.3})/0.3),1)'[final]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p",
        "-t", str(duration),
        # Add silent audio track so concat works
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-c:a", "aac", "-b:a", "192k", "-shortest",
        output_path,
    ]

    # ffmpeg requires -i inputs before -filter_complex in some builds,
    # but for generated sources we use lavfi within the filter.
    # Rebuild command properly:
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex", filter_complex,
        "-map", "[final]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-shortest",
        output_path,
    ]

    if _run_ffmpeg(cmd, "intro generation"):
        print(f"[BRAND-GFX] Intro generated: {output_path}")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# 2. LOWER THIRDS (name/title cards)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_lower_third(
    name: str,
    title: str,
    output_path: Optional[str] = None,
    duration: float = 5.0,
    position: str = "left",
) -> str:
    """
    Generate a lower-third name card.

    Visual:
      - Semi-transparent dark box slides in from left
      - Cyan accent bar on left edge
      - Name in white (bold, 36px)
      - Title in gray (regular, 24px)
      - Fade in over 0.3s, hold, fade out over 0.3s

    Args:
        name: Person's name (e.g. "SARAH CHEN")
        title: Title/role (e.g. "Marketing Strategist")
        duration: How long the lower third stays on screen
        position: "left" or "right"
    """
    if output_path is None:
        safe_name = name.lower().replace(" ", "_").replace("'", "")
        output_path = os.path.join(ASSETS_DIR, f"lt_{safe_name}.mp4")

    # Escape text for FFmpeg
    name_escaped = name.replace("'", "").replace(":", "\\:")
    title_escaped = title.replace("'", "").replace(":", "\\:")

    x_pos = 60 if position == "left" else f"{W - 500}"
    bar_x = 40 if position == "left" else f"{W - 520}"

    filter_complex = (
        f"color=c={BRAND_BG}@0:s={W}x{H}:d={duration}:r={FPS},"
        f"format=yuva420p[transparent];"

        f"[transparent]"
        # Dark semi-transparent box
        f"drawbox=x={int(bar_x) if position == 'left' else bar_x}:y={H-180}:w=480:h=120:"
        f"color={BRAND_BG}@0.85:t=fill:"
        f"enable='1',"

        # Cyan accent bar (left edge of box)
        f"drawbox=x={int(bar_x) if position == 'left' else bar_x}:y={H-180}:w=4:h=120:"
        f"color={BRAND_BLUE}@1.0:t=fill,"

        # Name text
        f"drawtext=text='{name_escaped}':"
        f"fontsize=36:"
        f"fontcolor={BRAND_WHITE}:"
        f"x={x_pos}:y={H-165}:"
        f"alpha='if(lt(t,0.3),t/0.3,if(gt(t,{duration-0.3}),({duration}-t)/0.3,1))',"

        # Title text
        f"drawtext=text='{title_escaped}':"
        f"fontsize=22:"
        f"fontcolor={BRAND_GRAY}:"
        f"x={x_pos}:y={H-120}:"
        f"alpha='if(lt(t,0.5),max(0,(t-0.2)/0.3),if(gt(t,{duration-0.3}),({duration}-t)/0.3,1))'"
        f"[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex", filter_complex,
        "-map", "[out]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-shortest",
        output_path,
    ]

    if _run_ffmpeg(cmd, f"lower third: {name}"):
        print(f"[BRAND-GFX] Lower third generated: {name}")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# 3. DATA VISUALIZATION CARDS (stat callouts)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_data_card(
    stat: str,
    label: str,
    output_path: Optional[str] = None,
    duration: float = 4.0,
    accent_color: str = BRAND_BLUE,
) -> str:
    """
    Generate a data visualization card for key statistics.

    Visual:
      - Full screen darkens slightly
      - Large stat number in cyan/amber (72px) with count-up feel
      - Label text below in white (28px)
      - Horizontal line separators animate in
      - Subtle glow/pulse effect on the number

    Args:
        stat: The number/stat to display (e.g. "3.2 MILLION", "28%", "90 DAYS")
        label: Description below (e.g. "people affected in 2025")
    """
    if output_path is None:
        safe_stat = stat.lower().replace(" ", "_").replace("%", "pct").replace(".", "")
        output_path = os.path.join(ASSETS_DIR, f"data_{safe_stat}.mp4")

    stat_escaped = stat.replace("'", "").replace(":", "\\:")
    label_escaped = label.replace("'", "").replace(":", "\\:")

    filter_complex = (
        # Dark background
        f"color=c={BRAND_BG}:s={W}x{H}:d={duration}:r={FPS}[bg];"

        # Subtle grain
        f"nullsrc=s={W}x{H}:d={duration}:r={FPS},"
        f"geq=random(1)*15:128:128,format=yuv420p[grain];"

        f"[bg][grain]blend=all_mode=addition:all_opacity=0.06[textured];"

        # Top decorative line
        f"[textured]drawbox="
        f"x='max(0,{W//2}-min({W//3},(t/0.8)*{W//3}))':"
        f"y={H//2 - 80}:w='min({2*W//3},(t/0.8)*{2*W//3})':h=1:"
        f"color={accent_color}@0.6:t=fill,"

        # Bottom decorative line
        f"drawbox="
        f"x='max(0,{W//2}-min({W//3},(t/0.8)*{W//3}))':"
        f"y={H//2 + 60}:w='min({2*W//3},(t/0.8)*{2*W//3})':h=1:"
        f"color={accent_color}@0.6:t=fill,"

        # Main stat number
        f"drawtext=text='{stat_escaped}':"
        f"fontsize=96:"
        f"fontcolor={accent_color}:"
        f"x=(w-text_w)/2:"
        f"y=(h/2)-50:"
        f"alpha='if(lt(t,0.4),t/0.4,1)*if(gt(t,{duration-0.4}),({duration}-t)/0.4,1)',"

        # Label text
        f"drawtext=text='{label_escaped}':"
        f"fontsize=28:"
        f"fontcolor={BRAND_WHITE}:"
        f"x=(w-text_w)/2:"
        f"y=(h/2)+30:"
        f"alpha='if(lt(t,0.6),max(0,(t-0.2)/0.4),1)*if(gt(t,{duration-0.4}),({duration}-t)/0.4,1)'"
        f"[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex", filter_complex,
        "-map", "[out]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-shortest",
        output_path,
    ]

    if _run_ffmpeg(cmd, f"data card: {stat}"):
        print(f"[BRAND-GFX] Data card generated: {stat}")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# 4. SCENE TRANSITIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_glitch_transition(
    output_path: Optional[str] = None,
    duration: float = 0.5,
) -> str:
    """
    Generate a glitch/digital transition clip.

    Visual:
      - Quick RGB split / chromatic aberration look
      - Flash of cyan accent color
      - Digital noise burst
      - Resolves to black

    Used between major story sections.
    """
    if output_path is None:
        output_path = os.path.join(ASSETS_DIR, "transition_glitch.mp4")

    # Simpler glitch: noise burst that fades to dark
    filter_complex = (
        f"color=c={BRAND_BG}:s={W}x{H}:d={duration}:r={FPS}[bg];"
        f"nullsrc=s={W}x{H}:d={duration}:r={FPS},"
        f"geq=random(1)*255:128:128,format=yuv420p[noise];"
        f"[bg][noise]blend=all_mode=addition:"
        f"all_opacity=0.4[noisy];"
        f"[noisy]fade=t=out:st=0.1:d={duration - 0.1}[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex", filter_complex,
        "-map", "[out]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-shortest",
        output_path,
    ]

    if _run_ffmpeg(cmd, "glitch transition"):
        print(f"[BRAND-GFX] Glitch transition generated")
    return output_path


def generate_hover_hook(
    line1: str = "HALF HER TEAM.",
    line2: str = "GONE.",
    stat: str = "3.2 MILLION",
    output_path: Optional[str] = None,
    duration: float = 3.0,
) -> str:
    """
    Generate a 3-second silent visual hook for YouTube hover preview.

    When viewers hover over a thumbnail on desktop or scroll on mobile,
    YouTube auto-plays the first ~3 seconds with no sound. This clip is
    designed to be compelling WITHOUT audio:

      0.0-1.0s: Bold text punch — "HALF HER TEAM. GONE." on dark bg
      1.0-2.0s: Quick flash to cyan accent color, then dark
      2.0-3.0s: Data stat flash — "3.2 MILLION" in cyan, fades

    After this 3s hook, the voiceover and main content begin.
    """
    if output_path is None:
        output_path = os.path.join(ASSETS_DIR, "hover_hook.mp4")

    line1_escaped = line1.replace("'", "").replace(":", "\\:")
    line2_escaped = line2.replace("'", "").replace(":", "\\:")
    stat_escaped = stat.replace("'", "").replace(":", "\\:")

    filter_complex = (
        # Dark background
        f"color=c={BRAND_BG}:s={W}x{H}:d={duration}:r={FPS}[bg];"

        # Grain texture
        f"nullsrc=s={W}x{H}:d={duration}:r={FPS},"
        f"geq=random(1)*18:128:128,format=yuv420p[grain];"

        f"[bg][grain]blend=all_mode=addition:all_opacity=0.07[textured];"

        # Phase 1 (0-1s): Bold text slam
        f"[textured]drawtext=text='{line1_escaped}':"
        f"fontsize=84:fontcolor={BRAND_WHITE}:"
        f"x=(w-text_w)/2:y=(h/2)-60:"
        f"alpha='if(lt(t,0.05),0,if(lt(t,0.9),1,max(0,1-(t-0.9)/0.1)))':"
        f"enable='between(t,0,1.0)',"

        f"drawtext=text='{line2_escaped}':"
        f"fontsize=96:fontcolor={BRAND_BLUE}:"
        f"x=(w-text_w)/2:y=(h/2)+40:"
        f"alpha='if(lt(t,0.15),0,if(lt(t,0.9),1,max(0,1-(t-0.9)/0.1)))':"
        f"enable='between(t,0,1.0)',"

        # Phase 2 (1-2s): Horizontal cyan accent line flash
        f"drawbox=x=0:y={H//2 - 1}:w={W}:h=3:"
        f"color={BRAND_BLUE}@1.0:t=fill:"
        f"enable='between(t,1.0,1.3)',"

        # Phase 3 (2-3s): Stat number flash
        f"drawtext=text='{stat_escaped}':"
        f"fontsize=110:fontcolor={BRAND_BLUE}:"
        f"x=(w-text_w)/2:y=(h/2)-30:"
        f"alpha='if(lt(t,2.0),0,if(lt(t,2.2),(t-2.0)/0.2,if(lt(t,2.8),1,max(0,1-(t-2.8)/0.2))))':"
        f"enable='between(t,1.8,3.0)'"
        f"[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex", filter_complex,
        "-map", "[out]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-shortest",
        output_path,
    ]

    if _run_ffmpeg(cmd, "hover hook"):
        print(f"[BRAND-GFX] Hover hook generated: {output_path}")
    return output_path


def generate_fade_transition(
    output_path: Optional[str] = None,
    duration: float = 0.8,
    color: str = BRAND_BG,
) -> str:
    """Simple branded fade to/from dark."""
    if output_path is None:
        output_path = os.path.join(ASSETS_DIR, "transition_fade.mp4")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={color}:s={W}x{H}:d={duration}:r={FPS}",
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-shortest",
        output_path,
    ]

    if _run_ffmpeg(cmd, "fade transition"):
        print(f"[BRAND-GFX] Fade transition generated")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# 5. END SCREEN (20 seconds - YouTube standard)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_end_screen(
    next_episode_title: str = "NEXT EPISODE",
    output_path: Optional[str] = None,
    duration: float = 20.0,
) -> str:
    """
    Generate a 20-second end screen (YouTube standard duration for end cards).

    Visual:
      - Dark branded background with subtle animation
      - "SUBSCRIBE" CTA with animated accent ring
      - Next episode teaser card placeholder (right side)
      - V-REAL AI logo centered at top
      - "More episodes" text

    YouTube overlays its own end screen elements on top of this,
    so we provide the visual backdrop.
    """
    if output_path is None:
        output_path = os.path.join(ASSETS_DIR, "end_screen.mp4")

    next_escaped = next_episode_title.replace("'", "").replace(":", "\\:")

    filter_complex = (
        # Background
        f"color=c={BRAND_BG}:s={W}x{H}:d={duration}:r={FPS}[bg];"

        # Grain
        f"nullsrc=s={W}x{H}:d={duration}:r={FPS},"
        f"geq=random(1)*12:128:128,format=yuv420p[grain];"

        f"[bg][grain]blend=all_mode=addition:all_opacity=0.05[textured];"

        # V-REAL AI header
        f"[textured]drawtext=text='V - R E A L   A I':"
        f"fontsize=48:fontcolor={BRAND_WHITE}:"
        f"x=(w-text_w)/2:y=80:"
        f"alpha='min(1,t/0.5)',"

        # Tagline
        f"drawtext=text='INSIGHTS THAT DETERMINE OUTCOMES':"
        f"fontsize=20:fontcolor={BRAND_GRAY}:"
        f"x=(w-text_w)/2:y=140:"
        f"alpha='if(lt(t,0.3),0,min(1,(t-0.3)/0.5))',"

        # Decorative line under header
        f"drawbox=x={W//2 - 150}:y=175:w=300:h=1:"
        f"color={BRAND_BLUE}@0.5:t=fill,"

        # Left side: Subscribe circle placeholder
        # (YouTube's end screen element goes here — we just provide visual context)
        f"drawtext=text='SUBSCRIBE':"
        f"fontsize=28:fontcolor={BRAND_BLUE}:"
        f"x={W//4 - 60}:y={H//2 + 20}:"
        f"alpha='if(lt(t,1.0),0,min(1,(t-1.0)/0.5))',"

        # Subscribe ring (circle approximation with drawbox)
        f"drawbox=x={W//4 - 100}:y={H//2 - 80}:w=200:h=200:"
        f"color={BRAND_BLUE}@0.3:t=3:"
        f"enable='gte(t,0.8)',"

        # Right side: Next episode card
        f"drawbox=x={W*3//4 - 160}:y={H//2 - 90}:w=320:h=180:"
        f"color={BRAND_BLUE}@0.15:t=fill:"
        f"enable='gte(t,0.5)',"
        f"drawbox=x={W*3//4 - 160}:y={H//2 - 90}:w=320:h=180:"
        f"color={BRAND_BLUE}@0.5:t=2:"
        f"enable='gte(t,0.5)',"

        f"drawtext=text='NEXT':"
        f"fontsize=22:fontcolor={BRAND_GRAY}:"
        f"x={W*3//4 - 30}:y={H//2 - 50}:"
        f"alpha='if(lt(t,1.2),0,min(1,(t-1.2)/0.5))',"

        f"drawtext=text='{next_escaped}':"
        f"fontsize=26:fontcolor={BRAND_WHITE}:"
        f"x={W*3//4 - 80}:y={H//2}:"
        f"alpha='if(lt(t,1.5),0,min(1,(t-1.5)/0.5))',"

        # Bottom text
        f"drawtext=text='More documentaries at V-Real AI':"
        f"fontsize=20:fontcolor={BRAND_GRAY}:"
        f"x=(w-text_w)/2:y={H - 60}:"
        f"alpha='if(lt(t,2.0),0,min(1,(t-2.0)/0.5))'"
        f"[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000",
        "-filter_complex", filter_complex,
        "-map", "[out]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast",
        "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration), "-shortest",
        output_path,
    ]

    if _run_ffmpeg(cmd, "end screen"):
        print(f"[BRAND-GFX] End screen generated")
    return output_path


# ═══════════════════════════════════════════════════════════════════════════════
# 6. GENERATE ALL EP001 BRANDED ASSETS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_ep001_assets() -> dict:
    """Generate all branded assets needed for EP001 'The Shift'."""
    ep_dir = os.path.expanduser("~/youtube-empire/assets/ep001/brand")
    os.makedirs(ep_dir, exist_ok=True)

    assets = {}

    print("\n" + "=" * 60)
    print("  GENERATING EP001 BRAND ASSETS")
    print("=" * 60)

    # 1. Intro
    print("\n--- Generating animated intro ---")
    assets["intro"] = generate_intro(
        os.path.join(ep_dir, "intro.mp4")
    )

    # 2. Lower thirds for characters
    print("\n--- Generating lower thirds ---")
    characters = [
        ("SARAH CHEN", "Marketing Strategist"),
        ("MIKE RODRIGUEZ", "Legal Researcher - 18 Years"),
        ("DAVID PARK", "Customer Service Manager"),
    ]
    assets["lower_thirds"] = []
    for name, title in characters:
        lt = generate_lower_third(name, title, os.path.join(
            ep_dir, f"lt_{name.lower().replace(' ', '_')}.mp4"
        ))
        assets["lower_thirds"].append(lt)

    # 3. Data cards for key statistics
    print("\n--- Generating data cards ---")
    stats = [
        ("3.2 MILLION", "people experienced this in 2025", BRAND_BLUE),
        ("28%", "salary increase for early adopters", BRAND_AMBER),
        ("43%", "who rejected AI faced job loss within 6 months", BRAND_BLUE),
        ("48%", "salary increase", BRAND_AMBER),
        ("90 DAYS", "the window that determines your outcome", BRAND_BLUE),
        ("80 / 20", "AI handles 80% - you own the critical 20%", BRAND_AMBER),
    ]
    assets["data_cards"] = []
    for stat, label, color in stats:
        dc = generate_data_card(stat, label, os.path.join(
            ep_dir, f"data_{stat.lower().replace(' ', '_').replace('%', 'pct').replace('.', '').replace('/', '_')}.mp4"
        ), accent_color=color)
        assets["data_cards"].append(dc)

    # 4. Hover hook (3s silent visual for YouTube preview)
    print("\n--- Generating hover hook ---")
    assets["hover_hook"] = generate_hover_hook(
        line1="HALF HER TEAM.",
        line2="GONE.",
        stat="3.2 MILLION",
        output_path=os.path.join(ep_dir, "hover_hook.mp4"),
    )

    # 5. Transitions
    print("\n--- Generating transitions ---")
    assets["transition_glitch"] = generate_glitch_transition(
        os.path.join(ep_dir, "transition_glitch.mp4")
    )
    assets["transition_fade"] = generate_fade_transition(
        os.path.join(ep_dir, "transition_fade.mp4")
    )

    # 5. End screen
    print("\n--- Generating end screen ---")
    assets["end_screen"] = generate_end_screen(
        "EP002: THE PRICE OF WAITING",
        os.path.join(ep_dir, "end_screen.mp4"),
    )

    print("\n" + "=" * 60)
    print(f"  ALL EP001 ASSETS GENERATED IN: {ep_dir}")
    print("=" * 60)

    # Write manifest
    manifest_path = os.path.join(ep_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(assets, f, indent=2)
    print(f"  Manifest: {manifest_path}")

    return assets


if __name__ == "__main__":
    generate_ep001_assets()
