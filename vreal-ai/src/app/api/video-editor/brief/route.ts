export const dynamic = 'force-dynamic';

// ── Types ─────────────────────────────────────────────────────────────────────

interface VideoEditorBriefRequest {
  video_title: string;
  hook_tts: string;
  chapters: Array<{
    title: string;
    tts_content: string;
    duration_estimate: string;
  }>;
  cta_tts: string;
  thumbnail_spec?: {
    main_text: string;
    sub_text?: string;
    color_accent: string;
    background: string;
  };
}

interface VideoEditorBriefResponse {
  project_settings: {
    timeline_name: string;
    resolution: '3840x2160';
    frame_rate: '30fps';
    color_space: 'Rec.709';
    audio_sample_rate: '48000 Hz';
  };
  intro_spec: {
    duration_seconds: number;
    animation: string;
    music_fade_in: string;
  };
  sections: Array<{
    section_id: string;
    section_title: string;
    estimated_duration: string;
    chapter_marker_label: string;
    broll_instructions: Array<{
      timestamp_hint: string;
      type: 'screen_recording' | 'stock_footage' | 'ai_generated_image' | 'text_animation';
      description: string;
      source_suggestion: string;
    }>;
    text_overlays: Array<{
      timestamp_hint: string;
      text: string;
      style: 'headline' | 'subtitle' | 'callout' | 'lower_third';
      animation: 'fade' | 'slide_up' | 'pop';
    }>;
    transition_in: string;
    pacing_note: string;
  }>;
  outro_spec: {
    duration_seconds: number;
    elements: string[];
    music_fade_out: string;
  };
  music_brief: {
    hook_mood: string;
    tutorial_mood: string;
    cta_mood: string;
    recommended_bpm_range: string;
    source_suggestions: string[];
    volume_guidance: string;
  };
  color_grade_brief: {
    overall_look: string;
    lut_suggestion: string;
    accent_color_hex: string;
    background_hex: string;
  };
  export_settings: {
    format: 'H.264' | 'H.265';
    resolution: '3840x2160';
    bitrate: string;
    audio_codec: string;
    filename_template: string;
  };
  nadia_notes: string;
}

// ── Slug helper ────────────────────────────────────────────────────────────────

function toSlug(title: string): string {
  return title
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
    .slice(0, 40);
}

// ── Prompt builder ─────────────────────────────────────────────────────────────

function buildPrompt(req: VideoEditorBriefRequest, timelineName: string): string {
  const chaptersJson = JSON.stringify(req.chapters, null, 2);
  const thumbnailJson = req.thumbnail_spec ? JSON.stringify(req.thumbnail_spec, null, 2) : 'null';
  const accentHex = req.thumbnail_spec?.color_accent ?? '#00D4FF';
  const backgroundHex = req.thumbnail_spec?.background ?? '#0A0F1E';

  return `You are Nadia Volkov — Video & Audio Director for @VRealAI, a faceless AI tools tutorial channel on YouTube.
Channel specs: 4K (3840x2160), 30fps, Rec.709, no talking head, all screen recordings + AI voiceover (Daniel, ElevenLabs).
You work exclusively in DaVinci Resolve. Your briefs are precise, technical, and production-ready.

Generate a complete DaVinci Resolve edit brief for the following video.

VIDEO TITLE: ${req.video_title}
TIMELINE NAME: ${timelineName}

HOOK TTS:
${req.hook_tts}

CHAPTERS:
${chaptersJson}

CTA TTS:
${req.cta_tts}

THUMBNAIL SPEC:
${thumbnailJson}

BRAND PALETTE:
- Navy background: #0A0F1E
- Cyan accent: #00D4FF
- Amber accent: #FFB347

PRODUCTION RULES:
1. B-roll for AI tool tutorials is PRIMARILY screen recordings of the tool being used. Use stock footage only for context shots (e.g., a person at a laptop, a cityscape for establishing). Use ai_generated_image sparingly for conceptual visuals.
2. Chapter markers use DaVinci Resolve color coding: hook section = red, tutorial chapters = blue, CTA = green.
3. Give specific timecode hints within each section (e.g., "0:05 - 0:15" relative to section start).
4. Intro is 2-3 seconds: animated @VRealAI logo + title card over the navy background.
5. Outro is 5-8 seconds: subscribe button animation, two end-screen cards (next video + playlist).
6. Music sits at -18dB under voiceover, -12dB for intro/outro.
7. Export as H.265 for 4K efficiency, 80 Mbps, AAC stereo 48kHz.
8. section_id values: "hook", "ch1", "ch2", ..., "cta" (matching the number of chapters provided).
9. color_grade_brief.accent_color_hex = "${accentHex}", background_hex = "${backgroundHex}".

Return ONLY valid JSON — no markdown fences, no comments — matching this exact structure:
{
  "project_settings": {
    "timeline_name": "${timelineName}",
    "resolution": "3840x2160",
    "frame_rate": "30fps",
    "color_space": "Rec.709",
    "audio_sample_rate": "48000 Hz"
  },
  "intro_spec": {
    "duration_seconds": <2-3>,
    "animation": "<description of logo/title animation>",
    "music_fade_in": "<fade-in description>"
  },
  "sections": [
    {
      "section_id": "<hook|ch1|ch2|...|cta>",
      "section_title": "<title>",
      "estimated_duration": "<e.g. 45-60 sec>",
      "chapter_marker_label": "<short DaVinci marker label>",
      "broll_instructions": [
        {
          "timestamp_hint": "<e.g. 0:05 - 0:15>",
          "type": "<screen_recording|stock_footage|ai_generated_image|text_animation>",
          "description": "<specific visual>",
          "source_suggestion": "<e.g. record Claude.ai demo, Pexels, Midjourney>"
        }
      ],
      "text_overlays": [
        {
          "timestamp_hint": "<e.g. 0:02 - 0:06>",
          "text": "<overlay text>",
          "style": "<headline|subtitle|callout|lower_third>",
          "animation": "<fade|slide_up|pop>"
        }
      ],
      "transition_in": "<transition description>",
      "pacing_note": "<pacing guidance for this section>"
    }
  ],
  "outro_spec": {
    "duration_seconds": <5-8>,
    "elements": ["<element1>", "<element2>"],
    "music_fade_out": "<fade-out description>"
  },
  "music_brief": {
    "hook_mood": "<mood description>",
    "tutorial_mood": "<mood description>",
    "cta_mood": "<mood description>",
    "recommended_bpm_range": "<e.g. 110-125 BPM>",
    "source_suggestions": ["Epidemic Sound", "Artlist"],
    "volume_guidance": "-18dB under voiceover, -12dB intro/outro"
  },
  "color_grade_brief": {
    "overall_look": "<look description>",
    "lut_suggestion": "<LUT name or description>",
    "accent_color_hex": "${accentHex}",
    "background_hex": "${backgroundHex}"
  },
  "export_settings": {
    "format": "H.265",
    "resolution": "3840x2160",
    "bitrate": "80 Mbps",
    "audio_codec": "AAC stereo 48kHz",
    "filename_template": "THEEDGEAI_${toSlug(req.video_title)}_4K_FINAL"
  },
  "nadia_notes": "<Nadia's overall production notes referencing DaVinci Resolve workflows, screen recording setup, audio sync, and anything specific to this video>"
}`;
}

// ── Claude call ────────────────────────────────────────────────────────────────

async function generateBrief(req: VideoEditorBriefRequest): Promise<VideoEditorBriefResponse> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');

  const timelineName = `THEEDGEAI_${toSlug(req.video_title)}_v1`;
  const prompt = buildPrompt(req, timelineName);

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 4096,
      messages: [{ role: 'user', content: prompt }],
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${err}`);
  }

  const data = await res.json() as { content: Array<{ type: string; text: string }> };
  const raw = data.content.find((b) => b.type === 'text')?.text ?? '';

  // Strip any accidental markdown fences
  const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/i, '').trim();

  return JSON.parse(cleaned) as VideoEditorBriefResponse;
}

// ── Route handler ──────────────────────────────────────────────────────────────

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<VideoEditorBriefRequest>;

    if (!body.video_title?.trim()) {
      return Response.json({ error: 'Missing required field: video_title' }, { status: 400 });
    }
    if (!body.hook_tts?.trim()) {
      return Response.json({ error: 'Missing required field: hook_tts' }, { status: 400 });
    }
    if (!Array.isArray(body.chapters) || body.chapters.length === 0) {
      return Response.json({ error: 'Missing required field: chapters (non-empty array)' }, { status: 400 });
    }
    if (!body.cta_tts?.trim()) {
      return Response.json({ error: 'Missing required field: cta_tts' }, { status: 400 });
    }

    const brief = await generateBrief({
      video_title: body.video_title,
      hook_tts: body.hook_tts,
      chapters: body.chapters,
      cta_tts: body.cta_tts,
      thumbnail_spec: body.thumbnail_spec,
    });

    return Response.json(brief);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    const isJson = message.includes('JSON');
    return Response.json(
      { error: isJson ? 'Failed to parse AI response as JSON — retry' : message },
      { status: 500 }
    );
  }
}
