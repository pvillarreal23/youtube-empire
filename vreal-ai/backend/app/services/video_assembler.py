"""
Video Assembly Service — FFmpeg-based automated video production

Replaces manual CapCut editing. Takes voice audio + video clips + music
and assembles a complete V-Real AI episode programmatically.

Assembly order (per production bible):
  1. Voice audio (foundation)
  2. Video clips (matched to script scenes)
  3. Background music (ducked under voice)
  4. Text overlays (kinetic typography)
  5. SFX and transitions

Audio targets:
  - Voice: -14 to -16 LUFS
  - Music: -25 to -30 LUFS, ducked to -35 under voice
  - Final master: -14 LUFS integrated
"""
from __future__ import annotations

import os
import json
import subprocess
import tempfile
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ── Configuration ────────────────────────────────────────────────────────────

OUTPUT_DIR = os.getenv("VIDEO_OUTPUT_DIR", os.path.expanduser("~/youtube-empire/output"))
TEMP_DIR = os.getenv("VIDEO_TEMP_DIR", os.path.expanduser("~/youtube-empire/output/temp"))

# V-Real AI brand colors
BRAND = {
    "bg": "#0A0F1E",
    "accent_blue": "#00D4FF",
    "accent_amber": "#FFB347",
    "text_primary": "#FFFFFF",
    "text_secondary": "#C8C8C8",
    "font": "Inter",
    "font_bold": "Inter-Bold",
}

# Video specs from production bible
VIDEO_SPECS = {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "codec": "libx264",
    "preset": "slow",
    "crf": 18,           # High quality
    "pix_fmt": "yuv420p",
    "audio_codec": "aac",
    "audio_bitrate": "192k",
    "audio_sample_rate": 48000,
}

# Audio levels (LUFS targets)
AUDIO_LEVELS = {
    "voice_lufs": -15,
    "music_lufs": -28,
    "music_duck_lufs": -35,
    "sfx_lufs": -20,
    "master_lufs": -14,
}


# ── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class SceneClip:
    """A single video clip matched to a script scene."""
    scene_number: int
    video_path: str          # Path to video file (Kling AI, stock, etc.)
    start_time: float        # Start time in the voice timeline (seconds)
    end_time: float          # End time in the voice timeline (seconds)
    clip_in: float = 0.0     # Trim start within the clip
    clip_out: float = 0.0    # Trim end (0 = use full clip)
    motion: str = "none"     # "zoom_in", "zoom_out", "pan_left", "pan_right", "ken_burns", "none"
    transition_in: str = "fade"   # "fade", "cut", "dissolve"
    transition_out: str = "fade"
    description: str = ""


@dataclass
class TextOverlay:
    """On-screen text element."""
    text: str
    start_time: float
    end_time: float
    position: str = "center"      # "center", "lower_third", "upper", "full_screen"
    style: str = "default"        # "default", "kinetic", "data_viz", "quote"
    font_size: int = 48
    color: str = BRAND["text_primary"]
    bg_color: Optional[str] = None
    animation: str = "fade_in"    # "fade_in", "type_on", "slide_up", "pop"


@dataclass
class AssemblyProject:
    """Complete video assembly specification."""
    episode_id: str
    title: str
    voice_audio_path: str
    music_path: Optional[str] = None
    scenes: list[SceneClip] = field(default_factory=list)
    text_overlays: list[TextOverlay] = field(default_factory=list)
    intro_path: Optional[str] = None       # Pre-rendered brand intro
    outro_path: Optional[str] = None       # Pre-rendered brand outro
    output_filename: Optional[str] = None


# ── Core Assembly Engine ─────────────────────────────────────────────────────

def ensure_dirs():
    """Create output and temp directories."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(TEMP_DIR, exist_ok=True)


def get_duration(file_path: str) -> float:
    """Get duration of audio/video file in seconds."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path],
        capture_output=True, text=True,
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def normalize_audio(input_path: str, output_path: str, target_lufs: float = -14) -> str:
    """
    Two-pass loudness normalization to target LUFS.
    This is critical — voice must be -14 to -16 LUFS, music must be -28 LUFS.
    """
    # Pass 1: Measure current loudness
    measure = subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:print_format=json",
            "-f", "null", "-"
        ],
        capture_output=True, text=True,
    )

    # Parse measured values from stderr
    stderr = measure.stderr
    try:
        json_start = stderr.rfind("{")
        json_end = stderr.rfind("}") + 1
        measured = json.loads(stderr[json_start:json_end])
    except (json.JSONDecodeError, ValueError):
        # Fallback: simple volume adjustment
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-af",
             f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
             "-ar", str(VIDEO_SPECS["audio_sample_rate"]), output_path],
            check=True, capture_output=True,
        )
        return output_path

    # Pass 2: Apply measured values for precise normalization
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-af", (
                f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:"
                f"measured_I={measured['input_i']}:"
                f"measured_TP={measured['input_tp']}:"
                f"measured_LRA={measured['input_lra']}:"
                f"measured_thresh={measured['input_thresh']}:"
                f"offset={measured['target_offset']}:"
                f"linear=true:print_format=summary"
            ),
            "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
            output_path,
        ],
        check=True, capture_output=True,
    )
    return output_path


def create_color_clip(duration: float, output_path: str, color: str = BRAND["bg"]) -> str:
    """Create a solid color video clip (used as fallback/background)."""
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i",
            f"color=c={color}:s={VIDEO_SPECS['width']}x{VIDEO_SPECS['height']}:d={duration}:r={VIDEO_SPECS['fps']}",
            "-c:v", VIDEO_SPECS["codec"], "-preset", "ultrafast",
            "-pix_fmt", VIDEO_SPECS["pix_fmt"],
            output_path,
        ],
        check=True, capture_output=True,
    )
    return output_path


def apply_motion(input_path: str, output_path: str, motion: str, duration: float) -> str:
    """Apply Ken Burns / zoom / pan motion to a clip (the 'Never Boring' rule)."""
    w, h = VIDEO_SPECS["width"], VIDEO_SPECS["height"]

    motion_filters = {
        "zoom_in": f"scale=8000:-1,zoompan=z='min(zoom+0.0015,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration * VIDEO_SPECS['fps'])}:s={w}x{h}:fps={VIDEO_SPECS['fps']}",
        "zoom_out": f"scale=8000:-1,zoompan=z='if(lte(zoom,1.0),1.5,max(1.001,zoom-0.0015))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={int(duration * VIDEO_SPECS['fps'])}:s={w}x{h}:fps={VIDEO_SPECS['fps']}",
        "pan_left": f"scale=8000:-1,zoompan=z='1.2':x='iw/2-(iw/zoom/2)-{int(0.1*w)}*on/{int(duration*VIDEO_SPECS['fps'])}':y='ih/2-(ih/zoom/2)':d={int(duration * VIDEO_SPECS['fps'])}:s={w}x{h}:fps={VIDEO_SPECS['fps']}",
        "pan_right": f"scale=8000:-1,zoompan=z='1.2':x='iw/2-(iw/zoom/2)+{int(0.1*w)}*on/{int(duration*VIDEO_SPECS['fps'])}':y='ih/2-(ih/zoom/2)':d={int(duration * VIDEO_SPECS['fps'])}:s={w}x{h}:fps={VIDEO_SPECS['fps']}",
        "ken_burns": f"scale=8000:-1,zoompan=z='min(zoom+0.001,1.3)':x='iw/2-(iw/zoom/2)+{int(0.05*w)}*on/{int(duration*VIDEO_SPECS['fps'])}':y='ih/2-(ih/zoom/2)':d={int(duration * VIDEO_SPECS['fps'])}:s={w}x{h}:fps={VIDEO_SPECS['fps']}",
    }

    if motion not in motion_filters:
        # No motion — just scale to fit
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path,
             "-vf", f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={BRAND['bg']}",
             "-c:v", VIDEO_SPECS["codec"], "-preset", "fast",
             "-t", str(duration), "-an", output_path],
            check=True, capture_output=True,
        )
        return output_path

    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path,
         "-vf", motion_filters[motion],
         "-c:v", VIDEO_SPECS["codec"], "-preset", "fast",
         "-an", output_path],
        check=True, capture_output=True,
    )
    return output_path


def duck_music_under_voice(
    music_path: str,
    voice_path: str,
    output_path: str,
    music_level: float = AUDIO_LEVELS["music_lufs"],
    duck_level: float = AUDIO_LEVELS["music_duck_lufs"],
) -> str:
    """
    Auto-duck background music under voice audio.
    Music plays at -28 LUFS normally, drops to -35 LUFS when voice is active.
    """
    voice_duration = get_duration(voice_path)

    # Normalize music to target level first
    music_norm = os.path.join(TEMP_DIR, "music_normalized.wav")
    normalize_audio(music_path, music_norm, target_lufs=music_level)

    # Use sidechaincompress to duck music when voice is present
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", music_norm,
            "-i", voice_path,
            "-filter_complex",
            (
                f"[0:a]aloop=loop=-1:size={int(48000 * voice_duration)},atrim=0:{voice_duration}[music_loop];"
                f"[music_loop][1:a]sidechaincompress=threshold=0.02:ratio=8:attack=50:release=300:level_sc=1[ducked]"
            ),
            "-map", "[ducked]",
            "-t", str(voice_duration),
            "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
            output_path,
        ],
        check=True, capture_output=True,
    )
    return output_path


def add_text_overlay(
    input_path: str,
    output_path: str,
    overlay: TextOverlay,
) -> str:
    """Add a single text overlay to a video clip."""
    # Position mapping
    positions = {
        "center": f"x=(w-text_w)/2:y=(h-text_h)/2",
        "lower_third": f"x=(w-text_w)/2:y=h-text_h-80",
        "upper": f"x=(w-text_w)/2:y=80",
        "full_screen": f"x=(w-text_w)/2:y=(h-text_h)/2",
    }
    pos = positions.get(overlay.position, positions["center"])

    # Build drawtext filter
    escaped_text = overlay.text.replace("'", "\\'").replace(":", "\\:")

    drawtext = (
        f"drawtext=text='{escaped_text}'"
        f":fontsize={overlay.font_size}"
        f":fontcolor={overlay.color}"
        f":{pos}"
        f":enable='between(t,{overlay.start_time},{overlay.end_time})'"
    )

    # Add background box if specified
    if overlay.bg_color:
        drawtext += f":box=1:boxcolor={overlay.bg_color}@0.7:boxborderw=20"

    # Add fade animation
    if overlay.animation == "fade_in":
        fade_dur = min(0.5, (overlay.end_time - overlay.start_time) / 4)
        drawtext += f":alpha='if(lt(t,{overlay.start_time}),0,if(lt(t,{overlay.start_time + fade_dur}),(t-{overlay.start_time})/{fade_dur},if(lt(t,{overlay.end_time - fade_dur}),1,({overlay.end_time}-t)/{fade_dur})))'"

    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-vf", drawtext,
         "-c:v", VIDEO_SPECS["codec"], "-preset", "fast",
         "-c:a", "copy", output_path],
        check=True, capture_output=True,
    )
    return output_path


# ── Main Assembly Pipeline ───────────────────────────────────────────────────

def assemble_video(project: AssemblyProject) -> str:
    """
    Main assembly pipeline. Takes an AssemblyProject and produces a final MP4.

    Steps:
      1. Normalize voice audio to -14 LUFS
      2. Prepare each video scene (trim, motion, scale)
      3. Concatenate scenes into continuous video track
      4. Mix voice + ducked music
      5. Apply text overlays
      6. Add intro/outro if provided
      7. Final loudness normalization to -14 LUFS
      8. Export final MP4

    Returns: path to final output file.
    """
    ensure_dirs()

    episode_temp = os.path.join(TEMP_DIR, project.episode_id)
    os.makedirs(episode_temp, exist_ok=True)

    voice_duration = get_duration(project.voice_audio_path)

    print(f"[ASSEMBLER] Starting assembly: {project.title}")
    print(f"[ASSEMBLER] Voice duration: {voice_duration:.1f}s")
    print(f"[ASSEMBLER] Scenes: {len(project.scenes)}")

    # ── Step 1: Normalize voice ──────────────────────────────────────────
    print("[ASSEMBLER] Step 1/7: Normalizing voice audio...")
    voice_norm = os.path.join(episode_temp, "voice_normalized.wav")
    normalize_audio(project.voice_audio_path, voice_norm, AUDIO_LEVELS["voice_lufs"])

    # ── Step 2: Prepare scene clips ──────────────────────────────────────
    print("[ASSEMBLER] Step 2/7: Preparing scene clips...")
    prepared_scenes = []

    if not project.scenes:
        # No scenes provided — create branded background for full duration
        bg_clip = os.path.join(episode_temp, "background.mp4")
        create_color_clip(voice_duration, bg_clip)
        prepared_scenes.append(bg_clip)
    else:
        # Sort scenes by start time
        sorted_scenes = sorted(project.scenes, key=lambda s: s.start_time)

        for i, scene in enumerate(sorted_scenes):
            scene_dur = scene.end_time - scene.start_time

            # Fill gaps between scenes with branded background
            if i == 0 and scene.start_time > 0:
                gap_clip = os.path.join(episode_temp, f"gap_pre.mp4")
                create_color_clip(scene.start_time, gap_clip)
                prepared_scenes.append(gap_clip)
            elif i > 0:
                prev_end = sorted_scenes[i - 1].end_time
                if scene.start_time > prev_end + 0.1:
                    gap_clip = os.path.join(episode_temp, f"gap_{i}.mp4")
                    create_color_clip(scene.start_time - prev_end, gap_clip)
                    prepared_scenes.append(gap_clip)

            # Process the scene clip
            scene_out = os.path.join(episode_temp, f"scene_{i:03d}.mp4")

            if not os.path.exists(scene.video_path):
                print(f"[ASSEMBLER] WARNING: Missing clip {scene.video_path}, using background")
                create_color_clip(scene_dur, scene_out)
            else:
                # Trim clip to needed duration
                trimmed = os.path.join(episode_temp, f"scene_{i:03d}_trimmed.mp4")
                trim_start = scene.clip_in
                subprocess.run(
                    ["ffmpeg", "-y", "-ss", str(trim_start), "-i", scene.video_path,
                     "-t", str(scene_dur),
                     "-vf", f"scale={VIDEO_SPECS['width']}:{VIDEO_SPECS['height']}:force_original_aspect_ratio=decrease,pad={VIDEO_SPECS['width']}:{VIDEO_SPECS['height']}:(ow-iw)/2:(oh-ih)/2:color={BRAND['bg']}",
                     "-c:v", VIDEO_SPECS["codec"], "-preset", "fast",
                     "-an", trimmed],
                    check=True, capture_output=True,
                )

                # Apply motion effect
                if scene.motion != "none":
                    apply_motion(trimmed, scene_out, scene.motion, scene_dur)
                else:
                    shutil.move(trimmed, scene_out)

            prepared_scenes.append(scene_out)

        # Fill remaining time after last scene
        last_end = sorted_scenes[-1].end_time
        if last_end < voice_duration:
            tail_clip = os.path.join(episode_temp, "gap_tail.mp4")
            create_color_clip(voice_duration - last_end, tail_clip)
            prepared_scenes.append(tail_clip)

    # ── Step 3: Concatenate all scene clips ──────────────────────────────
    print("[ASSEMBLER] Step 3/7: Concatenating scenes...")
    concat_list = os.path.join(episode_temp, "concat.txt")
    with open(concat_list, "w") as f:
        for clip_path in prepared_scenes:
            f.write(f"file '{clip_path}'\n")

    video_concat = os.path.join(episode_temp, "video_concat.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
         "-c:v", VIDEO_SPECS["codec"], "-preset", "fast",
         "-pix_fmt", VIDEO_SPECS["pix_fmt"],
         "-an", video_concat],
        check=True, capture_output=True,
    )

    # ── Step 4: Mix audio (voice + ducked music) ─────────────────────────
    print("[ASSEMBLER] Step 4/7: Mixing audio...")
    if project.music_path and os.path.exists(project.music_path):
        ducked_music = os.path.join(episode_temp, "music_ducked.wav")
        duck_music_under_voice(project.music_path, voice_norm, ducked_music)

        # Mix voice + ducked music
        mixed_audio = os.path.join(episode_temp, "audio_mixed.wav")
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", voice_norm,
                "-i", ducked_music,
                "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[mixed]",
                "-map", "[mixed]",
                "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
                mixed_audio,
            ],
            check=True, capture_output=True,
        )
    else:
        mixed_audio = voice_norm

    # Final audio normalization
    final_audio = os.path.join(episode_temp, "audio_final.wav")
    normalize_audio(mixed_audio, final_audio, AUDIO_LEVELS["master_lufs"])

    # ── Step 5: Merge video + audio ──────────────────────────────────────
    print("[ASSEMBLER] Step 5/7: Merging video + audio...")
    merged = os.path.join(episode_temp, "merged.mp4")
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", video_concat,
            "-i", final_audio,
            "-c:v", "copy",
            "-c:a", VIDEO_SPECS["audio_codec"],
            "-b:a", VIDEO_SPECS["audio_bitrate"],
            "-shortest",
            merged,
        ],
        check=True, capture_output=True,
    )

    # ── Step 6: Apply text overlays ──────────────────────────────────────
    print("[ASSEMBLER] Step 6/7: Applying text overlays...")
    current_video = merged
    for i, overlay in enumerate(project.text_overlays):
        overlay_out = os.path.join(episode_temp, f"overlay_{i:03d}.mp4")
        add_text_overlay(current_video, overlay_out, overlay)
        current_video = overlay_out

    # ── Step 7: Add intro/outro and export final ─────────────────────────
    print("[ASSEMBLER] Step 7/7: Final export...")
    output_name = project.output_filename or f"{project.episode_id}-final.mp4"
    final_output = os.path.join(OUTPUT_DIR, output_name)

    parts_to_concat = []
    if project.intro_path and os.path.exists(project.intro_path):
        parts_to_concat.append(project.intro_path)
    parts_to_concat.append(current_video)
    if project.outro_path and os.path.exists(project.outro_path):
        parts_to_concat.append(project.outro_path)

    if len(parts_to_concat) > 1:
        final_concat = os.path.join(episode_temp, "final_concat.txt")
        with open(final_concat, "w") as f:
            for p in parts_to_concat:
                f.write(f"file '{p}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", final_concat,
             "-c:v", VIDEO_SPECS["codec"], "-preset", VIDEO_SPECS["preset"],
             "-crf", str(VIDEO_SPECS["crf"]),
             "-pix_fmt", VIDEO_SPECS["pix_fmt"],
             "-c:a", VIDEO_SPECS["audio_codec"],
             "-b:a", VIDEO_SPECS["audio_bitrate"],
             final_output],
            check=True, capture_output=True,
        )
    else:
        # Re-encode with final quality settings
        subprocess.run(
            ["ffmpeg", "-y", "-i", current_video,
             "-c:v", VIDEO_SPECS["codec"], "-preset", VIDEO_SPECS["preset"],
             "-crf", str(VIDEO_SPECS["crf"]),
             "-pix_fmt", VIDEO_SPECS["pix_fmt"],
             "-c:a", VIDEO_SPECS["audio_codec"],
             "-b:a", VIDEO_SPECS["audio_bitrate"],
             final_output],
            check=True, capture_output=True,
        )

    # Report
    final_size_mb = os.path.getsize(final_output) / (1024 * 1024)
    final_duration = get_duration(final_output)
    print(f"[ASSEMBLER] ✓ Assembly complete: {final_output}")
    print(f"[ASSEMBLER]   Duration: {final_duration:.1f}s ({final_duration/60:.1f} min)")
    print(f"[ASSEMBLER]   Size: {final_size_mb:.1f} MB")

    return final_output


def create_project_from_script(
    episode_id: str,
    title: str,
    voice_audio: str,
    scene_descriptions: list[dict],
    clips_dir: str,
    music_path: Optional[str] = None,
) -> AssemblyProject:
    """
    Helper to create an AssemblyProject from a script's scene descriptions.

    scene_descriptions format (from script animation cues):
    [
        {
            "scene": 1,
            "description": "[ANIM: Dark screen, text fades in]",
            "start_time": 0.0,
            "end_time": 15.0,
            "motion": "zoom_in",
            "text_overlay": "The rules just changed."
        },
        ...
    ]
    """
    project = AssemblyProject(
        episode_id=episode_id,
        title=title,
        voice_audio_path=voice_audio,
        music_path=music_path,
    )

    for desc in scene_descriptions:
        scene_num = desc.get("scene", 0)

        # Look for matching clip in clips directory
        clip_patterns = [
            f"scene_{scene_num:02d}.*",
            f"scene-{scene_num:02d}.*",
            f"clip_{scene_num:02d}.*",
            f"{scene_num:02d}_*.*",
        ]

        clip_path = ""
        clips = Path(clips_dir)
        if clips.exists():
            for pattern in clip_patterns:
                matches = list(clips.glob(pattern))
                if matches:
                    clip_path = str(matches[0])
                    break

        project.scenes.append(SceneClip(
            scene_number=scene_num,
            video_path=clip_path,
            start_time=desc.get("start_time", 0),
            end_time=desc.get("end_time", 10),
            motion=desc.get("motion", "zoom_in"),
            description=desc.get("description", ""),
        ))

        # Add text overlay if specified
        if desc.get("text_overlay"):
            project.text_overlays.append(TextOverlay(
                text=desc["text_overlay"],
                start_time=desc.get("start_time", 0),
                end_time=min(desc.get("start_time", 0) + 5, desc.get("end_time", 10)),
                position=desc.get("text_position", "center"),
                style="kinetic",
                font_size=desc.get("font_size", 56),
            ))

    return project


def cleanup_temp(episode_id: str):
    """Remove temp files for a completed episode."""
    episode_temp = os.path.join(TEMP_DIR, episode_id)
    if os.path.exists(episode_temp):
        shutil.rmtree(episode_temp)
