#!/usr/bin/env python3
"""
EP001 Preview Animatic Builder

Generates a preview video using FFmpeg with:
- Dark branded backgrounds per scene
- Text overlays showing scene descriptions
- Section titles (Hook, Sarah, Mike, David, Framework, Close)
- Correct timing matching the voiceover brief

This is a structural preview — no real voiceover or footage needed.
"""
import subprocess
import os
import sys

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp_animatic")
os.makedirs(TEMP_DIR, exist_ok=True)

# Brand colors
BG = "0A0F1E"
ACCENT = "00D4FF"
TEXT = "FFFFFF"
SUBTLE = "888888"

W, H, FPS = 1920, 1080, 30

# Scene definitions: (scene_num, title, description, start_sec, duration_sec, bg_hex)
SCENES = [
    (1, "HOOK", "Sarah Chen's phone buzzed at 9:47 AM", 0, 30, "0A0F1E"),
    (2, "SETUP", "3.2 million people in 2025", 30, 75, "0F1428"),
    (3, "SARAH", "She did not wait for permission", 105, 90, "0A1A2E"),
    (4, "MIKE", "18 years of legal research", 195, 90, "1A0A0A"),
    (5, "DAVID", "He saw what others missed", 285, 75, "0A1A0A"),
    (6, "THE 90-DAY RULE", "Experiment - Complement - Bridge", 360, 150, "0F0A28"),
    (7, "BRAND CLOSE", "This is V-Real AI", 510, 30, "0A0F1E"),
]

# Text overlays that appear at specific moments
TEXT_OVERLAYS = [
    ("3.2 million people experienced this in 2025", 30, 35),
    ("48%% salary increase", 295, 300),
    ("Days 1-30\\: Immediate Experimentation", 370, 378),
    ("Days 31-60\\: Identify Your Complement", 410, 418),
    ("Days 61-90\\: Strategic Positioning", 450, 458),
]

TOTAL_DURATION = 540  # 9 minutes


def create_scene_clip(scene_num, title, desc, duration, bg_hex):
    """Create a single scene clip with title and description text."""
    out = os.path.join(TEMP_DIR, f"scene_{scene_num:02d}.mp4")

    # Escape special chars for drawtext
    safe_title = title.replace("'", "").replace(":", "\\:").replace("%", "%%")
    safe_desc = desc.replace("'", "").replace(":", "\\:").replace("%", "%%")

    # Build filter: background + title + description + scene number
    vf = (
        f"color=c=0x{bg_hex}:s={W}x{H}:d={duration}:r={FPS},"
        f"drawtext=text='{safe_title}':fontsize=72:fontcolor=0x{ACCENT}:x=(w-text_w)/2:y=h/3-36,"
        f"drawtext=text='{safe_desc}':fontsize=36:fontcolor=0x{TEXT}:x=(w-text_w)/2:y=h/2+20,"
        f"drawtext=text='Scene {scene_num} / 7':fontsize=24:fontcolor=0x{SUBTLE}:x=w-text_w-40:y=h-60,"
        f"drawtext=text='EP001 — The Shift | ANIMATIC PREVIEW':fontsize=20:fontcolor=0x{SUBTLE}:x=40:y=h-60"
    )

    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
         "-f", "lavfi", "-i", f"color=c=0x{bg_hex}:s={W}x{H}:d={duration}:r={FPS}",
         "-vf", vf.split("color=")[1].split(",", 1)[1] if "," in vf else "",
         "-t", str(duration),
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k",
         out],
        capture_output=True, text=True,
    )

    # Simpler approach: just create video with filter_complex
    subprocess.run(
        ["ffmpeg", "-y",
         "-f", "lavfi", "-i", f"color=c=0x{bg_hex}:s={W}x{H}:d={duration}:r={FPS}",
         "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo",
         "-vf", (
             f"drawtext=text='{safe_title}':fontsize=72:fontcolor=0x{ACCENT}:x=(w-text_w)/2:y=h/3-36,"
             f"drawtext=text='{safe_desc}':fontsize=36:fontcolor=0x{TEXT}:x=(w-text_w)/2:y=h/2+20,"
             f"drawtext=text='Scene {scene_num} / 7':fontsize=24:fontcolor=0x{SUBTLE}:x=w-text_w-40:y=h-60,"
             f"drawtext=text='EP001 The Shift | ANIMATIC PREVIEW':fontsize=20:fontcolor=0x{SUBTLE}:x=40:y=h-60"
         ),
         "-t", str(duration), "-shortest",
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k",
         out],
        check=True, capture_output=True,
    )

    print(f"  Scene {scene_num}: {title} ({duration}s)")
    return out


def main():
    print("=" * 50)
    print("  EP001 ANIMATIC PREVIEW BUILDER")
    print("=" * 50)

    # Step 1: Create individual scene clips
    print("\nCreating scenes...")
    scene_files = []
    for scene_num, title, desc, start, dur, bg in SCENES:
        path = create_scene_clip(scene_num, title, desc, dur, bg)
        scene_files.append(path)

    # Step 2: Create concat file
    concat_path = os.path.join(TEMP_DIR, "concat.txt")
    with open(concat_path, "w") as f:
        for sf in scene_files:
            f.write(f"file '{sf}'\n")

    # Step 3: Concatenate all scenes
    print("\nConcatenating scenes...")
    concat_out = os.path.join(TEMP_DIR, "concat.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_path,
         "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k",
         concat_out],
        check=True, capture_output=True,
    )

    # Step 4: Add timed text overlays
    print("Adding text overlays...")
    current = concat_out
    for i, (text, start, end) in enumerate(TEXT_OVERLAYS):
        overlay_out = os.path.join(TEMP_DIR, f"overlay_{i}.mp4")
        safe_text = text.replace("'", "\\'")
        fade_dur = 0.5
        subprocess.run(
            ["ffmpeg", "-y", "-i", current,
             "-vf", (
                 f"drawtext=text='{safe_text}'"
                 f":fontsize=56:fontcolor=0x{ACCENT}"
                 f":x=(w-text_w)/2:y=h*3/4"
                 f":enable='between(t,{start},{end})'"
                 f":alpha='if(lt(t-{start},{fade_dur}),(t-{start})/{fade_dur},if(lt({end}-t,{fade_dur}),({end}-t)/{fade_dur},1))'"
             ),
             "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
             "-c:a", "copy",
             overlay_out],
            check=True, capture_output=True,
        )
        current = overlay_out

    # Step 5: Final output
    final_out = os.path.join(OUTPUT_DIR, "ep001-animatic-preview.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-i", current,
         "-c:v", "libx264", "-preset", "medium", "-crf", "23",
         "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k",
         final_out],
        check=True, capture_output=True,
    )

    size_mb = os.path.getsize(final_out) / (1024 * 1024)
    print(f"\n✓ Animatic preview: {final_out}")
    print(f"  Size: {size_mb:.1f} MB")
    print(f"  Duration: {TOTAL_DURATION}s ({TOTAL_DURATION/60:.0f} min)")
    print(f"\nThis shows the video structure. Replace with real assets using produce_ep001.py")


if __name__ == "__main__":
    main()
