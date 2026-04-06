#!/usr/bin/env python3
"""
EP001 Video Assembly Runner

Reads assembly-config.json, checks that all required assets are present,
and assembles the final video using the video_assembler service.

Usage:
    python assemble.py              # Check assets and assemble if ready
    python assemble.py --check      # Only check which assets are present/missing
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# Resolve paths relative to this script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "assembly-config.json")

# Add the video assembler service to the Python path
sys.path.insert(0, os.path.join(PROJECT_ROOT, "vreal-ai", "backend"))


def load_config() -> dict:
    """Load and return the assembly configuration."""
    if not os.path.exists(CONFIG_PATH):
        print(f"[ERROR] Config not found: {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        return json.load(f)


def check_assets(config: dict) -> tuple[list[str], list[str]]:
    """
    Check which required asset files exist.
    Returns (present, missing) lists of file paths.
    """
    present = []
    missing = []

    # Voiceover
    voice_path = os.path.join(SCRIPT_DIR, config["voice_audio"])
    if os.path.exists(voice_path):
        present.append(voice_path)
    else:
        missing.append(voice_path)

    # Music
    music_path = os.path.join(SCRIPT_DIR, config["music"])
    if os.path.exists(music_path):
        present.append(music_path)
    else:
        missing.append(music_path)

    # Scene video files
    for scene in config["scene_descriptions"]:
        scene_path = os.path.join(SCRIPT_DIR, scene["video_file"])
        if os.path.exists(scene_path):
            present.append(scene_path)
        else:
            missing.append(scene_path)

    return present, missing


def print_asset_report(present: list[str], missing: list[str]):
    """Print a clear status report of asset availability."""
    total = len(present) + len(missing)

    print("=" * 60)
    print(f"  EP001 Asset Check: {len(present)}/{total} files found")
    print("=" * 60)

    if present:
        print(f"\n  PRESENT ({len(present)}):")
        for p in present:
            rel = os.path.relpath(p, SCRIPT_DIR)
            print(f"    [OK]  {rel}")

    if missing:
        print(f"\n  MISSING ({len(missing)}):")
        for m in missing:
            rel = os.path.relpath(m, SCRIPT_DIR)
            print(f"    [--]  {rel}")

    print()
    if not missing:
        print("  All assets present. Ready to assemble.")
    else:
        print(f"  {len(missing)} file(s) still needed before assembly.")
    print("=" * 60)


def assemble(config: dict):
    """Run the video assembler to produce the final video."""
    from app.services.video_assembler import (
        AssemblyProject,
        SceneClip,
        TextOverlay,
        assemble_video,
        cleanup_temp,
    )

    voice_path = os.path.join(SCRIPT_DIR, config["voice_audio"])
    music_path = os.path.join(SCRIPT_DIR, config["music"])

    # Build the AssemblyProject
    project = AssemblyProject(
        episode_id=config["episode_id"],
        title=config["title"],
        voice_audio_path=voice_path,
        music_path=music_path,
        output_filename=config.get("output_filename"),
    )

    for scene in config["scene_descriptions"]:
        video_path = os.path.join(SCRIPT_DIR, scene["video_file"])

        project.scenes.append(SceneClip(
            scene_number=scene["scene"],
            video_path=video_path,
            start_time=scene["start_time"],
            end_time=scene["end_time"],
            motion=scene.get("motion", "zoom_in"),
            transition_in=scene.get("transition_in", "fade"),
            transition_out=scene.get("transition_out", "fade"),
            description=scene.get("description", ""),
        ))

        if scene.get("text_overlay"):
            overlay_start = scene["start_time"]
            overlay_end = min(overlay_start + 5.0, scene["end_time"])
            project.text_overlays.append(TextOverlay(
                text=scene["text_overlay"],
                start_time=overlay_start,
                end_time=overlay_end,
                position=scene.get("text_position", "center"),
                style="kinetic",
                font_size=scene.get("font_size", 56),
            ))

    print(f"\n[ASSEMBLE] Starting assembly for {config['episode_id']}: {config['title']}")
    print(f"[ASSEMBLE] Voice: {voice_path}")
    print(f"[ASSEMBLE] Music: {music_path}")
    print(f"[ASSEMBLE] Scenes: {len(project.scenes)}")
    print(f"[ASSEMBLE] Text overlays: {len(project.text_overlays)}")
    print()

    try:
        output_path = assemble_video(project)
        print(f"\n[ASSEMBLE] Final video: {output_path}")
        print("[ASSEMBLE] Assembly complete.")
    except Exception as e:
        print(f"\n[ERROR] Assembly failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cleanup_temp(config["episode_id"])
        print("[ASSEMBLE] Temp files cleaned up.")


def main():
    parser = argparse.ArgumentParser(description="EP001 Video Assembly Runner")
    parser.add_argument(
        "--check", action="store_true",
        help="Only check asset availability, do not assemble",
    )
    args = parser.parse_args()

    config = load_config()
    present, missing = check_assets(config)
    print_asset_report(present, missing)

    if args.check:
        sys.exit(0 if not missing else 1)

    if missing:
        print("[ASSEMBLE] Cannot assemble: missing assets. Use --check for details.")
        sys.exit(1)

    assemble(config)


if __name__ == "__main__":
    main()
