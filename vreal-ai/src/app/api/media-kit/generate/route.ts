export const dynamic = 'force-dynamic';

interface MediaKitRequest {
  channel_name: string;
  channel_handle: string;
  niche: string;
  subscribers: number;
  avg_views: number;
  total_views: number;
  top_videos: Array<{ title: string; views: number }>;
  target_brand_category?: string;
}

interface MediaKitResponse {
  headline: string;
  channel_description: string;
  audience_demographics: {
    primary_age: string;
    gender_split: string;
    top_countries: string[];
    interests: string[];
    income_level: string;
  };
  key_stats: Array<{ label: string; value: string; context: string }>;
  content_pillars: string[];
  partnership_formats: Array<{ format: string; description: string; ideal_for: string }>;
  past_performance_highlights: string[];
  brand_alignment_statement: string;
  contact_section: string;
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
    const body = await request.json() as Partial<MediaKitRequest>;
    if (!body.channel_name?.trim() || !body.niche?.trim()) {
      return Response.json({ error: 'Missing required fields: channel_name, niche' }, { status: 400 });
    }

    const prompt = `You are the Business Development Lead for @VRealAI. Generate a professional media kit.

CHANNEL: ${body.channel_name} (${body.channel_handle ?? '@VRealAI'})
NICHE: ${body.niche}
SUBSCRIBERS: ${(body.subscribers ?? 0).toLocaleString()}
AVG VIEWS: ${(body.avg_views ?? 0).toLocaleString()}
TOTAL VIEWS: ${(body.total_views ?? 0).toLocaleString()}
TOP VIDEOS: ${JSON.stringify(body.top_videos ?? [])}
TARGET BRANDS: ${body.target_brand_category ?? 'AI tools, SaaS, productivity software'}

Return ONLY valid JSON:
{
  "headline": "<media kit headline, bold and specific>",
  "channel_description": "<2-3 sentence channel description for brands, highlights unique value>",
  "audience_demographics": {
    "primary_age": "<e.g. 25-34 (primary), 18-24 (secondary)>",
    "gender_split": "<e.g. 68% male, 32% female>",
    "top_countries": ["USA", "UK", "Canada"],
    "interests": ["AI tools", "productivity", "SaaS"],
    "income_level": "<e.g. $60K-$120K household income>"
  },
  "key_stats": [
    {"label": "<stat name>", "value": "<stat value>", "context": "<why this matters to brands>"}
  ],
  "content_pillars": ["<content category>"],
  "partnership_formats": [
    {"format": "<format name>", "description": "<what it includes>", "ideal_for": "<type of brand>"}
  ],
  "past_performance_highlights": ["<notable achievement or stat>"],
  "brand_alignment_statement": "<paragraph on why this channel aligns with tech/AI brands>",
  "contact_section": "<contact info template with placeholder email>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as MediaKitResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
