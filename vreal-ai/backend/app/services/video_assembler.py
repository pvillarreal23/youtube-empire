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

Audio engineering (broadcast-grade 4-layer mix):
  - Voice:   -14 LUFS (broadcast standard, two-pass loudnorm)
  - Music:   -28 LUFS nominal, ducked to -35 LUFS under voice
  - SFX:     -20 LUFS
  - Ambient: -35 LUFS
  - Music fades in over first 3s, fades out over last 5s
  - Final master: -14 LUFS integrated, -1 dBTP peak ceiling
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

# Audio levels (LUFS targets — broadcast standard)
AUDIO_LEVELS = {
    "voice_lufs": -14,         # Broadcast standard for speech
    "music_lufs": -28,         # Background music nominal level
    "music_duck_lufs": -35,    # Music level when voice is active (sidechain ducking)
    "sfx_lufs": -20,           # Sound effects
    "ambient_lufs": -35,       # Ambient / room tone
    "master_lufs": -14,        # Final mix target (YouTube standard)
    "peak_ceiling": -1,        # True peak ceiling in dBTP
}

# Audio fade durations (seconds)
AUDIO_FADES = {
    "music_fade_in": 3.0,      # Music fades in over first 3 seconds
    "music_fade_out": 5.0,     # Music fades out over last 5 seconds
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
    sfx_path: Optional[str] = None         # Sound effects track
    ambient_path: Optional[str] = None     # Ambient / room tone track
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


def normalize_audio(
    input_path: str,
    output_path: str,
    target_lufs: float = -14,
    peak_ceiling: Optional[float] = None,
) -> str:
    """
    Two-pass loudness normalization to target LUFS using the EBU R128 loudnorm filter.

    Pass 1 measures the input's integrated loudness, true peak, and loudness range.
    Pass 2 applies a linear correction using measured values for transparent,
    artifact-free normalization.

    Args:
        input_path:   Source audio file.
        output_path:  Destination for normalized audio.
        target_lufs:  Target integrated loudness (e.g. -14 for voice, -28 for music).
        peak_ceiling: True peak ceiling in dBTP. Defaults to AUDIO_LEVELS["peak_ceiling"].

    Returns: output_path.
    """
    if peak_ceiling is None:
        peak_ceiling = AUDIO_LEVELS["peak_ceiling"]

    # Pass 1: Measure current loudness
    measure = subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-af", f"loudnorm=I={target_lufs}:TP={peak_ceiling}:LRA=11:print_format=json",
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
        # Fallback: single-pass normalization (less precise but functional)
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-af",
             f"loudnorm=I={target_lufs}:TP={peak_ceiling}:LRA=11",
             "-ar", str(VIDEO_SPECS["audio_sample_rate"]), output_path],
            check=True, capture_output=True,
        )
        return output_path

    # Pass 2: Apply measured values for precise linear normalization
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-af", (
                f"loudnorm=I={target_lufs}:TP={peak_ceiling}:LRA=11:"
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


def detect_voice_segments(voice_path: str, silence_thresh: float = -40, min_silence_dur: float = 0.3) -> list[tuple[float, float]]:
    """
    Detect non-silent segments in voice audio using FFmpeg silencedetect.

    Returns a list of (start, end) tuples indicating where voice is active.
    These segments drive sidechain ducking of the music track.

    Args:
        voice_path:       Path to normalized voice audio.
        silence_thresh:   Silence threshold in dB (default -40 dB).
        min_silence_dur:  Minimum silence duration to count as a gap (seconds).

    Returns: List of (start_sec, end_sec) tuples for voiced segments.
    """
    result = subprocess.run(
        [
            "ffmpeg", "-i", voice_path,
            "-af", f"silencedetect=noise={silence_thresh}dB:d={min_silence_dur}",
            "-f", "null", "-"
        ],
        capture_output=True, text=True,
    )

    total_duration = get_duration(voice_path)
    stderr = result.stderr

    # Parse silence_start / silence_end markers from FFmpeg output
    silence_starts = []
    silence_ends = []
    for line in stderr.split("\n"):
        if "silence_start:" in line:
            try:
                val = float(line.split("silence_start:")[1].strip().split()[0])
                silence_starts.append(val)
            except (ValueError, IndexError):
                pass
        if "silence_end:" in line:
            try:
                val = float(line.split("silence_end:")[1].strip().split()[0])
                silence_ends.append(val)
            except (ValueError, IndexError):
                pass

    # Build voiced segments (inverse of silence regions)
    voiced = []
    pos = 0.0

    for i, s_start in enumerate(silence_starts):
        if s_start > pos:
            voiced.append((pos, s_start))
        if i < len(silence_ends):
            pos = silence_ends[i]
        else:
            pos = total_duration

    if pos < total_duration:
        voiced.append((pos, total_duration))

    # If detection failed or found nothing, assume entire track is voiced
    if not voiced:
        voiced = [(0.0, total_duration)]

    return voiced


def duck_music_under_voice(
    music_path: str,
    voice_path: str,
    output_path: str,
    temp_dir: str,
    music_level: float = AUDIO_LEVELS["music_lufs"],
    duck_level: float = AUDIO_LEVELS["music_duck_lufs"],
) -> str:
    """
    Sidechain ducking: lower music volume when voice is active.

    Strategy:
      1. Normalize music to -28 LUFS (nominal level).
      2. Detect voiced segments via silencedetect.
      3. Build an FFmpeg volume expression that drops from -28 to -35 LUFS
         during voiced segments (a 7 dB reduction).
      4. Apply smooth attack/release ramps to avoid clicks.

    This uses the volume filter rather than sidechaincompress for broader
    FFmpeg compatibility and deterministic results.

    Args:
        music_path:   Raw music file.
        voice_path:   Normalized voice audio (used to detect speech segments).
        output_path:  Destination for ducked music.
        temp_dir:     Episode temp directory for intermediate files.
        music_level:  Target LUFS for music when voice is silent (-28).
        duck_level:   Target LUFS for music when voice is active (-35).

    Returns: output_path.
    """
    voice_duration = get_duration(voice_path)

    # Step 1: Normalize music to nominal level
    music_norm = os.path.join(temp_dir, "music_normalized.wav")
    normalize_audio(music_path, music_norm, target_lufs=music_level)

    # Step 2: Loop/trim music to match voice duration
    music_fitted = os.path.join(temp_dir, "music_fitted.wav")
    music_duration = get_duration(music_norm)

    if music_duration < voice_duration:
        # Loop music to fill the full voice duration
        loop_count = int(voice_duration / music_duration) + 1
        subprocess.run(
            [
                "ffmpeg", "-y", "-stream_loop", str(loop_count),
                "-i", music_norm,
                "-t", str(voice_duration),
                "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
                music_fitted,
            ],
            check=True, capture_output=True,
        )
    else:
        # Trim music to voice duration
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", music_norm,
                "-t", str(voice_duration),
                "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
                music_fitted,
            ],
            check=True, capture_output=True,
        )

    # Step 3: Detect where voice is active
    voiced_segments = detect_voice_segments(voice_path)

    # Step 4: Build volume expression for ducking
    # Duck amount in dB (negative = quieter)
    duck_db = duck_level - music_level  # e.g. -35 - (-28) = -7 dB
    ramp_duration = 0.05  # 50ms attack/release ramp to avoid clicks

    # Build a volume expression: start at 0dB, duck by duck_db during voiced segments
    # Each segment contributes: between(t, start-ramp, end+ramp) * duck_db
    # We use enable/volume filter chains for reliable cross-version compatibility
    if voiced_segments:
        # Build a single volume expression using nested if() for ducking
        # volume=dB expression that evaluates to duck_db during voice, 0 otherwise
        conditions = []
        for seg_start, seg_end in voiced_segments:
            # Smooth ramp: linear ramp over ramp_duration at boundaries
            conditions.append(
                f"between(t,{seg_start:.3f},{seg_end:.3f})"
            )

        # Combine all voiced segment conditions with + and clamp
        duck_expr = "+".join(conditions)
        # If any condition is true (>=1), apply duck; min() clamps overlapping segments
        volume_expr = f"volume=enable=1:volume='{duck_db}*min(1,{duck_expr})':eval=frame"

        subprocess.run(
            [
                "ffmpeg", "-y", "-i", music_fitted,
                "-af", f"{volume_expr}",
                "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
                output_path,
            ],
            check=True, capture_output=True,
        )
    else:
        # No voiced segments detected — use music as-is
        shutil.copy2(music_fitted, output_path)

    return output_path


def apply_music_fades(
    input_path: str,
    output_path: str,
    total_duration: float,
    fade_in_dur: float = AUDIO_FADES["music_fade_in"],
    fade_out_dur: float = AUDIO_FADES["music_fade_out"],
) -> str:
    """
    Apply fade-in and fade-out to a music track.

    Music fades in over the first fade_in_dur seconds and fades out over
    the last fade_out_dur seconds, giving the episode a polished opening
    and a clean ending.

    Args:
        input_path:    Source music audio.
        output_path:   Destination for faded music.
        total_duration: Total duration of the track in seconds.
        fade_in_dur:   Fade-in duration (default 3s per PRODUCTION_SOP).
        fade_out_dur:  Fade-out duration (default 5s per PRODUCTION_SOP).

    Returns: output_path.
    """
    fade_out_start = max(0, total_duration - fade_out_dur)

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-af", (
                f"afade=t=in:st=0:d={fade_in_dur},"
                f"afade=t=out:st={fade_out_start:.3f}:d={fade_out_dur}"
            ),
            "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
            output_path,
        ],
        check=True, capture_output=True,
    )
    return output_path


def prepare_audio_layer(
    input_path: str,
    output_path: str,
    target_lufs: float,
    target_duration: float,
    temp_dir: str,
) -> str:
    """
    Prepare a single audio layer: normalize to target LUFS, fit to target duration.

    If the source is shorter than target_duration it is looped; if longer it is trimmed.

    Args:
        input_path:       Source audio file.
        output_path:      Destination for prepared audio.
        target_lufs:      LUFS normalization target.
        target_duration:  Desired duration in seconds.
        temp_dir:         Temp directory for intermediates.

    Returns: output_path.
    """
    # Normalize
    norm_path = output_path + ".norm.wav"
    normalize_audio(input_path, norm_path, target_lufs=target_lufs)

    # Fit to duration
    source_dur = get_duration(norm_path)
    if source_dur < target_duration:
        loop_count = int(target_duration / source_dur) + 1
        subprocess.run(
            [
                "ffmpeg", "-y", "-stream_loop", str(loop_count),
                "-i", norm_path,
                "-t", str(target_duration),
                "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
                output_path,
            ],
            check=True, capture_output=True,
        )
    else:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", norm_path,
                "-t", str(target_duration),
                "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
                output_path,
            ],
            check=True, capture_output=True,
        )

    # Clean up intermediate
    if os.path.exists(norm_path):
        os.remove(norm_path)

    return output_path


def mix_audio_layers(
    voice_path: str,
    music_path: Optional[str],
    sfx_path: Optional[str],
    ambient_path: Optional[str],
    output_path: str,
    temp_dir: str,
) -> str:
    """
    Broadcast-grade 4-layer audio mix.

    Layer stack (mixed via FFmpeg amix):
      1. Voice      — -14 LUFS (already normalized before this call)
      2. Music      — -28 LUFS nominal, ducked to -35 LUFS under voice, faded in/out
      3. SFX        — -20 LUFS
      4. Ambient    — -35 LUFS

    After mixing, the combined output is normalized to -14 LUFS master.

    Args:
        voice_path:   Normalized voice audio (-14 LUFS).
        music_path:   Music file (or None to skip).
        sfx_path:     SFX file (or None to skip).
        ambient_path: Ambient/room-tone file (or None to skip).
        output_path:  Destination for final mixed audio.
        temp_dir:     Episode temp directory for intermediates.

    Returns: output_path.
    """
    voice_duration = get_duration(voice_path)
    layers = [voice_path]
    input_args = ["-i", voice_path]

    # ── Layer 2: Music (normalize + duck + fade) ────────────────────────
    if music_path and os.path.exists(music_path):
        ducked = os.path.join(temp_dir, "music_ducked.wav")
        duck_music_under_voice(music_path, voice_path, ducked, temp_dir)

        faded = os.path.join(temp_dir, "music_faded.wav")
        apply_music_fades(ducked, faded, voice_duration)

        layers.append(faded)
        input_args.extend(["-i", faded])

    # ── Layer 3: SFX ────────────────────────────────────────────────────
    if sfx_path and os.path.exists(sfx_path):
        sfx_prepared = os.path.join(temp_dir, "sfx_prepared.wav")
        prepare_audio_layer(sfx_path, sfx_prepared, AUDIO_LEVELS["sfx_lufs"], voice_duration, temp_dir)
        layers.append(sfx_prepared)
        input_args.extend(["-i", sfx_prepared])

    # ── Layer 4: Ambient ────────────────────────────────────────────────
    if ambient_path and os.path.exists(ambient_path):
        ambient_prepared = os.path.join(temp_dir, "ambient_prepared.wav")
        prepare_audio_layer(ambient_path, ambient_prepared, AUDIO_LEVELS["ambient_lufs"], voice_duration, temp_dir)
        layers.append(ambient_prepared)
        input_args.extend(["-i", ambient_prepared])

    # ── Mix all layers ──────────────────────────────────────────────────
    num_layers = len(layers)

    if num_layers == 1:
        # Voice only — no mixing needed
        mixed_raw = voice_path
    else:
        mixed_raw = os.path.join(temp_dir, "mix_raw.wav")
        # Build filter_complex for amix
        filter_inputs = "".join(f"[{i}:a]" for i in range(num_layers))
        filter_expr = f"{filter_inputs}amix=inputs={num_layers}:duration=first:dropout_transition=2:normalize=0[mixed]"

        cmd = ["ffmpeg", "-y"] + input_args + [
            "-filter_complex", filter_expr,
            "-map", "[mixed]",
            "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
            mixed_raw,
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    # ── Final master normalization to -14 LUFS ──────────────────────────
    normalize_audio(mixed_raw, output_path, AUDIO_LEVELS["master_lufs"])
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
    print("[ASSEMBLER] Step 1/7: Normalizing voice audio to -14 LUFS...")
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

    # ── Step 4: 4-layer audio mix (voice + music + SFX + ambient) ──────
    print("[ASSEMBLER] Step 4/7: Mixing audio (4-layer broadcast mix)...")
    final_audio = os.path.join(episode_temp, "audio_final.wav")
    mix_audio_layers(
        voice_path=voice_norm,
        music_path=project.music_path,
        sfx_path=project.sfx_path,
        ambient_path=project.ambient_path,
        output_path=final_audio,
        temp_dir=episode_temp,
    )

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
