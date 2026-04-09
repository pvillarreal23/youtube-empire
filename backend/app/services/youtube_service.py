"""
YouTube upload service.

Uses the YouTube Data API v3 to upload videos as PRIVATE.
The user reviews in YouTube Studio and flips to public when ready.

Setup:
  1. Create a project in Google Cloud Console
  2. Enable YouTube Data API v3
  3. Create OAuth 2.0 credentials (Desktop app type)
  4. Download client_secrets.json to /backend/
  5. Run this script once to authorize: python -m app.services.youtube_service
  6. After that, uploads work automatically using the saved token

Make.com alternative:
  If you prefer, skip this service entirely and use Make.com's YouTube
  module to upload. Just send the video URL to Make.com via the webhook
  callback and let Make.com handle the upload.
"""

from __future__ import annotations

import os
import json
import httpx
from pathlib import Path

TOKENS_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "youtube_tokens.json"


def _load_tokens() -> dict | None:
    if TOKENS_PATH.exists():
        return json.loads(TOKENS_PATH.read_text())
    return None


def _save_tokens(tokens: dict):
    TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_PATH.write_text(json.dumps(tokens))


async def refresh_access_token(tokens: dict) -> str:
    """Refresh the OAuth access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post("https://oauth2.googleapis.com/token", data={
            "client_id": tokens["client_id"],
            "client_secret": tokens["client_secret"],
            "refresh_token": tokens["refresh_token"],
            "grant_type": "refresh_token",
        })
        resp.raise_for_status()
        data = resp.json()
        tokens["access_token"] = data["access_token"]
        _save_tokens(tokens)
        return data["access_token"]


async def upload_video(
    video_url: str,
    title: str,
    description: str,
    tags: list[str],
    category_id: str = "28",  # 28 = Science & Technology
    privacy: str = "private",
) -> dict:
    """
    Upload a video to YouTube as PRIVATE.

    Args:
        video_url: URL of the rendered video file
        title: Video title
        description: Full SEO description
        tags: List of tags
        category_id: YouTube category (28 = Science & Technology)
        privacy: "private", "unlisted", or "public"

    Returns:
        {"video_id": "...", "url": "https://youtube.com/watch?v=..."}
    """
    tokens = _load_tokens()
    if not tokens:
        raise Exception(
            "YouTube not authorized. Run: python -m app.services.youtube_service "
            "to set up OAuth tokens, or use Make.com for uploads instead."
        )

    access_token = await refresh_access_token(tokens)

    # Download the video file first
    async with httpx.AsyncClient(timeout=300) as client:
        video_resp = await client.get(video_url)
        video_resp.raise_for_status()
        video_bytes = video_resp.content

    # Upload to YouTube using resumable upload
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    async with httpx.AsyncClient(timeout=600) as client:
        # Step 1: Initialize resumable upload
        init_resp = await client.post(
            "https://www.googleapis.com/upload/youtube/v3/videos"
            "?uploadType=resumable&part=snippet,status",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Upload-Content-Type": "video/mp4",
                "X-Upload-Content-Length": str(len(video_bytes)),
            },
            json=metadata,
        )
        init_resp.raise_for_status()
        upload_url = init_resp.headers["Location"]

        # Step 2: Upload the video bytes
        upload_resp = await client.put(
            upload_url,
            headers={
                "Content-Type": "video/mp4",
                "Content-Length": str(len(video_bytes)),
            },
            content=video_bytes,
        )
        upload_resp.raise_for_status()
        result = upload_resp.json()

    video_id = result["id"]
    return {
        "video_id": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "status": privacy,
    }


# --- CLI for initial OAuth setup ---

if __name__ == "__main__":
    print("YouTube OAuth Setup")
    print("=" * 40)
    print()
    print("1. Go to https://console.cloud.google.com")
    print("2. Create a project → Enable YouTube Data API v3")
    print("3. Create OAuth 2.0 credentials (Desktop app)")
    print()

    client_id = input("Client ID: ").strip()
    client_secret = input("Client Secret: ").strip()

    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri=urn:ietf:wg:oauth:2.0:oob&"
        f"response_type=code&"
        f"scope=https://www.googleapis.com/auth/youtube.upload&"
        f"access_type=offline"
    )

    print(f"\nOpen this URL in your browser:\n{auth_url}\n")
    code = input("Paste the authorization code: ").strip()

    import httpx
    resp = httpx.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": "urn:ietf:wg:oauth:2.0:oob",
        "grant_type": "authorization_code",
    })
    resp.raise_for_status()
    data = resp.json()

    tokens = {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }
    _save_tokens(tokens)
    print(f"\nTokens saved to {TOKENS_PATH}")
    print("YouTube upload is now ready.")
