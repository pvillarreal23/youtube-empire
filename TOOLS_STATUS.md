# V-Real AI — Tools & Integration Status

## Cloud Server (Claude Code — Strategy, Code, Assembly)

| Tool | Status | Notes |
|------|--------|-------|
| Python 3.11 | ✅ Ready | Backend runtime |
| FastAPI | ✅ Ready | API framework |
| Node.js | ✅ Ready | Frontend runtime |
| FFmpeg | ✅ Ready | Video assembly pipeline |
| Claude API | ✅ Ready | Agent orchestration |
| SQLite | ✅ Ready | Database |

## Local Machine (Asset Generation)

| Tool | Status | Notes |
|------|--------|-------|
| ElevenLabs | ✅ Ready | AI voiceover (Julian voice) |
| Kling AI (fal.ai) | ✅ Ready | AI video generation |
| Flux 2 Pro (fal.ai) | ✅ Ready | AI image generation |
| AssemblyAI | ✅ Ready | Caption generation (8.4% WER) |
| Pexels | 🔧 Needs Setup | Stock footage fallback |
| Epidemic Sound | 🔧 Needs Setup | Licensed music |
| Canva / Midjourney | 🔧 Needs Setup | Thumbnail design |

## Production Pipeline

```
Script (Claude) → Voice (ElevenLabs) → Footage (Kling AI + Pexels) → Music (Epidemic Sound) → Assembly (FFmpeg) → Captions (AssemblyAI) → Upload (YouTube)
```

## API Keys Status

| Key | Status | Service |
|-----|--------|---------|
| ANTHROPIC_API_KEY | ✅ Set | Claude API — agent orchestration |
| FAL_API_KEY | 🔧 Needs Setup | Kling AI + Flux 2 Pro via fal.ai |
| ASSEMBLYAI_API_KEY | 🔧 Needs Setup | Caption generation |
| ELEVENLABS_API_KEY | 🔧 Needs Setup | Voiceover generation |
| PEXELS_API_KEY | 🔧 Needs Setup | Stock footage |
| OPENAI_API_KEY | 🔧 Optional | Pressure test model |
| GEMINI_API_KEY | 🔧 Optional | Pressure test model |
| YOUTUBE_CREDENTIALS | 🔧 Needs Setup | Upload automation |

## Video Specifications (LOCKED)

| Setting | Value |
|---------|-------|
| Resolution | 3840x2160 (4K) or 1920x1080 |
| Frame Rate | 24fps (cinematic) or 30fps |
| Codec | H.264 (libx264) High Profile |
| CRF | 18 |
| Audio Codec | AAC 320kbps, 48kHz |
| Voice LUFS | -14 to -16 |
| Music LUFS | -25 to -30 (duck to -35 under voice) |
| Master LUFS | -14 integrated, -1 dBTP true peak |
| Color Space | Rec. 709 |
| Captions | AssemblyAI SRT (burned-in or sidecar) |

## Backend API Endpoints

### Agent System
- `GET /api/agents` — List all agents
- `GET /api/agents/{id}` — Agent detail
- `GET /api/agents/org/tree` — Organization chart

### Thread Messaging
- `GET /api/threads` — List threads
- `GET /api/threads/{id}` — Thread with messages
- `POST /api/threads` — Create thread
- `POST /api/threads/{id}/messages` — Send message

### Video Pipeline
- `POST /api/video/generate/clip` — AI video generation (Kling v2)
- `POST /api/video/generate/image` — AI image generation (Flux 2 Pro)
- `POST /api/video/generate/still-to-video` — Ken Burns motion
- `POST /api/video/generate/captions` — Caption generation (AssemblyAI)
- `POST /api/video/generate/episode` — Batch episode media
- `GET /api/video/pipeline/status` — Service health check

### System
- `GET /api/health` — Health check
