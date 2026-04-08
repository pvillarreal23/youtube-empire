# V-Real AI — Project Context

## What Is This?

V-Real AI is a fully AI-powered, faceless YouTube documentary channel about AI tools, shifts, and transformation. Every aspect of production — scripting, voiceover, footage, editing, thumbnails, SEO, and publishing — is orchestrated by a team of 33 AI agents across 5 tiers.

**Owner:** Pedro Villarreal (@pvillarreal23)
**Channel:** @VRealAI
**Tagline:** "You're not paranoid. You're observant."
**Voice:** Julian (deep, rich, mature narrator via ElevenLabs)
**Style:** BBC/Netflix documentary — cinematic, intimate, never hustle-bro

## Revenue Target

$1M/year ($83K/month) through:
- YouTube AdSense (primary, months 1-6)
- Affiliate revenue (growth engine, month 2+)
- Sponsorships (month 6+ at 10K+ subs)
- Digital products (month 9+ at 25K+ subs)
- Newsletter monetization (month 4+ at 500+ list)

## Channel Strategy (v12)

- **Content Mix:** 50% Stories, 30% Breakdowns, 20% Playbooks
- **Publish Cadence:** 2x/week (Tuesday + Thursday, 2PM EST)
- **Target Length:** 8-12 minutes
- **Audience:** Ambitious professionals and entrepreneurs (25-45)
- **Quality Floor:** Minimum 7/10 quality score to publish

## Multi-Channel Plan

1. **V-Real AI** (NOW) — AI transformation documentaries
2. **Cash Flow Code** (Month 7) — Finance/business through AI lens
3. **Mind Shift** (Month 13) — Psychology and behavior change

Launch gates: Previous channel at 5K+ subs, consistent publishing, quality >7/10, revenue covering costs.

## Tech Stack

| Tool | Purpose | Cost |
|------|---------|------|
| Claude (Anthropic) | Strategy, code, orchestration | API usage |
| ElevenLabs | AI voiceover (Julian voice) | $20-40/mo |
| Kling AI (via fal.ai) | Cinematic AI video generation | $30-50/mo |
| Flux 2 Pro (via fal.ai) | AI image generation | Included |
| AssemblyAI | Premium captions (8.4% WER) | ~$0.006/min |
| Epidemic Sound | Licensed music | $15-30/mo |
| FFmpeg | Video assembly pipeline | Free |
| Next.js 15 | Frontend dashboard | Free |
| FastAPI | Backend API | Free |
| SQLAlchemy + SQLite | Database | Free |
| Make.com | Workflow automation | $0-15/mo |

**Total Budget:** $100-200/month

## Brand Identity

- **Primary Background:** #0A0F1E (deep navy)
- **Accent Cyan:** #00D4FF
- **Accent Amber:** #FFB347
- **Font:** Inter (Black for headlines, Regular for body)
- **Tone:** Intimate documentary — never preachy, never salesy, never hustle

## Agent Architecture (33 Agents, 5 Tiers)

### Tier 1 — Executive
- CEO Agent (master orchestrator)

### Tier 2 — VP Level
- Content VP (editorial calendar, quality gatekeeper)
- Operations VP (pipeline, scheduling, resource allocation)
- Analytics VP (data → decisions)
- Monetization VP (revenue streams, affiliates, sponsorships)

### Tier 3 — Channel Managers
- AI & Tech Channel Manager
- Finance & Business Channel Manager (future)
- Psychology & Behavior Channel Manager (future)

### Tier 4 — Specialists
- Scriptwriter, Hook Specialist, Storyteller
- Video Editor, Thumbnail Designer, Voice Director
- SEO Specialist, Shorts & Clips Agent

### Tier 5 — Support
- QA Lead, Automation Engineer, Finance Controller
- Project Manager, Reflection Council

## Production Pipeline

```
Research → Brief → Script → Pressure Test → Voice → Visuals → Music → Assembly → QA → Metadata → Upload → Post-Publish
```

Weekly cadence:
- **Sunday:** Topic research (30-45 min)
- **Monday-Tuesday:** Script writing + pressure testing
- **Wednesday:** Voice generation + visual production
- **Thursday:** Editing + music + assembly
- **Friday:** Thumbnail + metadata + scheduled upload
- **Publish:** Tuesday + Thursday at 2PM EST

## Repository Structure

```
youtube-empire/
├── agents/                     # 31 base agent definitions
│   ├── video_editor_agent.md
│   ├── scriptwriter_agent.md
│   ├── asset_manager_agent.md
│   └── ...
├── agents/vreal-ai/           # Tiered agent hierarchy
│   ├── tier-1/                # CEO + skills
│   ├── tier-2/                # VP agents + skills
│   ├── tier-3/                # Channel managers
│   ├── tier-4/                # Specialists
│   └── tier-5/                # Support agents
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── services/
│   │   │   ├── ai_media_generator.py
│   │   │   ├── video_assembler.py
│   │   │   ├── claude_service.py
│   │   │   └── agent_loader.py
│   │   └── routers/
│   │       ├── video_pipeline.py
│   │       ├── agents.py
│   │       └── threads.py
│   └── pyproject.toml
├── frontend/                  # Next.js dashboard
├── produce_ep001.py           # EP001 production runner
├── CONTEXT.md                 # This file
├── PRODUCTION_SOP.md          # 11-phase production SOP
├── SCRIPT_SOP.md              # 8-step script process
├── TOOLS_STATUS.md            # Tool/API integration status
├── VREAL_AI_METAPROMPT.md     # Session initialization prompt
├── EPISODE_BACKLOG.md         # Episode concept queue
└── EPISODE_DEBRIEF_LOG.md     # Post-publish learning log
```

## Current Status

- [x] 33 AI agents defined across 5 tiers
- [x] Full backend + frontend built
- [x] Video assembly pipeline (18-step FFmpeg)
- [x] AI media generation service (fal.ai integration)
- [x] Production SOP + Script SOP locked
- [x] EP001 "The Shift" script locked (v8-FINAL)
- [ ] EP001 voiceover generation
- [ ] EP001 visual production (14 scenes)
- [ ] EP001 end-to-end assembly
- [ ] YouTube channel setup + first upload
- [ ] Make.com automation wiring
- [ ] Episode backlog filled (3+ concepts)
- [ ] Multi-platform distribution setup
