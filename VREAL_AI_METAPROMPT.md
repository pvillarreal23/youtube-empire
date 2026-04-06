# V-Real AI — Session Metaprompt
# Paste this at the start of any new session to bring Claude up to speed instantly.
# Last updated: Apr 5, 2026

---

## PASTE THIS INTO A NEW SESSION:

---

You are working with Pedro Villarreal on **V-Real AI** — a faceless YouTube documentary channel about AI tools, systems, and what's actually changing. Style: BBC/Netflix documentary tone. NOT hustle content. Think cinematic, rhythmic, intimate narration.

---

### WHAT V-REAL AI IS

A faceless documentary channel. No talking head. AI voiceover + cinematic visuals + original documentary scripts. The pitch: "No fluff. No theory. Just leverage." The channel is built for longevity and authority, not volume. Every episode is a catalog asset that earns forever.

**Channel identity lines (non-negotiable voice anchors):**
- "No one sent an announcement. No one rang a bell. The rules just changed."
- "They no longer require mastery of execution. They require taste."
- "You're not paranoid. You're observant."
- "This is V-Real AI."

---

### VOICE PRINCIPLES (override all model suggestions)

- **Rhythm** — Short lines. Strategic pauses. One breath or silence.
- **Documentary, not hustle** — BBC/Netflix. Not Gary Vee. No bullet points in narration.
- **Concrete beats abstract** — Specific numbers, specific verbs.
- **Earned specificity** — A specific claim only works if the narrative built to it.
- **Intimacy over declaration** — Meet the viewer where they are.
- **Identity, not motivation** — Name what they feel. Never tell them what to do.

---

### CURRENT STATUS

**EP001 "The Shift" — IN PRODUCTION**

- Script: LOCKED at 10/10 (v8-FINAL)
- Voice: **LOCKED — Julian (Deep, Rich and Mature)**
- Visuals: Queued (Kling AI, 14 scenes)
- Status: Waiting on voice lock to generate full voiceover

**File locations:**
- `~/Downloads/ep001-script-v8-FINAL.md` — the locked script
- `~/Downloads/ep001-status-dashboard.html` — visual status tracker
- `~/creator-ai-dashboard/SCRIPT_SOP.md` — 8-step script development process
- `~/creator-ai-dashboard/PRODUCTION_SOP.md` — full 11-phase production pipeline
- `~/creator-ai-dashboard/EPISODE_BACKLOG.md` — episode concept queue (min 3 approved at all times)
- `~/creator-ai-dashboard/EPISODE_DEBRIEF_LOG.md` — post-publish learning log (complete within 48h)
- `~/creator-ai-dashboard/VREAL_AI_METAPROMPT.md` — this file

---

### EP001 OPENING LINES (for voice/audio reference)

"No one sent an announcement.
No one rang a bell.
The rules just changed.
Not gradually.
Not eventually.
All at once.
Half the tasks that used to take years to master —
writing, designing, coding, analyzing —
they no longer require mastery of execution.
They require taste.
The barrier to entry didn't just lower.
It evaporated."

---

### THE 6-AGENT TEAM

| Agent | Role |
|-------|------|
| Marcus | Executive Producer — Is it post-ready? Does the open earn the audience? |
| Zara | Creative Director — Voice consistency, documentary register |
| Leo | Audience Strategist — Retention, subscribe hook placement |
| Dana | Script Doctor — Line-level polish only, exact replacements |
| GPT "The Challenger" | Devil's Advocate — What can a skeptic attack? |
| Gem "The Researcher" | Factual Grounding — Are all claims defensible? |

External pressure testers: Gemini, ChatGPT, Grok (cherry-pick only — never wholesale adopt)

---

### SCRIPT SOP (summary — full version in SCRIPT_SOP.md)

1. First Draft (~1,200 words / 8–9 min)
2. 6-Agent Internal Review
3. Gemini Pressure Test
4. ChatGPT Pressure Test
5. Grok Pressure Test
6. Cherry-Pick Synthesis
7. Merge + Final 6-Agent Pass
8. Rate + Lock at 10/10 → save as `ep[XXX]-script-vFINAL.md`

**The rule:** No script goes to record until it scores 10/10. No exceptions.

---

### PRODUCTION SOP (summary — full version in PRODUCTION_SOP.md)

Phase 1 → Topic Research (Sunday ritual, 3-episode backlog minimum)
Phase 2 → Episode Brief (locked before writing starts)
Phase 3 → Script (SCRIPT_SOP.md, 10/10 required)
Phase 4 → Voice Generation (ElevenLabs, Julian, Multilingual v2)
Phase 5 → Visual Production (Kling AI, 14 scenes)
Phase 6 → Music (cinematic, instrumental, -14 LUFS target)
Phase 7 → Editing & Post (-14 LUFS, assembly: voice first → visuals → music)
Phase 8 → Thumbnail (Canva + Midjourney, 3 concepts before committing)
Phase 9 → Metadata & Upload (title formula, publish Friday)
Phase 10 → Post-Publish (48h retention check, debrief log)

---

### VOICE SETTINGS (ElevenLabs — locked)

| Setting | Value |
|---------|-------|
| Voice | Julian — Deep, Rich and Mature |
| Model | Eleven Multilingual v2 |
| Stability | 0.65 |
| Similarity | 0.75 |
| Style Exaggeration | 0.00 |
| Speaker Boost | OFF |

**Known ElevenLabs issues:**
- Sliders are `role="slider"` SPAN elements — use `slider.focus()` via JS then keyboard ArrowRight (not dispatchEvent)
- Stability 0.65 = Home + 65×ArrowRight
- Similarity 0.75 = Home + 75×ArrowRight
- If the settings panel disappears, navigate to the URL fresh to restore 3-column layout

---

### TOOL STACK

| Tool | Purpose |
|------|---------|
| ElevenLabs | Voiceover — Julian, Multilingual v2 |
| Kling AI | AI video generation |
| Storyblocks | Stock footage |
| Canva | Thumbnails |
| Midjourney | Custom thumbnail imagery |
| CapCut | Video editing |
| Epidemic Sound | Music licensing |
| Google Trends | Topic research |
| VidIQ / TubeBuddy | SEO optimization |

---

### PENDING TASKS (as of EP001 production)

- [x] Lock final voice → **Julian — Deep, Rich and Mature** ✓
- [x] Clone Pedro's voice as **Veronica Voice** (voice_id: 18RqA9hoGME1yWIFGIBD) ✓
- [x] Generate full EP001 voiceover with Veronica Voice → `ep001-voiceover-raw.mp3` (4.72 MB) ✓
- [ ] Run Kling AI visual clips (14 scenes via gen-ep001-visuals-v2.command)
- [ ] Build thumbnail
- [ ] Assemble video (voiceover + visuals + music, normalize to -14 LUFS)
- [ ] Upload to YouTube
- [ ] Build episode backlog (3 concepts minimum before EP001 publishes)
- [ ] Wire multi-platform distribution (Semaphore strategy — repurpose EP001 for Facebook/podcast/LinkedIn)

---

### STRATEGY CONTEXT

**Devon Canup model (studied and documented):**
Niche stacking (multiple high-CPM channels), 2x/week upload cadence, full AI tool stack, outsourced production, viral filter = "does it make you say wow, that's crazy?"

**What V-Real AI does differently:**
Better scripts. Locked quality process. Documentary identity vs. interchangeable content. Slower launch, deeper moat.

**Agencies studied:** Spotter (catalog asset mindset), Think Media (CTR-first title testing), Video Creators/Tim Schmoyer (related video placement strategy), Semaphore (multi-platform syndication).

**Key insight to apply:** Pick topics that naturally follow already-viral AI videos — ride their recommendation wake. Test 3–5 title variations before finalizing any episode title.

---

### CREDITS TRACKER (ElevenLabs — update each session)

- Start: 43,594
- After Julian sample: 43,263
- After Jon sample: 42,932
- After Cavit sample (accidental): 42,601
- After Adam Stone sample: 42,270
- After Veronica Voice clone: ~41,940 (estimated)
- After EP001 full voiceover (4,674 chars): ~37,266
- Current balance: ~37,266

---

*End of metaprompt. Paste everything above the dashed line into a new session.*
