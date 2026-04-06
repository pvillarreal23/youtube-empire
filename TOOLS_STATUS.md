# @VRealAI Video Pipeline — Tools Status
_Last updated: 2026-04-03_

## ✅ Installed & Ready

| Tool | Version / Notes |
|------|-----------------|
| **Homebrew** | 5.1.3 — installed at `/opt/homebrew/bin/brew` (not in default PATH; run `export PATH="/opt/homebrew/bin:$PATH"` or add to `~/.zshrc`) |
| **ffmpeg** | v8.1 — installed at `/opt/homebrew/bin/ffmpeg`. Use for video encoding, transcoding, merging audio/video. |
| **OBS Studio** | 32.1.1 — installed at `/Applications/OBS.app`. Use for screen recording, live streaming, scene management. |
| **Node.js** | v22.22.1 — at `/opt/homebrew/bin/node` |
| **Remotion** | v4.0.443 — `remotion`, `@remotion/cli`, `@remotion/player` added to `creator-ai-dashboard` |

### Remotion Files Created
- `src/remotion/Root.tsx` — Remotion entry point with `BrandedIntro` composition
- `src/remotion/BrandedIntro.tsx` — 3s (90 frames @ 30fps), 1920×1080 branded intro
  - Background: `#0A0F1E` (dark navy)
  - Accent color: `#00D4FF` (cyan)
  - Animated logo, brand name, tagline, accent line

To preview in Remotion Studio:
```bash
export PATH="/opt/homebrew/bin:$PATH"
cd /Users/pedrovillarreal/creator-ai-dashboard
npx remotion studio src/remotion/Root.tsx
```

---

## ⚠️ Missing — Needs Manual Install

| Tool | Why / How to Install |
|------|----------------------|
| **DaVinci Resolve** | Not found at `/Applications/DaVinci Resolve/`. Large download (~3 GB). Download free from: https://www.blackmagicdesign.com/products/davinciresolve |

---

## 🔧 Fix Recommended

**Add Homebrew to your shell PATH permanently** so tools like `ffmpeg`, `node`, `npm`, `obs` work without full paths:

```bash
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

---

## Pipeline Overview

```
Record (OBS) → Edit (DaVinci Resolve) → Encode/Process (ffmpeg) → Animate (Remotion) → Publish
```

- **OBS**: capture raw footage, screen recordings, webcam
- **DaVinci Resolve**: full NLE editing, color grading, audio mix (install manually)
- **ffmpeg**: batch encoding, format conversion, audio extraction, thumbnail generation
- **Remotion**: programmatic animated intros/outros, lower thirds, motion graphics
