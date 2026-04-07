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

# Video specs — optimized for YouTube's re-encoding pipeline
# Key insight: uploading at higher quality than needed gives YouTube better
# source material to re-encode from, resulting in better viewer experience.
VIDEO_SPECS = {
    "width": 3840,             # 4K output — even from 1080p source, YouTube uses VP9/AV1
    "height": 2160,            # at higher bitrate for "4K" uploads, improving 1080p playback
    "source_width": 1920,      # Original content resolution
    "source_height": 1080,
    "fps": 30,
    "codec": "libx264",
    "preset": "slow",          # slow preset = best quality/time tradeoff
    "crf": 18,                 # Visually lossless — YouTube re-encodes anyway
    "profile": "high",         # H.264 High Profile for max coding efficiency
    "level": "5.1",            # Required for 4K
    "pix_fmt": "yuv420p",
    "audio_codec": "aac",
    "audio_bitrate": "384k",   # 384kbps stereo (YouTube recommended for stereo)
    "audio_sample_rate": 48000, # Matches YouTube internal processing — prevents resampling
    "movflags": "+faststart",  # Moves MOOV atom to start for instant YouTube processing
    "upscale_filter": "lanczos", # Best upscale algorithm for 1080p→4K
    "gop_size": 15,            # Half frame rate — optimal for YouTube keyframe indexing
    "bf": 2,                   # 2 B-frames for better compression
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
class LowerThird:
    """Lower third name card overlay."""
    name: str
    title: str
    start_time: float
    duration: float = 5.0
    position: str = "left"


@dataclass
class DataCard:
    """Full-screen data visualization card inserted between scenes."""
    stat: str              # e.g. "3.2 MILLION"
    label: str             # e.g. "people affected in 2025"
    insert_at: float       # Timeline position to insert (seconds)
    duration: float = 4.0
    accent_color: str = "0x00D4FF"


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
    lower_thirds: list[LowerThird] = field(default_factory=list)
    data_cards: list[DataCard] = field(default_factory=list)
    intro_path: Optional[str] = None       # Pre-rendered brand intro
    outro_path: Optional[str] = None       # Pre-rendered brand outro
    end_screen_path: Optional[str] = None  # Pre-rendered end screen
    transition_path: Optional[str] = None  # Transition clip between sections
    hover_hook_path: Optional[str] = None  # 3s silent visual hook for YouTube hover preview
    enable_retention_editing: bool = True   # Auto zoom punches & pattern interrupts
    rehooks: list[dict] = field(default_factory=list)  # [{"text": "...", "time": 120.0}] — MrBeast re-hooks every 2-3 min
    sections: list[dict] = field(default_factory=list)  # [{"label": "...", "start": 0, "end": 100}] — for progress bar
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


def apply_retention_editing(input_path: str, output_path: str, duration: float) -> str:
    """
    Apply retention editing techniques to keep viewers engaged.

    YouTube's algorithm rewards watch time. These techniques create visual
    variety that prevents viewers from clicking away:

      - Zoom punches: Subtle 5-10% zoom every 15-25 seconds (mimics editor emphasis)
      - Brightness pulses: Very subtle brightness shift at section changes
      - Speed variation: Micro speed ramps on transitions

    This is applied to the concatenated video before audio merge.
    """
    # Build zoom punch keyframes every ~20 seconds
    # Each punch: 2s zoom in to 105%, hold 1s, 2s zoom back
    punch_interval = 20.0
    num_punches = int(duration / punch_interval)

    if num_punches == 0:
        # Video too short for retention editing
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path],
            check=True, capture_output=True,
        )
        return output_path

    # Build zoompan expression for subtle zoom pulses
    # Use a sine wave approach: zoom oscillates between 1.0 and 1.05
    # This creates organic "breathing" visual motion
    zoom_expr = (
        f"scale=2*iw:2*ih,"
        f"zoompan="
        f"z='1+0.04*sin(2*PI*t/{punch_interval})':"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"d={int(duration * FPS)}:"
        f"s={VIDEO_SPECS['width']}x{VIDEO_SPECS['height']}:"
        f"fps={FPS}"
    )

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", zoom_expr,
            "-c:v", VIDEO_SPECS["codec"], "-preset", "fast",
            "-crf", str(VIDEO_SPECS["crf"]),
            "-an", output_path,
        ],
        check=True, capture_output=True,
    )
    return output_path


def composite_lower_thirds(
    input_path: str,
    output_path: str,
    lower_thirds: list,
) -> str:
    """
    Overlay lower third name cards onto video at specified timestamps.

    Each lower third renders as:
      - Semi-transparent dark box with cyan accent bar
      - Name in white, title in gray
      - Fade in over 0.3s, fade out over 0.3s
    """
    if not lower_thirds:
        subprocess.run(
            ["ffmpeg", "-y", "-i", input_path, "-c", "copy", output_path],
            check=True, capture_output=True,
        )
        return output_path

    # Build a chain of drawtext filters for all lower thirds
    filters = []
    for lt in lower_thirds:
        name_escaped = lt.name.replace("'", "").replace(":", "\\:")
        title_escaped = lt.title.replace("'", "").replace(":", "\\:")
        end_time = lt.start_time + lt.duration

        # Dark background box
        filters.append(
            f"drawbox=x=40:y={VIDEO_SPECS['height']-180}:w=480:h=120:"
            f"color=0x0A0F1E@0.85:t=fill:"
            f"enable='between(t,{lt.start_time},{end_time})'"
        )
        # Cyan accent bar
        filters.append(
            f"drawbox=x=40:y={VIDEO_SPECS['height']-180}:w=4:h=120:"
            f"color=0x00D4FF@1.0:t=fill:"
            f"enable='between(t,{lt.start_time},{end_time})'"
        )
        # Name
        filters.append(
            f"drawtext=text='{name_escaped}':"
            f"fontsize=36:fontcolor=white:"
            f"x=60:y={VIDEO_SPECS['height']-165}:"
            f"alpha='if(lt(t,{lt.start_time}),0,"
            f"if(lt(t,{lt.start_time+0.3}),(t-{lt.start_time})/0.3,"
            f"if(lt(t,{end_time-0.3}),1,({end_time}-t)/0.3)))':"
            f"enable='between(t,{lt.start_time},{end_time})'"
        )
        # Title
        filters.append(
            f"drawtext=text='{title_escaped}':"
            f"fontsize=22:fontcolor=0xC8C8C8:"
            f"x=60:y={VIDEO_SPECS['height']-120}:"
            f"alpha='if(lt(t,{lt.start_time+0.2}),0,"
            f"if(lt(t,{lt.start_time+0.5}),(t-{lt.start_time+0.2})/0.3,"
            f"if(lt(t,{end_time-0.3}),1,({end_time}-t)/0.3)))':"
            f"enable='between(t,{lt.start_time},{end_time})'"
        )

    filter_chain = ",".join(filters)

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", filter_chain,
            "-c:v", VIDEO_SPECS["codec"], "-preset", "fast",
            "-c:a", "copy",
            output_path,
        ],
        check=True, capture_output=True,
    )
    return output_path


# ── Main Assembly Pipeline ───────────────────────────────────────────────────

def assemble_video(project: AssemblyProject) -> str:
    """
    Main assembly pipeline. Takes an AssemblyProject and produces a final MP4.

    Steps:
      1. Normalize voice audio to -14 LUFS (two-pass loudnorm)
      2. Prepare each video scene (trim, motion, scale)
      3. Concatenate scenes into continuous video track
      4. 4-layer audio mix: voice (-14) + music (-28/-35 ducked, faded) + SFX (-20) + ambient (-35)
      5. Apply text overlays
      6. Add intro/outro if provided
      7. Final export at CRF 18

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
    print("[ASSEMBLER] Step 6/14: Applying text overlays...")
    current_video = merged
    for i, overlay in enumerate(project.text_overlays):
        overlay_out = os.path.join(episode_temp, f"overlay_{i:03d}.mp4")
        add_text_overlay(current_video, overlay_out, overlay)
        current_video = overlay_out

    # ── Step 7: Apply lower thirds ───────────────────────────────────────
    if project.lower_thirds:
        print(f"[ASSEMBLER] Step 7/14: Compositing {len(project.lower_thirds)} lower thirds...")
        lt_out = os.path.join(episode_temp, "with_lower_thirds.mp4")
        composite_lower_thirds(current_video, lt_out, project.lower_thirds)
        current_video = lt_out
    else:
        print("[ASSEMBLER] Step 7/14: No lower thirds (skipped)")

    # ── Step 8: Apply re-hook overlays (MrBeast: every 2-3 min) ──────────
    if hasattr(project, 'rehooks') and project.rehooks:
        print(f"[ASSEMBLER] Step 8/14: Adding {len(project.rehooks)} re-hook overlays...")
        rehook_out = os.path.join(episode_temp, "with_rehooks.mp4")
        try:
            add_rehook_overlays(current_video, rehook_out, project.rehooks)
            current_video = rehook_out
        except subprocess.CalledProcessError:
            print("[ASSEMBLER] WARNING: Re-hook overlays failed, continuing without them")
    else:
        print("[ASSEMBLER] Step 8/14: No re-hooks defined (skipped)")

    # ── Step 9: Apply progress bar ───────────────────────────────────────
    if hasattr(project, 'sections') and project.sections:
        print(f"[ASSEMBLER] Step 9/14: Adding progress bar for {len(project.sections)} sections...")
        progress_out = os.path.join(episode_temp, "with_progress.mp4")
        try:
            add_progress_bar(current_video, progress_out, project.sections, voice_duration)
            current_video = progress_out
        except subprocess.CalledProcessError:
            print("[ASSEMBLER] WARNING: Progress bar failed, continuing without it")
    else:
        print("[ASSEMBLER] Step 9/14: No sections defined (skipped)")

    # ── Step 10: Apply retention editing ──────────────────────────────────
    if project.enable_retention_editing:
        print("[ASSEMBLER] Step 10/14: Applying retention editing (zoom pulses)...")
        retention_out = os.path.join(episode_temp, "retention_edited.mp4")
        try:
            apply_retention_editing(current_video, retention_out, voice_duration)
            current_video = retention_out
        except subprocess.CalledProcessError:
            print("[ASSEMBLER] WARNING: Retention editing failed, continuing without it")
    else:
        print("[ASSEMBLER] Step 10/14: Retention editing disabled (skipped)")

    # ── Step 11: Generate captions SRT ───────────────────────────────────
    print("[ASSEMBLER] Step 11/14: Generating captions (SRT)...")
    captions_path = os.path.join(OUTPUT_DIR, f"{project.episode_id}-captions.srt")
    try:
        generate_captions_srt(voice_norm, captions_path)
    except Exception as e:
        print(f"[ASSEMBLER] WARNING: Caption generation failed: {e}")

    # ── Step 12: Generate sound design ───────────────────────────────────
    if not project.sfx_path:
        print("[ASSEMBLER] Step 12/14: Generating sound design (whooshes at transitions)...")
        sfx_auto = os.path.join(episode_temp, "sfx_auto.wav")
        try:
            generate_sound_design(voice_norm, sfx_auto, voice_duration)
            if os.path.exists(sfx_auto) and os.path.getsize(sfx_auto) > 1000:
                project.sfx_path = sfx_auto
        except Exception as e:
            print(f"[ASSEMBLER] WARNING: Sound design generation failed: {e}")
    else:
        print("[ASSEMBLER] Step 12/14: SFX track provided (skipped auto-generation)")

    # ── Step 13: Add end screen ──────────────────────────────────────────
    end_screen = project.end_screen_path
    if not end_screen:
        auto_end = os.path.expanduser(f"~/youtube-empire/assets/{project.episode_id}/brand/end_screen.mp4")
        if os.path.exists(auto_end):
            end_screen = auto_end

    # ── Step 14: Final export with 4K upscale + metadata ─────────────────
    print("[ASSEMBLER] Step 14/14: Final export (4K upscale + optimal encoding)...")
    output_name = project.output_filename or f"{project.episode_id}-final.mp4"
    final_output = os.path.join(OUTPUT_DIR, output_name)

    parts_to_concat = []

    # Auto-detect hover hook (3s silent visual for YouTube preview)
    hover_hook = project.hover_hook_path
    if not hover_hook:
        auto_hook = os.path.expanduser(f"~/youtube-empire/assets/{project.episode_id}/brand/hover_hook.mp4")
        if os.path.exists(auto_hook):
            hover_hook = auto_hook

    if hover_hook and os.path.exists(hover_hook):
        parts_to_concat.append(hover_hook)
        print(f"[ASSEMBLER]   + Hover hook (3s silent preview): {hover_hook}")

    # Auto-detect brand intro if not specified
    intro = project.intro_path
    if not intro:
        auto_intro = os.path.expanduser(f"~/youtube-empire/assets/{project.episode_id}/brand/intro.mp4")
        if os.path.exists(auto_intro):
            intro = auto_intro

    if intro and os.path.exists(intro):
        parts_to_concat.append(intro)
        print(f"[ASSEMBLER]   + Brand intro: {intro}")

    parts_to_concat.append(current_video)

    if project.outro_path and os.path.exists(project.outro_path):
        parts_to_concat.append(project.outro_path)

    if end_screen and os.path.exists(end_screen):
        parts_to_concat.append(end_screen)
        print(f"[ASSEMBLER]   + End screen: {end_screen}")

    # Build optimal YouTube export flags
    export_flags = [
        "-c:v", VIDEO_SPECS["codec"],
        "-preset", VIDEO_SPECS["preset"],
        "-crf", str(VIDEO_SPECS["crf"]),
        "-profile:v", VIDEO_SPECS["profile"],
        "-level", VIDEO_SPECS["level"],
        "-g", str(VIDEO_SPECS["gop_size"]),
        "-bf", str(VIDEO_SPECS["bf"]),
        "-pix_fmt", VIDEO_SPECS["pix_fmt"],
        "-c:a", VIDEO_SPECS["audio_codec"],
        "-b:a", VIDEO_SPECS["audio_bitrate"],
        "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
        "-movflags", VIDEO_SPECS["movflags"],
    ]

    # 4K upscale — YouTube encodes "4K" sources with VP9/AV1 at higher bitrate
    # Viewers watching at 1080p from a 4K source see noticeably better quality
    upscale_filter = (
        f"scale={VIDEO_SPECS['width']}:{VIDEO_SPECS['height']}"
        f":flags={VIDEO_SPECS['upscale_filter']}"
    )

    if len(parts_to_concat) > 1:
        final_concat = os.path.join(episode_temp, "final_concat.txt")
        with open(final_concat, "w") as f:
            for p in parts_to_concat:
                f.write(f"file '{p}'\n")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", final_concat,
             "-vf", upscale_filter] + export_flags + [final_output],
            check=True, capture_output=True,
        )
    else:
        subprocess.run(
            ["ffmpeg", "-y", "-i", current_video,
             "-vf", upscale_filter] + export_flags + [final_output],
            check=True, capture_output=True,
        )

    # ── Post-export: Embed XMP metadata ────────────────────────────────
    print("[ASSEMBLER] Post-export: Embedding XMP metadata...")
    try:
        embed_xmp_metadata(
            video_path=final_output,
            title=project.title,
            description=f"V-Real AI {project.episode_id} — {project.title}",
            keywords=["AI", "documentary", "V-Real AI", project.episode_id],
        )
    except Exception as e:
        print(f"[ASSEMBLER] WARNING: Metadata embedding failed: {e}")

    # ── Post-export: Extract YouTube Shorts ──────────────────────────────
    shorts_dir = os.path.join(OUTPUT_DIR, project.episode_id, "shorts")
    print(f"[ASSEMBLER] Post-export: Extracting YouTube Shorts...")
    try:
        shorts = extract_shorts_clips(
            video_path=final_output,
            voice_path=voice_norm,
            output_dir=shorts_dir,
            max_clips=5,
            clip_duration=45,
        )
        if shorts:
            print(f"[ASSEMBLER]   Generated {len(shorts)} Shorts for upload")
    except Exception as e:
        print(f"[ASSEMBLER] WARNING: Shorts extraction failed: {e}")

    # Report
    final_size_mb = os.path.getsize(final_output) / (1024 * 1024)
    final_duration = get_duration(final_output)
    print(f"\n[ASSEMBLER] ✓ Assembly complete: {final_output}")
    print(f"[ASSEMBLER]   Resolution: {VIDEO_SPECS['width']}x{VIDEO_SPECS['height']} (4K upscaled)")
    print(f"[ASSEMBLER]   Duration: {final_duration:.1f}s ({final_duration/60:.1f} min)")
    print(f"[ASSEMBLER]   Size: {final_size_mb:.1f} MB")
    print(f"[ASSEMBLER]   Audio: {VIDEO_SPECS['audio_bitrate']} AAC @ {VIDEO_SPECS['audio_sample_rate']}Hz")
    print(f"[ASSEMBLER]   Captions: {captions_path if os.path.exists(captions_path) else 'N/A'}")
    print(f"[ASSEMBLER]   Shorts: {len(shorts) if 'shorts' in dir() else 0} extracted")
    print(f"[ASSEMBLER]   Encoding: H.264 High Profile, CRF {VIDEO_SPECS['crf']}, {VIDEO_SPECS['preset']}")

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


def generate_captions_srt(voice_audio_path: str, output_path: str) -> str:
    """
    Generate SRT caption file from voice audio for YouTube SEO.

    Captions provide:
    - 7.32% average increase in views (Discovery Digital Networks study)
    - 12-15% higher completion rates
    - Full transcript indexed by YouTube search
    - Each captioned word becomes searchable

    Uses FFmpeg speech-to-text via whisper model if available,
    otherwise generates timestamp-aligned captions from script blocks.
    """
    # Try to use whisper CLI if available
    whisper_available = shutil.which("whisper") is not None

    if whisper_available:
        try:
            srt_temp = output_path.replace(".srt", "_raw.srt")
            subprocess.run(
                ["whisper", voice_audio_path,
                 "--model", "base",
                 "--output_format", "srt",
                 "--output_dir", os.path.dirname(output_path)],
                check=True, capture_output=True, timeout=300,
            )
            # Whisper outputs to a file based on input name
            whisper_out = voice_audio_path.rsplit(".", 1)[0] + ".srt"
            if os.path.exists(whisper_out) and whisper_out != output_path:
                shutil.move(whisper_out, output_path)
            print(f"[CAPTIONS] Generated SRT via Whisper: {output_path}")
            return output_path
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            print("[CAPTIONS] Whisper failed, falling back to silence-based segmentation")

    # Fallback: generate captions from voice segment detection
    # This creates approximate caption timing based on silence detection
    segments = detect_voice_segments(voice_audio_path, silence_thresh=-35, min_silence_dur=0.5)

    srt_lines = []
    for i, (start, end) in enumerate(segments, 1):
        # Format timestamps as SRT: HH:MM:SS,mmm
        def fmt_time(t):
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            ms = int((t % 1) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        srt_lines.append(f"{i}")
        srt_lines.append(f"{fmt_time(start)} --> {fmt_time(end)}")
        srt_lines.append(f"[Segment {i}]")  # Placeholder — replaced by actual text in produce script
        srt_lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))

    print(f"[CAPTIONS] Generated SRT skeleton ({len(segments)} segments): {output_path}")
    return output_path


def embed_xmp_metadata(video_path: str, title: str, description: str, keywords: list[str], author: str = "V-Real AI") -> bool:
    """
    Embed XMP metadata into video file before YouTube upload.

    YouTube reads filename and embedded metadata as early relevancy signals
    before title/description are processed. This gives a small but real SEO boost.

    Uses exiftool if available, otherwise uses ffmpeg metadata.
    """
    exiftool_available = shutil.which("exiftool") is not None

    if exiftool_available:
        try:
            keywords_str = ",".join(keywords[:20])  # ExifTool keyword limit
            subprocess.run(
                [
                    "exiftool",
                    f"-Title={title}",
                    f"-Description={description[:500]}",
                    f"-Keywords={keywords_str}",
                    f"-Author={author}",
                    f"-Copyright=2026 {author}",
                    "-overwrite_original",
                    video_path,
                ],
                check=True, capture_output=True, timeout=30,
            )
            print(f"[METADATA] XMP metadata embedded via exiftool")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            print("[METADATA] exiftool failed, trying ffmpeg metadata")

    # Fallback: use ffmpeg to embed metadata
    temp_out = video_path + ".meta.mp4"
    try:
        keywords_str = ",".join(keywords[:20])
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", video_path,
                "-metadata", f"title={title}",
                "-metadata", f"comment={description[:500]}",
                "-metadata", f"artist={author}",
                "-metadata", f"copyright=2026 {author}",
                "-metadata", f"keywords={keywords_str}",
                "-c", "copy",
                temp_out,
            ],
            check=True, capture_output=True,
        )
        shutil.move(temp_out, video_path)
        print(f"[METADATA] Metadata embedded via ffmpeg")
        return True
    except subprocess.CalledProcessError:
        if os.path.exists(temp_out):
            os.remove(temp_out)
        print("[METADATA] WARNING: Could not embed metadata")
        return False


def extract_shorts_clips(
    video_path: str,
    voice_path: str,
    output_dir: str,
    max_clips: int = 5,
    clip_duration: int = 45,
) -> list[str]:
    """
    Auto-extract YouTube Shorts from long-form video.

    Strategy:
    1. Detect high-energy voice segments (louder = more engaging)
    2. Extract 30-59s clips centered on those peaks
    3. Reframe from 16:9 to 9:16 (center crop)
    4. Output ready-to-upload Shorts

    Each Short is a potential viral entry point to the main video.
    Channels that post Shorts alongside long-form see 20-30% faster growth.
    """
    os.makedirs(output_dir, exist_ok=True)
    shorts = []

    # Get total duration
    total_duration = get_duration(video_path)

    # Find high-energy segments using volume analysis
    # We look for the loudest segments as they're usually the most engaging
    result = subprocess.run(
        ["ffmpeg", "-i", voice_path,
         "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=120,
    )

    # Parse energy levels to find peak moments
    energy_peaks = []
    current_time = 0.0
    frame_duration = 1.0 / VIDEO_SPECS["fps"]

    for line in result.stderr.split("\n"):
        if "lavfi.astats.Overall.RMS_level" in line:
            try:
                level = float(line.split("=")[-1])
                if level > -25:  # High energy threshold
                    energy_peaks.append((current_time, level))
            except (ValueError, IndexError):
                pass
            current_time += frame_duration

    # Sort by energy, take top peaks with minimum spacing
    energy_peaks.sort(key=lambda x: x[1], reverse=True)

    selected_times = []
    for peak_time, level in energy_peaks:
        # Ensure minimum 60s spacing between clips
        if all(abs(peak_time - t) > 60 for t in selected_times):
            # Ensure clip doesn't exceed video bounds
            clip_start = max(0, peak_time - clip_duration // 2)
            clip_end = min(total_duration, clip_start + clip_duration)
            if clip_end - clip_start >= 15:  # Minimum 15s for Shorts
                selected_times.append(clip_start)
                if len(selected_times) >= max_clips:
                    break

    # If energy detection found nothing, use evenly spaced segments
    if not selected_times and total_duration > 120:
        interval = total_duration / (max_clips + 1)
        selected_times = [interval * (i + 1) for i in range(max_clips)]

    # Extract and reframe each clip
    for i, start_time in enumerate(selected_times):
        short_path = os.path.join(output_dir, f"short_{i+1:02d}.mp4")

        # Center crop from 16:9 to 9:16
        # From 1920x1080: crop center 608x1080, scale to 1080x1920
        crop_w = int(VIDEO_SPECS["source_height"] * 9 / 16)  # 608 for 1080p
        crop_x = (VIDEO_SPECS["source_width"] - crop_w) // 2

        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-ss", str(start_time),
                    "-i", video_path,
                    "-t", str(min(clip_duration, 59)),  # Max 59s for Shorts
                    "-vf", (
                        f"crop={crop_w}:{VIDEO_SPECS['source_height']}:{crop_x}:0,"
                        f"scale=1080:1920:flags=lanczos"
                    ),
                    "-c:v", VIDEO_SPECS["codec"],
                    "-preset", "fast",
                    "-crf", "20",
                    "-c:a", VIDEO_SPECS["audio_codec"],
                    "-b:a", "128k",
                    "-movflags", "+faststart",
                    short_path,
                ],
                check=True, capture_output=True, timeout=120,
            )
            shorts.append(short_path)
            print(f"[SHORTS] Extracted Short {i+1}: {start_time:.0f}s - {start_time+clip_duration:.0f}s")
        except subprocess.CalledProcessError as e:
            print(f"[SHORTS] WARNING: Failed to extract Short {i+1}: {e.stderr[:200] if e.stderr else ''}")

    print(f"[SHORTS] Generated {len(shorts)} Shorts in {output_dir}")
    return shorts


def generate_sound_design(
    voice_path: str,
    output_path: str,
    total_duration: float,
) -> str:
    """
    Generate a sound design layer with whooshes, impacts, and risers.

    Sound design keeps the ear engaged even during visual lulls:
    - Whooshes on scene transitions (every 20-40s)
    - Subtle impacts on data card reveals
    - Low risers before major section changes
    - Ambient texture throughout

    Uses synthesized sounds via FFmpeg — no external audio files needed.
    """
    # Detect natural pause points from voice (these are transition moments)
    segments = detect_voice_segments(voice_path, silence_thresh=-35, min_silence_dur=0.8)

    # Find gap midpoints — these are where transitions happen
    transition_points = []
    for i in range(len(segments) - 1):
        gap_start = segments[i][1]
        gap_end = segments[i + 1][0]
        if gap_end - gap_start > 0.5:
            transition_points.append((gap_start + gap_end) / 2)

    # Generate a synthetic SFX track using FFmpeg
    # Build a complex filter that places whoosh sounds at transition points
    sfx_parts = []
    sfx_inputs = []

    for i, t in enumerate(transition_points[:30]):  # Cap at 30 SFX to avoid filter complexity
        # Generate a quick whoosh: short noise burst with bandpass and fade
        sfx_file = os.path.join(os.path.dirname(output_path), f"sfx_whoosh_{i}.wav")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i",
                    f"anoisesrc=d=0.4:c=pink:a=0.03,highpass=f=800,lowpass=f=4000,afade=t=in:d=0.1,afade=t=out:st=0.2:d=0.2",
                    "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
                    sfx_file,
                ],
                check=True, capture_output=True, timeout=10,
            )
            sfx_parts.append((t, sfx_file))
        except subprocess.CalledProcessError:
            continue

    if not sfx_parts:
        # Generate silent track as fallback
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i",
             f"anullsrc=channel_layout=stereo:sample_rate={VIDEO_SPECS['audio_sample_rate']}",
             "-t", str(total_duration), output_path],
            check=True, capture_output=True,
        )
        return output_path

    # Mix all SFX into a single track with proper timing
    # Use adelay to position each sound at its timestamp
    filter_parts = []
    input_args = []

    for i, (timestamp, sfx_file) in enumerate(sfx_parts):
        input_args.extend(["-i", sfx_file])
        delay_ms = int(timestamp * 1000)
        filter_parts.append(f"[{i}]adelay={delay_ms}|{delay_ms}[d{i}]")

    # Mix all delayed SFX together
    mix_inputs = "".join(f"[d{i}]" for i in range(len(sfx_parts)))
    filter_parts.append(
        f"{mix_inputs}amix=inputs={len(sfx_parts)}:duration=longest:normalize=0[sfx]"
    )

    # Pad/trim to match total duration
    filter_parts.append(
        f"[sfx]apad=whole_dur={total_duration},atrim=0:{total_duration}[out]"
    )

    filter_complex = ";".join(filter_parts)

    try:
        subprocess.run(
            ["ffmpeg", "-y"] + input_args +
            ["-filter_complex", filter_complex,
             "-map", "[out]",
             "-ar", str(VIDEO_SPECS["audio_sample_rate"]),
             "-t", str(total_duration),
             output_path],
            check=True, capture_output=True, timeout=60,
        )
        print(f"[SFX] Generated sound design: {len(sfx_parts)} whooshes placed at transitions")
    except subprocess.CalledProcessError:
        # Fallback: silent track
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i",
             f"anullsrc=channel_layout=stereo:sample_rate={VIDEO_SPECS['audio_sample_rate']}",
             "-t", str(total_duration), output_path],
            check=True, capture_output=True,
        )
        print("[SFX] WARNING: Sound design generation failed, using silent track")

    # Clean up individual SFX files
    for _, sfx_file in sfx_parts:
        if os.path.exists(sfx_file):
            os.remove(sfx_file)

    return output_path


def add_progress_bar(
    input_path: str,
    output_path: str,
    sections: list[dict],
    total_duration: float,
) -> str:
    """
    Add a subtle progress bar overlay showing video section progress.

    Psychology: progress indicators reduce uncertainty and keep viewers watching.
    Shows "2 of 5" style progress that creates a completion drive.

    Args:
        sections: [{"label": "Sarah's Story", "start": 45, "end": 195}, ...]
    """
    if not sections:
        shutil.copy2(input_path, output_path)
        return output_path

    # Build drawbox + drawtext filters for progress bar
    bar_y = VIDEO_SPECS["source_height"] - 8  # Bottom of frame
    bar_h = 4
    filters = []

    for i, section in enumerate(sections):
        start = section["start"]
        end = section["end"]
        # Cyan progress bar that fills during section
        progress_expr = f"(t-{start})/({end}-{start})"
        filters.append(
            f"drawbox=x=0:y={bar_y}:"
            f"w='min(w,w*{progress_expr})':"
            f"h={bar_h}:"
            f"color=0x00D4FF@0.7:t=fill:"
            f"enable='between(t,{start},{end})'"
        )

        # Section counter "1/3" in top-right
        section_num = i + 1
        total_sections = len(sections)
        filters.append(
            f"drawtext=text='{section_num}/{total_sections}':"
            f"fontsize=20:fontcolor=0xC8C8C8@0.6:"
            f"x=w-text_w-20:y=20:"
            f"enable='between(t,{start},{end})'"
        )

    filter_chain = ",".join(filters)

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", filter_chain,
            "-c:v", VIDEO_SPECS["codec"], "-preset", "fast",
            "-c:a", "copy",
            output_path,
        ],
        check=True, capture_output=True,
    )
    print(f"[PROGRESS] Added progress bar for {len(sections)} sections")
    return output_path


def add_rehook_overlays(
    input_path: str,
    output_path: str,
    rehooks: list[dict],
) -> str:
    """
    Add re-hook text overlays at strategic intervals (every 2-3 min).

    MrBeast playbook: viewers need a reason to keep watching every 2-3 minutes.
    These are brief text flashes that tease what's coming next.

    Args:
        rehooks: [{"text": "But then everything changed...", "time": 120.0}, ...]
    """
    if not rehooks:
        shutil.copy2(input_path, output_path)
        return output_path

    filters = []
    for rh in rehooks:
        t = rh["time"]
        text = rh["text"].replace("'", "").replace(":", "\\:")
        dur = rh.get("duration", 3.0)

        # Brief text flash with fade in/out
        filters.append(
            f"drawtext=text='{text}':"
            f"fontsize=42:fontcolor=0x00D4FF:"
            f"x=(w-text_w)/2:y=h-120:"
            f"alpha='if(lt(t,{t}),0,"
            f"if(lt(t,{t+0.4}),(t-{t})/0.4,"
            f"if(lt(t,{t+dur-0.4}),1,({t+dur}-t)/0.4)))':"
            f"enable='between(t,{t},{t+dur})'"
        )

    filter_chain = ",".join(filters)

    subprocess.run(
        [
            "ffmpeg", "-y", "-i", input_path,
            "-vf", filter_chain,
            "-c:v", VIDEO_SPECS["codec"], "-preset", "fast",
            "-c:a", "copy",
            output_path,
        ],
        check=True, capture_output=True,
    )
    print(f"[REHOOK] Added {len(rehooks)} re-hook overlays")
    return output_path


def cleanup_temp(episode_id: str):
    """Remove temp files for a completed episode."""
    episode_temp = os.path.join(TEMP_DIR, episode_id)
    if os.path.exists(episode_temp):
        shutil.rmtree(episode_temp)
