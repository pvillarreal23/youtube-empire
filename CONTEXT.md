# V-Real AI — Project Context

## What Is This?

V-Real AI (@VRealAI) is a **fully AI-powered, faceless YouTube documentary channel** about AI tools and transformation, targeting $1M/year revenue. The entire production pipeline — from research to scripting to voiceover to video editing to publishing — is run by **33 AI agents** organized across 9 tiers.

**Owner:** Pedro Villarreal (@pvillarreal23)
**Channel Voice:** Julian — deep, rich, mature narrator (ElevenLabs)
**Tagline:** "You're not paranoid. You're observant."
**Tone:** BBC/Netflix documentary. Cinematic. Intimate. Not tutorials. Not hype.

---

## The Big Picture

Pedro is building this channel **transparently** — the audience knows it's AI-built. The growth strategy:

1. Build the channel autonomously with AI agents
2. Be fully transparent about how it's made and how much it earns
3. Grow the audience (AI beginners who want to learn, not experts)
4. Once proven, teach the audience how to do the same thing
5. Monetize through courses, products, and community — NOT from Day 1

**Target audience:** People who **don't know anything about AI** and are just starting. NOT advanced users. Get them using AI first, then introduce tools, then teach them to make money with it.

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | Next.js 15, TypeScript, Tailwind CSS | Dashboard + API routes |
| Backend | FastAPI, SQLAlchemy, aiosqlite | Agent orchestration, production pipeline |
| Video | Remotion (React), FFmpeg | Animated intros, video assembly |
| Voice | ElevenLabs (Julian voice) | Voiceover generation |
| Footage | Pexels (free stock), Kling AI | B-roll sourcing |
| AI Models | Claude (primary), ChatGPT, Gemini, Grok | Scripts, research, pressure testing |
| Automation | Make.com webhooks | Production workflow triggers |
| Hosting | YouTube (primary), Gumroad (products) | Distribution + sales |

---

## Repository Structure

```
youtube-empire/
├── agents/                    # 33 AI agent definitions (markdown)
│   └── vreal-ai/
│       ├── tier-1/            # CEO Agent
│       ├── tier-2/            # VPs (Content, Analytics, Monetization, Operations)
│       ├── tier-3/            # Channel Managers
│       ├── tier-4/            # Production (Scriptwriter, Video Editor, Voice Director, etc.)
│       ├── tier-5/            # Quality (QA Lead, Compliance, Finance, Reflection Council)
│       ├── tier-6/            # Growth (SEO, Social Media, Shorts, Thumbnail)
│       ├── tier-7/            # Revenue (Affiliate, Newsletter, Digital Products, Partnerships)
│       ├── tier-8/            # Support (Secretary, Workflow Orchestrator, Project Manager)
│       └── tier-9/            # Research (Senior Researcher, Trend Researcher, Data Analyst)
│
├── vreal-ai/                  # Main application
│   ├── backend/               # FastAPI backend (port 8000)
│   │   ├── app/
│   │   │   ├── models/        # SQLAlchemy models (production, agents, skills, etc.)
│   │   │   ├── routers/       # API endpoints (production, agents, skills, etc.)
│   │   │   ├── services/      # Core services:
│   │   │   │   ├── video_assembler.py    # FFmpeg 7-step video assembly
│   │   │   │   ├── footage_sourcer.py    # Auto B-roll sourcing (Pexels + Kling AI)
│   │   │   │   ├── pressure_test.py      # Multi-model quality review (4 personas)
│   │   │   │   ├── agent_memory.py       # Agent learning + skill tracking
│   │   │   │   ├── skill_growth.py       # XP-based agent skill progression
│   │   │   │   ├── claude_service.py     # Claude API integration
│   │   │   │   ├── youtube_uploader.py   # YouTube Data API upload
│   │   │   │   └── make_integration.py   # Make.com webhook triggers
│   │   │   └── main.py
│   │   └── .env               # API keys (ANTHROPIC, ELEVENLABS, PEXELS, YOUTUBE, etc.)
│   │
│   └── src/                   # Next.js frontend (port 3000)
│       ├── app/               # Pages + 75+ API proxy routes
│       ├── components/        # Dashboard (mobile-first pipeline view)
│       ├── config/            # production-bible.ts (brand colors, animation rules)
│       └── remotion/          # BrandedIntro.tsx (V-Real AI animated intro)
│
├── insights/                  # Strategy documents
│   ├── strategy-v12-final.md  # Current strategy (scored 9.62/10)
│   └── [agent]-insights.md    # Per-agent insight logs (33 files)
│
├── products/                  # Digital products (in development)
│   ├── prompt-library/        # First product: AI Prompt Library ($9-19)
│   └── lead-magnet/           # Free: 10 Best AI Marketing Prompts
│
├── PRODUCTION_SOP.md          # 7-phase production workflow
├── SCRIPT_SOP.md              # Script writing standards
├── TOOLS_STATUS.md            # Tool integration status
├── ep001-the-shift-v10.md     # EP001 script (ready for production)
└── ep001-script.json          # EP001 metadata
```

---

## Production Pipeline

```
Research → Script → Voiceover → Footage → Edit → SEO → Quality Gate → Publish
```

Each stage is handled by specific AI agents. The Quality Gate runs a **4-model pressure test** (Claude, ChatGPT, Gemini, Grok personas). Videos must score **9+/10** from all reviewers or loop back.

**Video specs:** 1920x1080, 30fps, H.264, CRF 18, -14 LUFS master audio

---

## Channel Strategy (v12 — Scored 9.62/10)

**Content mix:** 45% Breakdowns, 40% Playbooks, 15% Stories (85% evergreen)
**Publishing:** 2 videos/week (4-6 min) → 3/week (8-12 min) by Month 3
**Shorts:** Daily from Day 1
**Platform:** YouTube-first for 6 months
**Monetization:** Trust-first. Affiliates only for tools we use. No courses until validated.

**Revenue targets (conservative):**
- Month 6: 8K subs / $600/mo
- Month 12: 40K subs / $4K/mo
- Month 24: 180K subs / $22K/mo
- $1M annual: Month 30-36

**Product ladder:** Free lead magnet → Prompt Library ($9-19) → Workflow Guide ($19-39) → Mini-Course ($49-99) → Cohort Course ($197-497)

---

## Agent System (33 Agents, 9 Tiers)

Agents have:
- **Personality traits** and specializations defined in markdown
- **XP-based skill growth** (Apprentice → Journeyman → Expert → Master → Grandmaster)
- **Memory system** tracking performance across tasks
- **Meta-prompting** for advanced reasoning
- **Collaboration protocols** between tiers

**Key agents:**
| Agent | Tier | Role |
|-------|------|------|
| CEO Agent | 1 | Strategic decisions, final approvals |
| Content VP | 2 | Content strategy, editorial direction |
| Monetization VP | 2 | Revenue strategy, product roadmap |
| Scriptwriter | 4 | Script drafting (Julian's voice) |
| Video Editor | 4 | Visual assembly, motion graphics |
| Voice Director | 4 | ElevenLabs voiceover QA |
| SEO Specialist | 6 | Titles, descriptions, tags, thumbnails |
| Quality Lead | 5 | Pressure testing, final quality gate |
| Digital Product Manager | 7 | Course/product creation and launches |

---

## Current State

### What's Built
- Full FastAPI backend with all models, routers, and services
- Next.js dashboard with mobile-first pipeline view
- 33 agent definitions with skill tracking
- Video assembly pipeline (FFmpeg-based, 7-step)
- Footage auto-sourcing (Pexels + Kling AI)
- Multi-model pressure testing system
- Branded intro animation (Remotion — V-Real AI branding)
- EP001 "The Shift" script (v10, ready for production)
- Channel strategy v12 (scored 9.62/10 across 4-model pressure test)
- 8 Next.js API proxy routes for dashboard → backend

### What's In Progress
- First digital product: AI Prompt Library
- Free lead magnet: 10 Best AI Prompts
- Course research (best faceless YouTube channel courses)

### What Needs Work
- EP001 end-to-end production run (script → final video)
- YouTube channel setup and first upload
- Email list / newsletter setup (beehiiv)
- Gumroad store setup for digital products
- External API access (OpenAI, Gemini, Grok return 403 from cloud server — using Claude multi-persona workaround)

---

## Brand Identity

| Element | Value |
|---------|-------|
| Name | V-Real AI |
| Handle | @VRealAI |
| Tagline | "You're not paranoid. You're observant." |
| Voice | Julian (ElevenLabs — deep, rich, mature) |
| Background color | #0A0F1E (deep navy) |
| Accent primary | #00D4FF (electric cyan) |
| Accent secondary | #FFB347 (warm amber) |
| Font | Inter |
| Logo | V-shaped icon with cyan glow |

---

## Key Files to Know

| File | What It Does |
|------|-------------|
| `insights/strategy-v12-final.md` | The master channel strategy |
| `PRODUCTION_SOP.md` | How episodes are produced |
| `SCRIPT_SOP.md` | How scripts are written |
| `ep001-the-shift-v10.md` | First episode script |
| `vreal-ai/backend/app/services/video_assembler.py` | Video assembly engine |
| `vreal-ai/backend/app/services/pressure_test.py` | Quality testing system |
| `vreal-ai/src/remotion/BrandedIntro.tsx` | Animated intro |
| `vreal-ai/src/components/dashboard.tsx` | Main dashboard UI |
| `vreal-ai/src/config/production-bible.ts` | Visual/audio standards |
| `agents/vreal-ai/tier-7/digital-product-manager.md` | Product strategy agent |

---

## Git Info

- **Repo:** pvillarreal23/youtube-empire
- **Current branch:** claude/improve-video-editing-mDM2y
- **Remote:** origin

---

## Environment Variables Needed

```
ANTHROPIC_API_KEY=        # Claude API (primary AI model)
ELEVENLABS_API_KEY=       # Voice generation (Julian)
PEXELS_API_KEY=           # Free stock footage
YOUTUBE_CREDENTIALS=      # YouTube Data API
YOUTUBE_TOKEN=            # YouTube OAuth token
OPENAI_API_KEY=           # ChatGPT (pressure testing)
GEMINI_API_KEY=           # Gemini (pressure testing)
GROK_API_KEY=             # Grok (pressure testing)
KLING_API_KEY=            # AI video generation
MAKE_WEBHOOK_*=           # Make.com automation webhooks (12 endpoints)
```

---

## Philosophy

1. **Transparent.** The audience knows this channel is AI-built. We show them how.
2. **Beginner-first.** Our audience doesn't know AI yet. We teach them to USE it before we teach tools.
3. **Trust before money.** No aggressive monetization. Earn trust first.
4. **Quality gate.** Nothing ships below 9/10. Ever.
5. **Pedro approves, AI builds.** Pedro is the decision-maker. The 33 agents are the workforce.
