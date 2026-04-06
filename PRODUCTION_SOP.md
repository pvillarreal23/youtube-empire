# V-Real AI — Full Production SOP
# Standard Operating Procedure | All Episodes
# Established: EP001 "The Shift" — Apr 5, 2026

---

## THE RULE

No episode ships without clearing every phase in this document.
The script phase is governed by SCRIPT_SOP.md.
This document covers everything else — before and after the script.

---

## PHASE 1 — TOPIC RESEARCH

**When:** Weekly. Every Sunday. 30–45 min.
**Output:** 3–5 episode concepts queued in the backlog before you need them.
**Never start an episode without a full backlog. Running out of ideas mid-production kills momentum.**

### Research Ritual
1. Check Google Trends for AI/tech topics spiking this week
2. Scan r/artificial, r/MachineLearning, r/singularity for signal
3. Review top-performing faceless AI/tech channels for topic gaps they haven't covered
4. Ask: *"What happened this week in AI that nobody has explained well yet?"*
5. Apply the Devon Canup filter: **Does this make you go "wow, that's crazy"?** If not, skip it.
6. Apply the Tim Schmoyer filter: **What massive video would YouTube recommend us after?** Pick topics that ride the wake of already-viral AI content — related video placement is the #1 traffic source for new subscribers.
7. Log surviving concepts in `EPISODE_BACKLOG.md` with working title + one-line pitch

### Topic Scoring Criteria
- [ ] Passes the "wow" test — genuinely surprising or counterintuitive
- [ ] Has a strong point of view — not just a news recap
- [ ] Evergreen enough to be relevant in 60 days
- [ ] Can be told in documentary style without showing a face
- [ ] Has visual potential — footage or AI imagery can carry it
- [ ] Topically adjacent to a video already going viral — rides the recommendation algorithm

---

## PHASE 2 — PRE-PRODUCTION

**When:** Before writing starts.
**Output:** Approved episode brief.

### Episode Brief (required before writing)
```
EP: [number]
Working Title: [title]
Core Question: [the single question this episode answers]
Angle: [what makes our take different from everyone else's]
Key Claim: [the most surprising/concrete thing we'll prove]
Target Length: ~1,200 words / 8–9 min
Visual Direction: [2–3 sentences on the look and feel]
```

No writing starts until the brief is locked.

---

## PHASE 3 — SCRIPT

Follow **SCRIPT_SOP.md** exactly.
Do not proceed to Phase 4 until the script scores 10/10.

**Deliverable:** `ep[XXX]-script-vFINAL.md` saved to Downloads.

---

## PHASE 4 — VOICE GENERATION

**Voice:** Julian — Deep, Rich and Mature
**Platform:** ElevenLabs Text to Speech
**Model:** Eleven Multilingual v2

### Settings (locked — do not change without team sign-off)
| Setting | Value |
|---------|-------|
| Stability | 0.65 |
| Similarity | 0.75 |
| Style Exaggeration | 0.00 |
| Speaker Boost | OFF |

### Process
1. Open ElevenLabs → Text to Speech
2. Confirm Julian is selected and all settings match the table above
3. Paste the final script text
4. Generate speech
5. Listen to full playback — flag any mispronunciations or pacing issues
6. If needed, regenerate problem sections only (do not regenerate full script unnecessarily — credits cost money)
7. Download audio file
8. Save as `ep[XXX]-voiceover-raw.mp3` in Downloads

### Common Issues
- Credits remaining: Track balance before each generation (331 chars ≈ 331 credits)
- Slider values reset when voice is switched — always verify before generating
- If settings panel disappears, navigate to the page URL fresh to restore layout

---

## PHASE 5 — VISUAL PRODUCTION

**Platform:** Kling AI
**Style:** Cinematic, documentary-grade. No talking heads. No screen recordings.

### Scene Breakdown Process
1. Read the final script and identify natural visual beats (every 30–60 seconds)
2. Write a one-sentence visual prompt for each scene
3. Categorize each scene: stock footage / AI-generated / text overlay
4. Run AI generations via Kling for scenes that need custom visuals
5. Source stock footage for remaining scenes (Storyblocks or equivalent)

### Visual Quality Bar
- Each shot must feel like it belongs in a Netflix documentary
- No generic stock footage of people typing on laptops
- Prefer abstract, atmospheric, or symbolic over literal
- Consistency in color grade across all scenes

**Deliverable:** All scene assets organized in `ep[XXX]-visuals/` folder.

---

## PHASE 6 — MUSIC

**Target:** Cinematic, understated. Score, not playlist.
**Source:** Epidemic Sound or licensed library

### Selection Criteria
- [ ] Builds without overwhelming the voiceover
- [ ] Tonally matches the episode's emotional arc
- [ ] No lyrics — pure instrumental
- [ ] Has a clean intro and outro for fade in/out

### Layering
- Main score: continuous under narration
- Hit moments: brief musical emphasis on key revelations
- Silence: use it deliberately — don't fill every gap

**Deliverable:** `ep[XXX]-music-main.mp3` + `ep[XXX]-music-hits.mp3`

---

## PHASE 7 — EDITING & POST-PRODUCTION

### Assembly Order (automated via video_assembler.py)
1. Normalize voice audio to -14 LUFS
2. Prepare scene clips (trim, apply motion effects — zoom, pan, ken burns)
3. Concatenate scenes with branded background fills for gaps
4. Mix voice + auto-ducked music (sidechain compression)
5. Apply text overlays (kinetic typography, lower thirds, data viz)
6. Prepend Remotion intro / append outro
7. Final export at CRF 18 (high quality H.264)

**Manual alternative:** If automated assembly needs tweaks, the voiceover is the spine — cut visuals to narration rhythm, not the other way around.

### Audio Standards
| Setting | Target |
|---------|--------|
| Final mix LUFS | -14 LUFS (YouTube standard) |
| Peak ceiling | -1 dBTP |
| Voiceover level | Clear and present — never buried |
| Music level | Supporting — should disappear when you focus on it |

### Quality Check Before Export
- [ ] Watch full episode from viewer's perspective — no context
- [ ] First 30 seconds: would a cold viewer stay?
- [ ] Audio levels consistent throughout
- [ ] No visual jump cuts that don't serve the rhythm
- [ ] End card / subscribe prompt in the right place (around 85% mark)

**Deliverable:** `ep[XXX]-FINAL.mp4` exported at 1080p minimum (4K preferred)

---

## PHASE 8 — THUMBNAIL

**Tool:** Canva + Midjourney for custom imagery

### Thumbnail Formula
- Single dominant visual — one image that earns a stop-scroll
- Bold, readable text at mobile size (test at 120px wide)
- 3 words maximum on the thumbnail — let curiosity do the work
- High contrast — dark background or bright background, not mid-tone grey
- Text completes the title — don't repeat what the title already says
- No clickbait — the thumbnail must be honest about what the video delivers

### Process
1. Generate 3 thumbnail concepts before committing to one
2. A/B test mentally: which one would you click at 2am on mobile?
3. Export at 1280x720px

**Deliverable:** `ep[XXX]-thumbnail-FINAL.png`

---

## PHASE 9 — METADATA & UPLOAD PREP

**Complete all of this before uploading.**

### Title Formula
- Lead with the hook — the counterintuitive claim or surprising angle
- Include a high-search keyword naturally
- Keep under 60 characters for clean display
- Test: would this title make Devon Canup's "wow" test?

### Title Testing Ritual (Think Media method — mandatory)
Never go with the first title. Write 3–5 variations before picking one.
For each variation ask: *"Would I click this at midnight on my phone with no context?"*
Pick the one that creates the strongest curiosity gap — not the cleverest one.

**Title variation template:**
```
Option 1: [Direct claim — states the counterintuitive truth]
Option 2: [Question — puts the viewer in the scenario]
Option 3: [Stakes — what they stand to lose or gain]
Option 4: [Contrast — what people think vs. what's actually true]
Option 5: [Urgency — why this matters right now]
```
Test all 5. Pick the strongest. Kill your darlings.

### Description
```
[2–3 sentence hook that expands on the title — not a summary]

V-Real AI is a faceless documentary channel about AI tools, systems,
and what's actually changing. No fluff. No theory. Just leverage.

[Relevant timestamps if episode warrants it]

Subscribe for weekly episodes.
```

### Tags
- 5–10 tags max — quality over quantity
- Mix: broad (artificial intelligence, AI tools) + specific (episode topic keywords)

### Category
Science & Technology

### Checklist Before Hitting Publish
- [ ] Title finalized
- [ ] Description written
- [ ] Thumbnail uploaded
- [ ] Tags added
- [ ] Category set
- [ ] End screen configured
- [ ] Monetization enabled
- [ ] Scheduled publish time set (consistent day + time every week)

---

## PHASE 10 — POST-PUBLISH

### First 48 Hours
- Reply to every comment in the first 24 hours — signals engagement to algorithm
- Check retention graph at 48 hours — identify where viewers drop
- Note the average view duration percentage

### Learning Loop (after each episode)
```
EP[XXX] Debrief:
- Views at 48h:
- CTR:
- AVD (average view duration):
- Retention cliff (where most viewers left):
- Best-performing thumbnail test:
- What to do differently next episode:
```

Save debrief to `EPISODE_DEBRIEF_LOG.md`.

---

## EPISODE BACKLOG MANAGEMENT

Always have minimum 3 episode concepts approved before current episode publishes.
If backlog drops below 3, Sunday topic research session is mandatory before any other production work.

---

## TOOL STACK

| Tool | Purpose | Where |
|------|---------|-------|
| Claude API | Script writing, strategy, pressure testing, video assembly orchestration | Cloud server |
| FFmpeg + video_assembler.py | Automated video assembly, audio normalization, text overlays | Cloud server |
| Remotion | Animated intros/outros, motion graphics | Cloud server |
| ElevenLabs | Voiceover — Julian, Multilingual v2 | Local (browser) |
| Kling AI | AI video generation for custom scenes | Local (browser) |
| Pexels | Free stock footage (also auto-sourced via footage_sourcer.py) | Cloud + Local |
| Canva / Midjourney | Thumbnail design | Local (browser) |
| Epidemic Sound | Music licensing | Local (browser) |
| Google Trends | Topic research | Local (browser) |

---

## CADENCE

| Day | Activity |
|-----|---------|
| Sunday | Topic research + backlog review |
| Monday–Tuesday | Script development (SCRIPT_SOP.md) |
| Wednesday | Voice generation + visual production |
| Thursday | Editing + music |
| Friday | Thumbnail + metadata + upload |
| Saturday | Buffer / overflow / debrief |

**Publish day: Friday.** Every week. Protect it.

---

## THE BENCHMARK

EP001 "The Shift" sets the quality floor.
Every episode must clear that bar before it ships.
Never publish an episode you wouldn't want to be the first one a new subscriber watches.

---

## PHASE 11 — MULTI-PLATFORM DISTRIBUTION

**Principle (Semaphore model):** Every episode is produced once and distributed everywhere.
Each platform gets a native version — not a repost, a re-edit optimized for that platform's algorithm.

### Distribution Checklist (per episode)

**YouTube (primary)**
- Full episode as produced

**Facebook Video**
- Re-edit for Facebook's format: hook in first 3 seconds, captions burned in, 3–8 min sweet spot
- Facebook's algorithm rewards watch time and comments — cut anything that doesn't earn a reaction
- Upload natively to Facebook, not a YouTube link

**Podcast / Audio**
- Export voiceover-only version (no music bed, or very light)
- Upload to Spotify, Apple Podcasts via RSS feed
- Title + description optimized for podcast search

**LinkedIn**
- Write a 150–200 word post that captures the episode's core insight
- End with a question to drive comments
- Link to YouTube in first comment, not the post body (LinkedIn suppresses outbound links)
- Post within 24 hours of YouTube publish

**Short-form (YouTube Shorts / TikTok / Reels)**
- Pull the single strongest 30–60 second moment from each episode
- Add captions, reframe vertically if needed
- Post as a teaser with CTA to full episode

### Distribution Schedule
| Platform | When |
|---------|------|
| YouTube | Friday (publish day) |
| LinkedIn post | Friday same day |
| Facebook video | Saturday |
| Podcast | Saturday |
| Short-form clip | Sunday |

---

*V-Real AI Production SOP — living document. Update after each episode based on what you learn.*
