"""
Notification service — sends review package to the operator.

After the pipeline completes, sends an email with:
  1. Script text
  2. Thumbnail image (or concepts)
  3. SEO metadata (title, description, tags)
  4. YouTube link (private) for video review

Also supports Discord/Telegram notifications.
"""

from __future__ import annotations

import httpx
from app.config import (
    NOTIFICATION_EMAIL,
    NOTIFICATION_WEBHOOK_URL,
    DISCORD_WEBHOOK_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)


async def send_review_package(
    title: str,
    script: str,
    seo_package: str | None = None,
    thumbnail_brief: str | None = None,
    shorts_scripts: str | None = None,
    youtube_url: str | None = None,
    social_posts: str | None = None,
    newsletter_draft: str | None = None,
):
    """
    Send the complete review package via all configured channels.
    """
    # Build the review summary
    summary = f"NEW VIDEO PACKAGE READY FOR REVIEW\n{'=' * 40}\n\n"
    summary += f"TITLE: {title}\n\n"

    if youtube_url:
        summary += f"YOUTUBE (PRIVATE): {youtube_url}\n"
        summary += "→ Review in YouTube Studio, flip to Public when ready\n\n"

    summary += f"SCRIPT:\n{'-' * 20}\n{script[:3000]}\n\n"

    if seo_package:
        summary += f"SEO PACKAGE:\n{'-' * 20}\n{seo_package[:1500]}\n\n"

    if thumbnail_brief:
        summary += f"THUMBNAIL CONCEPTS:\n{'-' * 20}\n{thumbnail_brief[:1000]}\n\n"

    if shorts_scripts:
        summary += f"SHORTS SCRIPTS:\n{'-' * 20}\n{shorts_scripts[:1000]}\n\n"

    if social_posts:
        summary += f"SOCIAL MEDIA POSTS:\n{'-' * 20}\n{social_posts[:1000]}\n\n"

    if newsletter_draft:
        summary += f"NEWSLETTER DRAFT:\n{'-' * 20}\n{newsletter_draft[:1000]}\n\n"

    summary += "Reply APPROVE in Discord/Telegram to publish, or manage in YouTube Studio."

    # Send via all configured channels
    results = {}

    if DISCORD_WEBHOOK_URL:
        results["discord"] = await _send_discord(summary)

    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        results["telegram"] = await _send_telegram(summary)

    if NOTIFICATION_WEBHOOK_URL:
        results["webhook"] = await _send_webhook(title, summary)

    return results


async def _send_discord(message: str) -> bool:
    """Send to Discord via webhook."""
    try:
        # Discord webhook has 2000 char limit per message
        chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
        async with httpx.AsyncClient(timeout=30) as client:
            for chunk in chunks:
                await client.post(DISCORD_WEBHOOK_URL, json={"content": chunk})
        return True
    except Exception:
        return False


async def _send_telegram(message: str) -> bool:
    """Send to Telegram."""
    try:
        # Telegram has 4096 char limit
        chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
        async with httpx.AsyncClient(timeout=30) as client:
            for chunk in chunks:
                await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                    json={"chat_id": TELEGRAM_CHAT_ID, "text": chunk},
                )
        return True
    except Exception:
        return False


async def _send_webhook(title: str, summary: str) -> bool:
    """Send to a generic webhook (Make.com, Zapier, etc.)."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(NOTIFICATION_WEBHOOK_URL, json={
                "event": "review_package_ready",
                "title": title,
                "summary": summary,
            })
        return True
    except Exception:
        return False
