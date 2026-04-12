export const dynamic = 'force-dynamic';

interface QcRequest {
  hook: string;
  hook_tts: string;
  chapters: Array<{ title: string; content: string; tts_content: string; duration_estimate: string }>;
  cta: string;
  cta_tts: string;
  titles: string[];
  thumbnail_spec?: object;
  cta_type?: string;
}

interface QcIssue {
  severity: 'critical' | 'warning' | 'suggestion';
  section: string;
  issue: string;
  fix: string;
}

interface QcResponse {
  approved: boolean;
  score: number;
  issues: QcIssue[];
  strengths: string[];
  brand_voice_rating: number;
  tts_readability_rating: number;
  hook_strength_rating: number;
  summary: string;
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
    const body = await request.json() as Partial<QcRequest>;
    if (!body.hook?.trim()) {
      return Response.json({ error: 'Missing required field: hook' }, { status: 400 });
    }

    const prompt = `You are Marcus Webb — Quality Control Director for @VRealAI. Review this script for brand compliance and production quality.

BRAND STANDARDS:
- Faceless AI tutorial channel, opinionated and direct
- TTS-optimized: em-dashes for pauses, ellipses for breath, short sentences
- No fluff, no filler words ("amazing", "incredible", "game-changer" are banned)
- Hook must create tension before teaching
- CTA must be specific and actionable

HOOK: ${body.hook}
HOOK TTS: ${body.hook_tts}
CHAPTERS: ${JSON.stringify(body.chapters ?? [])}
CTA: ${body.cta}
CTA TTS: ${body.cta_tts}
TITLES: ${JSON.stringify(body.titles ?? [])}
CTA TYPE: ${body.cta_type ?? 'unknown'}

Return ONLY valid JSON:
{
  "approved": <true if score >= 70>,
  "score": <0-100>,
  "issues": [
    {"severity": "critical|warning|suggestion", "section": "<hook|chapter_N|cta|title>", "issue": "<description>", "fix": "<specific fix>"}
  ],
  "strengths": ["<what works well>"],
  "brand_voice_rating": <1-10>,
  "tts_readability_rating": <1-10>,
  "hook_strength_rating": <1-10>,
  "summary": "<2-3 sentence QC verdict>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as QcResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
