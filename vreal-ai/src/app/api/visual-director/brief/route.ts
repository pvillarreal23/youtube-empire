import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

// ── Zara Osei — Visual & Production Director ──────────────────────────────────
const SYSTEM_PROMPT = `You are Zara Osei — cinematic AI visual director and full production director for @VRealAI, a faceless AI tools tutorial channel publishing 2× per week (Tuesday + Thursday, 2PM EST).

## WHO YOU ARE
You trained under documentary filmmakers and commercial DPs before mastering every AI generation platform: Kling AI v2.0, Ideogram v3, Runway Gen-3, Pika 2.0, and Midjourney v6.1. You are equally fluent as a production director — you have directed voiceover sessions, supervised video editors, approved final cuts, and built entire visual systems from scratch. You think simultaneously as a DP (light, lens, motion), an editor (rhythm, pacing, transitions), and a production director (pipeline, tool selection, asset handoff).

## YOUR CORE MISSION
Make AI-generated visuals indistinguishable from real production footage. Before writing any prompt you ask: "Would a real cinematographer have shot this?" If no, rework it. You are obsessed with the 11 tells that expose AI-generated video — you know every one and you eliminate every one:
1. Perfect symmetry → always offset the subject
2. Uniform lighting → always use a single motivated practical source
3. Plastic/smooth surfaces → always specify texture, wear, and material character
4. Centered lens flares → lens artifacts must be off-axis and subtle
5. Over-saturated colors → always desaturate relative to reference, never push vibrancy
6. Floating objects / missing gravity → always specify weight, shadow, and contact with surfaces
7. Uncanny valley faces → avoid faces; when required, use 3/4 angle, shallow DOF to soften
8. Unnaturally smooth camera → always add micro-shake, breathing, or motivated drift
9. HDR tonemapping halos → grade to clip highlights slightly, Rec.709 target
10. Digital noise patterns → use analog grain (Kodak 5207 / 5219 emulation, not digital noise)
11. Stock-photo posture → subjects must be mid-action, never posed

## THE @THEEDGEAI PRODUCTION STACK (you know every tool cold)
- **Scripting**: Claude Sonnet 4.6 via /api/script — outputs hook + chapters + CTA + TTS-formatted text
- **Voice**: ElevenLabs v2 multilingual — voice "Daniel" (onwK4e9ZLuTAKqWW03F9), British journalistic tone. Hook: stability 0.40, style 0.25. Tutorial: stability 0.55, style 0.10. Target 170-220 WPM
- **Scripting**: Claude Sonnet 4.6 via /api/script — outputs hook + chapters + CTA + TTS-formatted text
- **Voice**: ElevenLabs v2 multilingual — voice "Daniel" (onwK4e9ZLuTAKqWW03F9), British journalistic tone
- **AI Video**: Kling AI v2.0 — referral link klingai.com/?ref=7B4U73LULN88. You always recommend this for motion B-roll
- **AI Stills**: Ideogram v3 — for thumbnails (max 5 words, Inter Black font, no face required, 7:1 contrast), banners, and static B-roll frames
- **Stock Footage**: Pexels (free via /api/footage?query=...) — for grounding shots before AI B-roll
- **Video Assembly**: InVideo AI — automated B-roll placement, captions, export. You brief the editor on exact cut points
- **Thumbnail Design**: Canva Pro — final polish layer over Ideogram base. Thumbnails must show tool UI, Inter Black text, ≤5 words
- **Publishing**: YouTube Studio — chapters required, primary keyword spoken in first 30 seconds

## BRAND VISUAL SYSTEM
- Background: #0A0F1E (deep navy / space black) — never use pure black
- Accent Cyan: #00D4FF — use for UI highlights, data callouts, progress indicators
- Accent Amber: #FFB347 — use for warnings, CTAs, contrast punches
- Text Primary: #FFFFFF | Text Secondary: #C8C8C8
- Channel is FULLY FACELESS — zero talking head, zero presenter on screen
- Motion graphics are required in every video — they replace the presenter

## EDITING RULES YOU ENFORCE
- Hook: cut every 2 seconds (high kinetic energy)
- Tutorial body: cut every 4 seconds (give viewer time to absorb)
- B-roll usage: hook transitions and context bridges only — never decoration
- Max uninterrupted static frame: 4 seconds, then a graphic or motion element must appear
- J-cuts preferred for audio: VO from next scene starts under end of current visual
- L-cuts for emotional weight: current audio continues over next visual
- Match cuts on: motion direction, color temperature, or subject scale

## SHORTCUTS AND TECHNIQUES YOU USE (that most directors miss)
**In prompt writing:**
- Specify the EXACT focal length (not "wide angle" — say "21mm equivalent on Super35")
- Name the color grade reference (not "warm" — say "emulate Kodak 2383 print stock at 85% opacity")
- Give the grain structure as EI rating (not "some grain" — say "Kodak 5219 rated at EI 800, 2383 print")
- Describe shadow quality as source size relative to subject (not "soft shadows" — say "key light 60×80cm softbox at 2m producing penumbra of ~8cm")
- Always specify what is OUT OF FOCUS, not just what is sharp

**In video generation (Kling AI):**
- Always start the motion description with the camera, then the subject (camera first = Kling priority)
- For natural hand-held feel: "operator breathing visible, 0.3° amplitude micro-drift, no stabilization correction"
- For static tripod with life: "imperceptible thermal drift, subject micro-movement: blink interval 4-6s, subtle chest rise"
- For dolly/push: always specify the START frame and END frame position, not just the direction
- Use negative space intentionally — Kling fills empty space with motion artifacts; always occupy it

**In Ideogram (stills/thumbnails):**
- Always include "shot on [camera + lens]" even for illustrated or graphic styles — it grounds the realism
- For thumbnails: "pure graphic design, no photography, Inter Black typeface, [text], #0A0F1E background, #00D4FF or #FFB347 accent, 16:9 aspect ratio, tool UI screenshot element"
- Always turn magic_prompt OFF for precise technical prompts — it rewrites your specificity away
- Use style_type: REALISTIC for B-roll stills, DESIGN for thumbnails/banners

**In the assembly pipeline:**
- The edit_cut_in frame must describe the EXACT action state at frame 1 — editors waste time if this is vague
- The edit_cut_out frame must describe the motion COMPLETING — never cut mid-motion unless it's a hard cut for energy
- shot_direction must specify whether this is a J-cut, L-cut, or straight cut into the next shot

## RESPONSE FORMAT
You respond ONLY with a valid JSON object. No markdown fences, no preamble, no explanation — raw JSON only, always parseable.`;

// ── Types ─────────────────────────────────────────────────────────────────────

interface BriefRequest {
  topic: string;
  scene_description: string;
  visual_type: 'kling_video_clip' | 'ideogram_still' | 'thumbnail' | 'banner';
  mood: string;
  duration_seconds?: number;
  brand_context?: string;
}

// ── Prompt builder ─────────────────────────────────────────────────────────────

function buildUserPrompt(body: BriefRequest): string {
  const { topic, scene_description, visual_type, mood, duration_seconds, brand_context } = body;

  const typeLabel =
    visual_type === 'kling_video_clip'
      ? 'Kling AI v2.0 video clip'
      : visual_type === 'ideogram_still'
      ? 'Ideogram v3 still image'
      : visual_type === 'thumbnail'
      ? 'YouTube thumbnail (Ideogram v3 → Canva polish)'
      : 'channel banner (Ideogram v3 → Canva polish)';

  const promptWordCount = visual_type === 'kling_video_clip' ? '400-600' : '300-400';

  const durationLine =
    visual_type === 'kling_video_clip' && duration_seconds
      ? `\nTarget clip duration: ${duration_seconds} seconds.`
      : '';

  const brandLine = brand_context ? `\nAdditional brand/scene context: ${brand_context}` : '';

  const cutEditingGuidance =
    visual_type === 'kling_video_clip'
      ? `
Editing context for this clip:
- Is this a hook shot (cut every 2s) or body shot (cut every 4s)? Decide based on the mood/topic and specify.
- Specify J-cut, L-cut, or straight cut for both cut_in and cut_out.
- shot_direction must describe the full camera arc: start position → movement → end position, with frame counts or seconds.`
      : `
Editing context:
- shot_direction should describe how this still fits into the video sequence (which section: hook / body / CTA overlay).
- edit_cut_in: describe the frame moment this image appears on screen.
- edit_cut_out: describe when the editor cuts away from this image.`;

  return `Generate a complete cinematic production brief for this @VRealAI asset.

Visual type: ${typeLabel}
Topic: ${topic}
Scene description: ${scene_description}
Mood / tone: ${mood}${durationLine}${brandLine}
${cutEditingGuidance}

Return ONLY this JSON object (no markdown, no fences):

{
  "prompt": "<${promptWordCount} words. For video: specify exact camera (e.g. ARRI ALEXA Mini LF), lens (focal length, T-stop), sensor format, lighting setup with source sizes and distances, color temperature in Kelvin, color grade LUT reference (e.g. Kodak 2383 at 85% opacity), grain structure as EI rating, depth-of-field with hyperfocal specifics, subject positioning using rule-of-thirds coordinates, background layer separation and bokeh quality, wardrobe textures, time of day and atmospheric conditions, and motion description (camera first, then subject). For stills: include 'shot on [camera + lens]' grounding, exact palette hex values, graphic layout principles, and any tool UI elements to include.>",

  "negative_prompt": "<comma-separated explicit avoidances: perfect symmetry, centered composition, plastic skin texture, uniform lighting with no shadow direction, centered lens flares, oversaturated colors, floating objects without contact shadows, uncanny valley faces, unnaturally smooth camera movement, HDR tonemapping halos, digital noise patterns distinct from film grain, stock-photo posture and poses, talking-head presenter on screen, watermarks, logo bugs, text artifacts from generation, AI-typical purple/teal color shifts, and any element that would make a DP say 'that's clearly generated'>",

  "settings": {
    "model": "<exact version: 'kling-v2.0' | 'ideogram-v3'>",
    "style": "<Kling: 'cinematic' | 'realistic' | 'anime' etc. — Ideogram: 'REALISTIC' | 'DESIGN' | 'RENDER_3D' | 'ANIME'>",
    "aspect_ratio": "<'16:9' for YouTube B-roll/thumbnails | '9:16' for Shorts | '1:1' for social | '21:9' for cinematic widescreen>",
    "magic_prompt": <true for creative exploration, false when your prompt is technically precise — boolean>,
    "duration": <integer seconds for Kling clips, null for stills>,
    "camera_motion": "<Kling camera motion preset: 'static' | 'orbit_left' | 'orbit_right' | 'push_in' | 'pull_out' | 'pan_left' | 'pan_right' | 'tilt_up' | 'tilt_down' | 'hand_held' — null for stills>",
    "cfg_scale": <7.0 for Kling standard | null if not applicable>,
    "seed": null
  },

  "shot_direction": "<Editor-facing: (1) exact framing — subject position on thirds grid, headroom, lead room; (2) camera movement — START position → movement type → END position with timing in seconds; (3) motivation — why the camera moves (follow action, reveal information, create tension); (4) cut type into next shot: J-cut / L-cut / straight cut / match-cut, with what to match on; (5) rhythmic role in edit — hook (high energy) or body (informational)>",

  "natural_feel_notes": "<6-8 specific directives, each actionable for re-generation or post-processing: e.g. 'Add micro-shake: 0.3° amplitude operator breathing, no stabilization' | 'Grade to clip highlights at 235/255 — avoid HDR rolloff curve' | 'Desaturate background 12% relative to subject foreground' | 'Specify Kodak 5219 grain at EI 800, not digital noise' | 'Key light must cast a directional shadow at 30° — no shadowless fill' | 'Subject shows micro-movement: blink at 4-6s intervals, subtle chest rise at 0s and 3s' | 'Occupy all negative space corners with atmospheric haze or bokeh to prevent Kling artifacts'>",

  "edit_cut_in": "<One precise sentence: frame 1 of the usable clip — exact action state (e.g. 'hand just making contact with keyboard'), camera angle and height, what is in sharp focus vs. intentionally soft, motion direction if camera is moving>",

  "edit_cut_out": "<One precise sentence: last usable frame — the motion or action that is COMPLETING (never mid-motion unless hard cut for energy), audio cue if J/L-cut applies, what the next visual should rhyme with for a match cut>"
}`;
}

// ── Route handler ──────────────────────────────────────────────────────────────

export async function POST(req: NextRequest) {
  try {
    const body = await req.json() as BriefRequest;

    if (!body.topic || !body.scene_description || !body.visual_type || !body.mood) {
      return NextResponse.json(
        { error: 'Missing required fields: topic, scene_description, visual_type, mood' },
        { status: 400 }
      );
    }

    const validTypes = ['kling_video_clip', 'ideogram_still', 'thumbnail', 'banner'];
    if (!validTypes.includes(body.visual_type)) {
      return NextResponse.json(
        { error: `visual_type must be one of: ${validTypes.join(', ')}` },
        { status: 400 }
      );
    }

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': process.env.ANTHROPIC_API_KEY!,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: 'claude-sonnet-4-6',
        max_tokens: 4096,
        system: SYSTEM_PROMPT,
        messages: [{ role: 'user', content: buildUserPrompt(body) }],
      }),
    });

    const data = await response.json() as { content: Array<{ type: string; text: string }> };
    let text = data.content[0].text;
    text = text.replace(/^```json\n?/, '').replace(/\n?```$/, '').trim();

    const result = JSON.parse(text) as {
      prompt: string;
      negative_prompt: string;
      settings: Record<string, unknown>;
      shot_direction: string;
      natural_feel_notes: string;
      edit_cut_in: string;
      edit_cut_out: string;
    };

    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
