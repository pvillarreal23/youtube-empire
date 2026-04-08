# V-Real AI — Production Standard Operating Procedure

## Overview

This document governs the complete production pipeline for V-Real AI. Every episode follows these 11 phases without exception. Quality is non-negotiable — if a phase cannot be completed at standard, the episode is delayed, never shipped at lower quality.

**Benchmark:** EP001 "The Shift" sets the quality floor. Every future episode must match or exceed it.

---

## PHASE 1 — Topic Research

**Owner:** Senior Researcher + Trend Researcher
**Cadence:** Weekly Sunday ritual (30-45 minutes)
**Output:** 3-5 scored concepts added to EPISODE_BACKLOG.md

### Process
1. Scan sources: Google Trends, Reddit (r/artificial, r/MachineLearning, r/technology), Twitter/X, Hacker News, industry newsletters
2. Apply **Devon Canup "Wow" Filter**: Would the average person say "wow" hearing this? If not, skip.
3. Apply **Tim Schmoyer Related-Video Filter**: Would this appear in the "suggested" sidebar of a top-performing AI video? If not, reconsider.
4. Score each concept on: search demand (25%), audience match (25%), retention potential (20%), timeliness (15%), competition density (15%)
5. Top 3-5 concepts go to EPISODE_BACKLOG.md

### Handoff Rule
Minimum 3 approved concepts must exist in the backlog at ALL times. If the backlog drops below 3, mandatory research before any other work.

---

## PHASE 2 — Pre-Production

**Owner:** Content VP + Channel Manager
**Duration:** 1-2 hours
**Output:** Locked episode brief

### Episode Brief Template
```
EPISODE BRIEF:
Episode: EP[XXX]
Channel: V-Real AI
Topic: [Topic]
Pillar: [Story / Breakdown / Playbook]

Core Question: [The question this episode answers]
Angle: [Our unique perspective]
Key Claim: [The one thing viewers will remember]
Visual Direction: [Cinematic mood, key scenes, visual metaphors]

Target Length: [8-12 minutes]
Monetization Hook: [Affiliate / AdSense / None for early eps]
Publish Window: [Tuesday or Thursday, 2PM EST]
```

### Approval Gate
Content VP must sign off before script writing begins. No exceptions.

---

## PHASE 3 — Script

**Owner:** Scriptwriter + Hook Specialist + Storyteller
**Duration:** 2 days (Monday-Tuesday)
**Output:** `ep[XXX]-script-vFINAL.md` scoring 7/10+
**Governed by:** SCRIPT_SOP.md

### Process
1. Scriptwriter produces first draft (~1,200 words / 8-9 min)
2. Hook Specialist reviews and rewrites opening (0-30 seconds)
3. Storyteller reviews narrative arc and emotional beats
4. 6-agent internal review panel scores the script
5. Multi-model pressure test (Claude, Gemini, ChatGPT, Grok)
6. Cherry-pick synthesis — take only lines that are more precise
7. Final merge + 6-agent pass
8. Consensus 10/10 required before recording

### Quality Gate
- Minimum quality score: 7/10 (10-point rubric)
- Hook must score 8+ on scroll-stop power
- No script ships until it scores 10/10 across all models and agents

---

## PHASE 4 — Voice Generation

**Owner:** Voice Director
**Duration:** 1-2 hours (Wednesday AM)
**Output:** `ep[XXX]-voiceover-raw.mp3`

### Voice Settings (LOCKED — Do Not Change)
- **Voice:** Julian — Deep, Rich and Mature
- **Model:** Eleven Multilingual v2
- **Stability:** 0.65
- **Similarity:** 0.75
- **Style Exaggeration:** 0.00
- **Speaker Boost:** OFF

### Process
1. Split script into 4-6 blocks (natural section breaks)
2. Generate each block via ElevenLabs API
3. Review for mispronunciations, pacing issues, robotic artifacts
4. Regenerate problem sections (adjust text phrasing if needed)
5. Concatenate all blocks into final voiceover
6. Verify: clean audio, natural rhythm, -14 to -16 LUFS

### Handoff
Clean voiceover file ready for assembly. Flag any sections that need attention during editing.

---

## PHASE 5 — Visual Production

**Owner:** Video Editor + Asset Manager
**Duration:** Concurrent with Phase 4 (Wednesday)
**Output:** Scene assets in `output/ep[XXX]-visuals/`

### Footage Hierarchy (Priority Order)
1. **Kling AI custom video** — Cinematic, documentary-grade (hero moments)
2. **Cinematic stock video** — Artgrid, Storyblocks (supporting shots)
3. **AI-generated images** — Flux 2 Pro with Ken Burns motion
4. **Screen recordings** — Only for tool demos, with professional annotations
5. **Motion graphics** — Data visualizations, animated explainers
6. **Stock photos** — LAST resort, only with significant motion applied

### Scene Breakdown
- Every 30-60 seconds of script = 1 scene
- Each scene gets: primary visual + 2-3 B-roll alternatives
- Start visual production when script is approved (before voiceover)

### Quality Standards
- All footage: 4K or 1080p minimum
- AI-generated: no coherence artifacts, no text artifacts, smooth motion
- Netflix-grade quality: would this look at home in a documentary?

### Banned Footage
- Generic "person typing on laptop"
- Low-resolution content
- Watermarked clips
- Robot stock footage
- Photos used as video without Ken Burns/motion

---

## PHASE 6 — Music

**Owner:** Video Editor
**Duration:** 1-2 hours (Wednesday-Thursday)
**Output:** Background music track(s) matching emotional arc

### Requirements
- Cinematic, instrumental, NO lyrics
- Builds with the narrative — quiet during intimate moments, rising during revelations
- BPM matches editing pace
- Must not overpower voice at any point

### Audio Levels
- Music: -25 to -30 LUFS (background)
- Duck to -35 LUFS under voice (auto-ducking)
- Swell up during purely visual sequences

### Sources
- Primary: Epidemic Sound (licensed)
- Fallback: Soundraw/AIVA (AI-generated)
- Emergency: FFmpeg-generated ambient pad

---

## PHASE 7 — Editing & Post-Production

**Owner:** Video Editor
**Duration:** Full day (Thursday)
**Output:** `ep[XXX]-FINAL.mp4`

### Assembly Pipeline (18-Step)
See `backend/app/services/video_assembler.py` for automated pipeline.

1. Process AI voiceover (EQ, compression, warmth, LUFS)
2. Lay voiceover on timeline
3. Mark section breaks from script
4. Plan visual sequences for each section
5. Layer primary visuals (AI video, motion graphics, B-roll)
6. Apply Ken Burns to still images
7. Scale all to target resolution
8. Conform frame rate
9. Tighten pacing — enforce 2-second rule
10. Add lower thirds, kinetic text, data visualizations
11. Burn captions from SRT
12. Mix music with auto-ducking
13. Mix SFX synced to visual cuts
14. Mix ambient layer
15. Merge 4-layer audio mix
16. LUFS normalization (-14 integrated, -1 dBTP true peak)
17. Apply color grade / LUT
18. Final render + validation report

### Quality Checks
- No static visual >2 seconds
- Minimum 15 visual changes per minute
- Pattern interrupt every 45-60 seconds (major) and 15-20 seconds (minor)
- Audio at -14 LUFS integrated
- Captions word error rate <5%

---

## PHASE 8 — Thumbnail

**Owner:** Thumbnail Designer
**Duration:** 2-3 hours (Thursday-Friday)
**Output:** 1280x720px PNG (3 concepts, strongest selected)

### Requirements
- Single dominant visual (one focal point)
- Maximum 3 words of text
- High contrast — readable at mobile thumbnail size
- Must complement title (not repeat it)
- Face/emotion when possible (AI-generated if needed)
- Test: would you click this at 120px width?

### Process
1. Extract strongest visual frame from video
2. Design 3 thumbnail concepts
3. Select strongest (team vote or A/B test if available)
4. Export at 1280x720px, <2MB

---

## PHASE 9 — Metadata & Upload

**Owner:** SEO Specialist + Channel Manager
**Duration:** 1-2 hours (Friday AM)
**Output:** Fully optimized upload, scheduled

### Title
- Under 60 characters
- Primary keyword in first 3 words
- 3-5 variations tested
- Must create curiosity gap

### Description
- First 2 lines: hook + value prop (visible before "Show More")
- Timestamps for chapters
- Affiliate links with disclosure
- Related videos from channel
- Keywords woven naturally (500+ words)

### Tags
- 15-25 relevant tags
- Mix of broad (AI, technology) and specific (tool names, concepts)
- Include common misspellings of key terms

### Upload Checklist
- [ ] Title optimized
- [ ] Description complete with timestamps
- [ ] Tags comprehensive
- [ ] Thumbnail uploaded
- [ ] End screen configured
- [ ] Cards added
- [ ] Captions uploaded (.srt)
- [ ] Category: Science & Technology or Education
- [ ] Scheduled: Tuesday or Thursday, 2PM EST

---

## PHASE 10 — Post-Publish

**Owner:** Channel Manager + Community Manager
**Duration:** 48 hours after publish
**Output:** Debrief in EPISODE_DEBRIEF_LOG.md

### First 48 Hours Protocol
1. **0-30 min:** Share to Twitter, LinkedIn, Instagram
2. **0-1 hour:** Heart first 20-30 comments, reply to every early comment
3. **24 hours:** Check CTR — if below 4%, consider thumbnail swap
4. **48 hours:** Full debrief — retention analysis, performance metrics, learnings

### Metrics to Capture
- Views, CTR, AVD (average view duration), AVD %, subscribers gained
- Top traffic source
- Biggest drop-off point + hypothesis + fix
- Best-performing thumbnail, title

---

## PHASE 11 — Multi-Platform Distribution

**Owner:** Social Media Manager + Shorts & Clips Agent
**Duration:** Staggered Friday-Sunday
**Output:** Content distributed across all platforms

### Semaphore Model
Produce once, distribute everywhere:
- **YouTube:** Primary (full episode)
- **YouTube Shorts:** 3-5 clips per episode within 48 hours
- **TikTok:** Re-formatted vertical clips
- **Instagram Reels:** Re-formatted vertical clips
- **LinkedIn:** Professional angle clip + written post
- **Facebook:** Full video repost
- **Podcast:** Audio-only version
- **Newsletter:** Episode summary + exclusive insight

### Automation
Wire via Make.com webhooks for automatic distribution triggers.

---

## Weekly Production Cadence

| Day | Track A (Tuesday Publish) | Track B (Thursday Publish) |
|-----|---------------------------|----------------------------|
| Sunday | Topic research | Topic research |
| Monday | Script writing | Brief approval |
| Tuesday | **PUBLISH** + Post-publish | Script writing |
| Wednesday | Voice + visuals (Track B) | Voice + visuals |
| Thursday | Thumbnail + metadata (Track B) | **PUBLISH** + Post-publish |
| Friday | Upload scheduled (Track B) | Multi-platform distribution |
| Saturday | Buffer day (sacred) | Buffer day (sacred) |
