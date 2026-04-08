export const dynamic = 'force-dynamic';

interface SeoRequest {
  topic: string;
  tool_name: string;
  titles: string[];
  hook: string;
  chapters: Array<{ title: string; content: string }>;
}

interface SeoResponse {
  recommended_title: string;
  description: string;
  tags: string[];
  hashtags: string[];
  chapters_timestamps: string;
  pinned_comment: string;
  seo_score: number;
  keyword_density: Record<string, number>;
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
    const body = await request.json() as Partial<SeoRequest>;
    if (!body.topic?.trim() || !body.tool_name?.trim()) {
      return Response.json({ error: 'Missing required fields: topic, tool_name' }, { status: 400 });
    }

    const titlesJson = JSON.stringify(body.titles ?? []);
    const chaptersJson = JSON.stringify(body.chapters ?? []);

    const prompt = `You are Ethan Park — SEO Specialist for @VRealAI YouTube channel. Optimize this video for maximum discoverability.

TOPIC: ${body.topic}
TOOL: ${body.tool_name}
TITLE OPTIONS: ${titlesJson}
HOOK EXCERPT: ${(body.hook ?? '').slice(0, 300)}
CHAPTERS: ${chaptersJson}

Return ONLY valid JSON:
{
  "recommended_title": "<best title from options or improved version, 60 chars max>",
  "description": "<YouTube description, 400-500 chars, keyword-rich first 2 lines, timestamps, links section>",
  "tags": ["<20-30 relevant YouTube tags>"],
  "hashtags": ["#tag1", "#tag2", "#tag3"],
  "chapters_timestamps": "<YouTube chapters format: 0:00 Intro\\n0:45 Chapter1\\n...>",
  "pinned_comment": "<pinned comment text to boost engagement, 150 chars max>",
  "seo_score": <1-100>,
  "keyword_density": {"<keyword>": <count>}
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as SeoResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
