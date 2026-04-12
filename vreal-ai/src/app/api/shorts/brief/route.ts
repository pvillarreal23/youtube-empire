export const dynamic = 'force-dynamic';

interface ShortsBriefRequest {
  video_title: string;
  hook_tts: string;
  chapters: Array<{ title: string; tts_content: string; duration_estimate: string }>;
  cta_tts: string;
}

interface ShortsClip {
  clip_id: string;
  source_section: string;
  title: string;
  hook_line: string;
  script: string;
  duration_seconds: number;
  screen_recording_hint: string;
  text_overlay: string;
  trending_angle: string;
}

interface ShortsBriefResponse {
  clips: ShortsClip[];
  posting_schedule: Array<{ day: string; clip_id: string; caption: string; hashtags: string[] }>;
  repurposing_notes: string;
}

async function callClaude(prompt: string): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: 'claude-sonnet-4-6', max_tokens: 2048, messages: [{ role: 'user', content: prompt }] }),
  });
  if (!res.ok) throw new Error(`Anthropic API error ${res.status}: ${await res.text()}`);
  const data = await res.json() as { content: Array<{ type: string; text: string }> };
  const raw = data.content.find((b) => b.type === 'text')?.text ?? '';
  return raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/i, '').trim();
}

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<ShortsBriefRequest>;
    if (!body.video_title?.trim()) return Response.json({ error: 'Missing required field: video_title' }, { status: 400 });
    if (!Array.isArray(body.chapters) || body.chapters.length === 0) return Response.json({ error: 'Missing required field: chapters' }, { status: 400 });

    const prompt = `You are Kai Nakamura — Shorts & Clips Specialist for @VRealAI. Create YouTube Shorts briefs from this long-form video.

VIDEO TITLE: ${body.video_title}
HOOK: ${body.hook_tts}
CHAPTERS: ${JSON.stringify(body.chapters)}
CTA: ${body.cta_tts}

Create 3-4 Shorts (45-60 sec each) that can stand alone AND drive views to the long-form video.

Return ONLY valid JSON:
{
  "clips": [
    {
      "clip_id": "short_1",
      "source_section": "<which chapter/section>",
      "title": "<Shorts title, 60 chars max>",
      "hook_line": "<first 3 seconds — must stop the scroll>",
      "script": "<full 45-60 sec TTS script with em-dashes and ellipses>",
      "duration_seconds": <45-60>,
      "screen_recording_hint": "<what to show on screen>",
      "text_overlay": "<bold text overlay for the hook moment>",
      "trending_angle": "<what trending format this uses: POV, tutorial, reaction, etc>"
    }
  ],
  "posting_schedule": [
    {"day": "Day 1 (publish day)", "clip_id": "short_1", "caption": "<caption>", "hashtags": ["#Shorts", "#AI"]}
  ],
  "repurposing_notes": "<notes on how these Shorts complement the long-form video>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as ShortsBriefResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
