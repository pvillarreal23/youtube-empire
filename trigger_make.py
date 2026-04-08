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
load_dotenv(Path(__file__).resolve().parent / ".env")

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
        "voice_settings": {
            "stability": 0.65,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": False,
        },
        "script_blocks": [
            {
                "name": "block1-hook-sarah",
                "section": "Hook + Setup + Sarah (0:00-3:15)",
                "text": "Half her team was gone by ten AM.\n\nReplaced by AI tools that cost forty-nine dollars a month.\n\nBut here's what nobody tells you — the people who moved fast saw twenty-eight percent salary increases.\n\nThe people who froze took eight months to recover.\n\nThe difference was a single decision made in the first ninety days.\n\nAnd I tracked exactly what that decision was.\n\nThis happened to three point two million people in 2025.\n\nDecember fifteenth, 2025.\n\nOpenAI released their advanced reasoning model.\n\nSame week, Anthropic launched Claude three point five Sonnet with computer control.\n\nWithin seventy-two hours, AI tools could handle tasks that took human teams weeks.\n\nI tracked forty-seven people through this transformation — across eight industries, four continents, ages twenty-six to fifty-two.\n\nThree survival patterns emerged.\n\nThe first pattern: people who experimented immediately. Sarah Chen is the clearest example.\n\nSarah Chen didn't wait for permission.\n\nDecember eighteenth — three days after the AI announcement — she signed up for everything.\n\nClaude. ChatGPT. Copy dot AI.\n\nHer husband found her at midnight, teaching Claude to analyze competitor campaigns.\n\n\"What are you doing?\"\n\n\"Learning how to survive.\"\n\nJanuary third — breakthrough moment.\n\nA competitive analysis that typically took two days was finished by eleven thirty AM.\n\nBut something was different about the quality.\n\nThe AI handled the data collection.\n\nSarah added the strategic thinking that competitors couldn't replicate.\n\nShe didn't replace herself with AI.\n\nShe became irreplaceable because of AI.\n\nThe second pattern: people who resisted the change. Mike Rodriguez represents this path."
            },
            {
                "name": "block2-mike",
                "section": "Mike's Story (3:15-4:45)",
                "text": "Mike Rodriguez made a different choice.\n\nEighteen years of legal research experience.\n\nWhen his firm introduced Harvey AI, Mike's response was immediate and final.\n\nHis words: \"I don't need a computer to tell me how to practice law.\"\n\nThat wasn't arrogance.\n\nMike believed something true — human judgment in law can't be outsourced.\n\nHe'd built his reputation on finding precedents other lawyers missed.\n\nOn understanding the nuance behind case law.\n\nOn being the guy partners trusted with impossible research.\n\nThe problem?\n\nHarvey AI didn't outsource his judgment. It accelerated it.\n\nAnd he missed the moment when that distinction mattered.\n\nWhile his colleagues learned Harvey AI, Mike doubled down on what made him valuable.\n\nFebruary reality check.\n\nHis research assignments were taking six hours.\n\nHis AI-assisted colleagues were finishing equivalent work in forty-five minutes.\n\nThe partners delivered their verdict.\n\n\"Mike, your efficiency metrics don't justify your position.\"\n\nMarch first — position eliminated.\n\nMike wasn't alone. Forty-three percent of workers who rejected AI training in the first sixty days faced similar outcomes within six months.\n\nThe third pattern: people who saw the shift as strategy. David Park exemplifies this approach."
            },
            {
                "name": "block3-david",
                "section": "David's Story (4:45-6:00)",
                "text": "David Park saw what others missed.\n\nWhen his company announced AI customer service integration, David didn't panic.\n\nHe studied the technology for two weeks.\n\nMapped what AI could and couldn't do.\n\nThen he wrote the memo that changed everything.\n\n\"AI can handle eighty percent of our ticket volume perfectly. But the twenty percent it can't handle — furious customers, complex technical issues, executive escalations — that's where we create customer loyalty.\"\n\nInstead of fighting the AI rollout, he designed it.\n\nResult: VP of Customer Experience.\n\nForty-eight percent salary increase.\n\nBut here's what connects these three stories...\n\nEach person had the exact same information on the exact same day.\n\nThe difference wasn't opportunity. It was response speed."
            },
            {
                "name": "block4-framework",
                "section": "Framework Revelation (6:00-8:30)",
                "text": "Sarah, Mike, and David weren't unique cases.\n\nI found this same pattern in forty-seven people across eight industries.\n\nThe people who succeeded all did three specific actions within ninety days of their company's AI announcement.\n\nThis is the Ninety-Day Rule.\n\nDays one to thirty: Immediate hands-on experimentation.\n\nWinners signed up for AI tools the day their company announced integration.\n\nNot when training started. Not when it became mandatory.\n\nThe day they heard it was coming.\n\nSarah spent thirty minutes every morning for thirty days testing different AI tools.\n\nShe gave Claude the same tasks she'd normally do manually.\n\nCompared outputs. Found the gaps. Learned the limits.\n\nMike? He never opened a single AI tool.\n\nDays thirty-one to sixty: Identify your irreplaceable complement.\n\nThey mapped what AI handled well versus what broke down.\n\nThen they became experts at the breakdown points.\n\nSarah discovered AI could generate competitive analysis in minutes.\n\nBut it couldn't interpret what that meant for strategy.\n\nCouldn't read between the lines of competitor behavior.\n\nCouldn't predict which insights would actually change business decisions.\n\nSo she became the strategic interpreter.\n\nDavid found AI could resolve eighty percent of customer tickets.\n\nBut it couldn't handle the twenty percent that required emotional intelligence.\n\nThe angry customers. The complex technical problems. The executive escalations.\n\nSo he became the human escalation specialist.\n\nDays sixty-one to ninety: Position yourself as the essential bridge.\n\nThey stopped competing with AI and started designing workflows that combined both.\n\nThey became the person who understood what AI could do and what humans had to do.\n\nSarah pitched herself as the \"AI-Human Strategy Director.\"\n\nNot just a marketer. The person who could harness AI speed and add human wisdom.\n\nDavid positioned himself as the \"Customer Experience Architect.\"\n\nNot just a manager. The designer of human-AI customer service systems.\n\nThey made themselves indispensable by becoming the integration point.\n\nHere's what makes this urgent.\n\nMost industries are already past day sixty of this transformation.\n\nIf you're in marketing, customer service, content creation, research, analysis — your ninety-day window is probably closing.\n\nIf you're watching this today, here's what you do.\n\nQuestion one: What am I doing manually that AI could accelerate?\n\nPick one task. Sign up for one AI tool. Test it for thirty minutes.\n\nQuestion two: What can I do that AI fundamentally cannot?\n\nFind the breakdown points. The judgment calls. The human moments.\n\nQuestion three: How do I become the bridge that makes both work better?\n\nDon't compete with AI. Design the workflow that needs both.\n\nThe question isn't whether this will reach your job.\n\nIt's whether you'll be Sarah or Mike when it does.\n\nThis shift isn't happening to us.\n\nIt's happening through us.\n\nThe question is: which side of it will you choose to be on?"
            },
            {
                "name": "block5-close",
                "section": "Brand Close (8:30-9:00)",
                "text": "If this changed how you see what's coming for your industry, there's more where this came from.\n\nThis is V-Real AI.\n\nWe're here to help you see what's coming — and position yourself correctly — before your ninety days are up.\n\nSubscribe for the insights that determine outcomes.\n\nThe next episode drops Tuesday."
            },
        ],
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
