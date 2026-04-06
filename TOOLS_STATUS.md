# @VRealAI Video Pipeline — Tools Status
_Last updated: 2026-04-06_

## Production Environments

### Cloud Server (Claude Code — strategy, code, assembly)
| Tool | Status | Purpose |
|------|--------|---------|
| **Python 3.11** | Ready | Backend, video assembly, pressure testing |
| **FastAPI** | Ready | Backend API server (port 8000) |
| **Node.js** | Ready | Next.js frontend (port 3000) |
| **FFmpeg** | Ready | Video encoding, assembly, audio normalization |
| **Remotion** | Ready | Animated intros/outros, motion graphics |
| **Claude API** | Ready | Scripts, research, pressure testing (4-persona) |
| **SQLite (aiosqlite)** | Ready | Production pipeline database |

### Local Machine (Cowork — asset generation)
| Tool | Status | Purpose |
|------|--------|---------|
| **ElevenLabs** | Ready | Voiceover generation (Julian voice) |
| **Kling AI** | Ready | Custom AI video footage |
| **Pexels** | Ready | Free stock footage |
| **Epidemic Sound** | Ready | Music licensing |
| **Canva / Midjourney** | Ready | Thumbnail design |
| **Browser** | Ready | All web-based tools |

---

## Pipeline Overview

```
Script (Claude) → Voice (ElevenLabs) → Footage (Kling AI + Pexels) → Music (Epidemic Sound)
    ↓                                         ↓
Assembly (FFmpeg video_assembler.py) ← Assets land in output/ep[XXX]/
    ↓
Intro/Outro (Remotion) → Text Overlays → Audio Normalization → Final Export
    ↓
Upload (YouTube) → Distribution
```

**Cloud handles:** Script writing, video assembly, audio mixing, text overlays, quality gate
**Local handles:** Voice generation, footage creation, music selection, thumbnail design, YouTube upload

---

## Remotion Files
- `vreal-ai/src/remotion/Root.tsx` — Composition registry
- `vreal-ai/src/remotion/BrandedIntro.tsx` — 3s V-Real AI branded intro (1920x1080, 30fps)
  - V-shaped cyan logo with glow animation
  - "V-Real AI" brand text
  - Tagline: "You're not paranoid. You're observant."

---

## API Keys Required (.env)

| Key | Status | Service |
|-----|--------|---------|
| ANTHROPIC_API_KEY | Set | Claude (primary AI) |
| ELEVENLABS_API_KEY | Set | Voice generation |
| PEXELS_API_KEY | Needs setup | Stock footage auto-sourcing |
| OPENAI_API_KEY | Set (403 on cloud) | ChatGPT pressure testing |
| GEMINI_API_KEY | Set (403 on cloud) | Gemini pressure testing |
| GROK_API_KEY | Set (403 on cloud) | Grok pressure testing |
| KLING_API_KEY | Not set | AI video generation |
| YOUTUBE_CREDENTIALS | Not set | YouTube upload API |

**Note:** OpenAI, Gemini, and Grok APIs return 403 from the cloud server due to network restrictions. Workaround: Claude role-plays 4 different reviewer personas for pressure testing.

---

## Video Specs

| Setting | Value |
|---------|-------|
| Resolution | 1920x1080 |
| Frame rate | 30fps |
| Codec | H.264 (libx264) |
| CRF | 18 (high quality) |
| Audio | AAC 192kbps, 48kHz |
| Voice LUFS | -14 to -16 |
| Music LUFS | -28 (duck to -35 under voice) |
| Master LUFS | -14 (YouTube standard) |
