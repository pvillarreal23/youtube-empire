#!/usr/bin/env python3
"""
Make.com Pipeline Trigger — Standalone Script

Triggers Make.com scenarios directly from command line.
Use this to manually fire any pipeline step or let cowork run it.

Usage:
  python trigger_make.py --scenario all          # Fire all scenarios for EP001
  python trigger_make.py --scenario voiceover    # Fire voiceover generation
  python trigger_make.py --scenario upload       # Fire upload + SEO + social
  python trigger_make.py --scenario thumbnail    # Fire thumbnail generation
  python trigger_make.py --scenario social       # Fire social media distribution
  python trigger_make.py --scenario analytics    # Start analytics monitoring
  python trigger_make.py --status               # Check which webhooks are configured

Scenarios fire in order: voiceover → video → seo → thumbnail → upload → social → analytics → notify
"""
from __future__ import annotations

import os
import sys
import json
import time
import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / "vreal-ai" / "backend" / ".env")

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx")
    sys.exit(1)

# ── Webhook Configuration ────────────────────────────────────────────────────

WEBHOOKS = {
    "voiceover":  os.getenv("MAKE_WEBHOOK_VOICEOVER", ""),
    "video":      os.getenv("MAKE_WEBHOOK_VIDEO", ""),
    "upload":     os.getenv("MAKE_WEBHOOK_UPLOAD", ""),
    "thumbnail":  os.getenv("MAKE_WEBHOOK_THUMBNAIL", ""),
    "seo":        os.getenv("MAKE_WEBHOOK_SEO", ""),
    "social":     os.getenv("MAKE_WEBHOOK_SOCIAL", ""),
    "analytics":  os.getenv("MAKE_WEBHOOK_ANALYTICS", ""),
    "sheets":     os.getenv("MAKE_WEBHOOK_SHEETS", ""),
    "notify":     os.getenv("MAKE_WEBHOOK_NOTIFY", ""),
    "newsletter": os.getenv("MAKE_WEBHOOK_NEWSLETTER", ""),
    "research":   os.getenv("MAKE_WEBHOOK_RESEARCH", ""),
    "script":     os.getenv("MAKE_WEBHOOK_SCRIPT", ""),
    "custom":     os.getenv("MAKE_WEBHOOK_CUSTOM", ""),
}

# ── Episode Configuration (EP001) ───────────────────────────────────────────

EP001_PAYLOADS = {
    "voiceover": {
        "episode_id": "ep001",
        "title": "EP001 — The Shift",
        "voice_id": "CjK4w2V6sbgFJY05zTGt",
        "voice_name": "Julian",
        "model": "eleven_multilingual_v2",
        "blocks": 5,
        "action": "generate_voiceover",
        "script_url": "See SCRIPT_BLOCKS in produce_ep001.py",
    },
    "video": {
        "episode_id": "ep001",
        "title": "EP001 — The Shift",
        "action": "assemble_video",
        "pipeline_version": "14-step",
        "features": [
            "4K upscale", "hover hook", "brand intro", "lower thirds",
            "data cards", "re-hooks", "progress bar", "retention editing",
            "sound design", "end screen", "captions", "shorts extraction",
            "XMP metadata", "LUFS normalization"
        ],
    },
    "upload": {
        "episode_id": "ep001",
        "title": "Half Her Team Was Gone by 10 AM",
        "action": "upload_to_youtube",
        "privacy": "unlisted",
        "category": "Education",
        "tags": ["AI shift", "AI marketing", "AI 2026", "future of work"],
        "filename": "half-her-team-was-gone-by-10am-ai-shift-2026.mp4",
    },
    "thumbnail": {
        "episode_id": "ep001",
        "title": "Half Her Team Was Gone by 10 AM",
        "action": "generate_thumbnails",
        "variants": 3,
        "concept": "shocked face + '10 AM' in cyan (#00D4FF) + dark bg with faint TERMINATED overlay",
        "rules": "3 elements max, phone-readable at 150px, 0-3 words text",
        "resolution": "1920x1080",
        "format": "JPG under 2MB",
        "saturation_boost": "+20-30%",
    },
    "seo": {
        "episode_id": "ep001",
        "title": "Half Her Team Was Gone by 10 AM [AI Documentary 2026]",
        "action": "optimize_metadata",
        "description_words": 500,
        "chapters": 10,
        "tags_count": 21,
        "hashtags": ["AIshift", "AI2026", "AImarketing", "futureofwork"],
        "primary_keyword": "AI shift 2026",
        "secondary_keywords": ["AI replacing jobs", "AI marketing", "90 day rule AI"],
    },
    "social": {
        "episode_id": "ep001",
        "title": "Half Her Team Was Gone by 10 AM",
        "action": "distribute_social",
        "platforms": ["twitter", "linkedin", "instagram", "tiktok"],
        "shorts_count": 5,
        "hook": "Half her team was gone by 10 AM. Replaced by AI tools costing $49/month.",
        "cta": "Full documentary on YouTube — link in bio",
    },
    "analytics": {
        "episode_id": "ep001",
        "action": "start_monitoring",
        "check_intervals": ["15min", "30min", "1h", "6h", "24h", "48h"],
        "benchmarks": {
            "views_1h": 50,
            "views_24h": 300,
            "ctr_target": 0.04,
            "avg_view_duration_pct": 0.50,
        },
    },
    "sheets": {
        "episode_id": "ep001",
        "action": "update_production_tracker",
        "status": "production_complete",
        "pipeline_version": "14-step",
    },
    "notify": {
        "episode_id": "ep001",
        "action": "notify_pedro",
        "message": "EP001 production complete. Ready for review.",
        "action_needed": "Review video, approve thumbnails, set to public",
    },
    "newsletter": {
        "episode_id": "ep001",
        "action": "draft_newsletter",
        "subject": "The AI Shift Nobody Saw Coming",
        "preview": "Half her team was gone by 10 AM...",
    },
    "research": {
        "episode_id": "ep002",
        "action": "start_research",
        "topic": "The Price of Waiting — cost of delaying AI adoption",
        "deadline": "EP002 brief already drafted",
    },
    "script": {
        "episode_id": "ep002",
        "action": "start_script",
        "brief_url": "See output/ep002/EP002-BRIEF.md",
        "target_words": 1200,
        "target_duration": "8-9 minutes",
    },
    "custom": {
        "episode_id": "ep001",
        "action": "custom_trigger",
        "message": "Custom webhook fired from trigger_make.py",
    },
}


# ── Execution Order ──────────────────────────────────────────────────────────

PRODUCTION_ORDER = [
    "voiceover", "video", "seo", "thumbnail",
    "upload", "social", "analytics", "sheets", "notify",
]


def fire_webhook(scenario: str, payload: dict) -> bool:
    """Fire a single Make.com webhook."""
    url = WEBHOOKS.get(scenario, "")
    if not url:
        print(f"  [{scenario}] SKIPPED — webhook not configured")
        return False

    try:
        response = httpx.post(
            url,
            json={
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                **payload,
            },
            timeout=15,
        )
        if response.status_code == 200:
            print(f"  [{scenario}] ✓ FIRED — {response.status_code}")
            return True
        else:
            print(f"  [{scenario}] WARNING — HTTP {response.status_code}: {response.text[:200]}")
            return False
    except httpx.ConnectError:
        print(f"  [{scenario}] ERROR — Cannot reach Make.com (network blocked?)")
        return False
    except Exception as e:
        print(f"  [{scenario}] ERROR — {str(e)[:200]}")
        return False


def show_status():
    """Show which webhooks are configured."""
    print("\n" + "=" * 60)
    print("  MAKE.COM WEBHOOK STATUS")
    print("=" * 60)

    configured = 0
    for name, url in WEBHOOKS.items():
        status = "✓ CONFIGURED" if url else "✗ NOT SET"
        if url:
            configured += 1
            # Show masked URL
            masked = url[:35] + "..." if len(url) > 35 else url
            print(f"  {name:15s} {status}  {masked}")
        else:
            print(f"  {name:15s} {status}")

    print(f"\n  {configured}/{len(WEBHOOKS)} webhooks configured")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Make.com Pipeline Trigger")
    parser.add_argument("--scenario", type=str, default=None,
                        help="Which scenario to fire (or 'all' for full pipeline)")
    parser.add_argument("--status", action="store_true",
                        help="Show webhook configuration status")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be sent without firing")
    args = parser.parse_args()

    if args.status:
        show_status()
        return 0

    if not args.scenario:
        parser.print_help()
        print("\nAvailable scenarios:", ", ".join(WEBHOOKS.keys()))
        print("Use --scenario all to fire the full production pipeline")
        return 1

    scenarios = PRODUCTION_ORDER if args.scenario == "all" else [args.scenario]

    print("\n" + "=" * 60)
    print(f"  FIRING MAKE.COM SCENARIOS: {', '.join(scenarios)}")
    print("=" * 60 + "\n")

    fired = 0
    failed = 0

    for scenario in scenarios:
        payload = EP001_PAYLOADS.get(scenario, {"episode_id": "ep001", "action": scenario})

        if args.dry_run:
            print(f"  [{scenario}] DRY RUN — would send:")
            print(f"    {json.dumps(payload, indent=2)[:300]}")
            continue

        if fire_webhook(scenario, payload):
            fired += 1
        else:
            failed += 1

        # Small delay between scenarios to avoid overwhelming Make.com
        if len(scenarios) > 1:
            time.sleep(1)

    print(f"\n  Results: {fired} fired, {failed} failed/skipped")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
