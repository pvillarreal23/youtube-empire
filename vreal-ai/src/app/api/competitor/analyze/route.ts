export const dynamic = 'force-dynamic';

interface CompetitorRequest {
  topic: string;
  tool_name: string;
  competitor_channels?: string[];
}

interface CompetitorVideo {
  estimated_title_type: string;
  angle: string;
  weakness: string;
  opportunity: string;
}

interface CompetitorAnalysis {
  landscape_summary: string;
  content_gaps: string[];
  overused_angles: string[];
  underserved_audiences: string[];
  competitor_weaknesses: Array<{ channel_type: string; weakness: string; opportunity: string }>;
  top_performing_formats: string[];
  recommended_differentiation: string;
  estimated_competition_level: 'low' | 'medium' | 'high' | 'saturated';
  winning_title_formulas: string[];
  sample_competitor_videos: CompetitorVideo[];
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
    const body = await request.json() as Partial<CompetitorRequest>;
    if (!body.topic?.trim() || !body.tool_name?.trim()) {
      return Response.json({ error: 'Missing required fields: topic, tool_name' }, { status: 400 });
    }

    const prompt = `You are the Competitive Intelligence Analyst for @VRealAI. Analyze the YouTube competitive landscape for this topic.

TOPIC: ${body.topic}
TOOL: ${body.tool_name}
KNOWN COMPETITOR CHANNELS: ${(body.competitor_channels ?? []).join(', ') || 'General AI tools channels'}

@VRealAI differentiators: faceless, AI voiceover only, opinionated takes, fast-paced tutorials, no face cam, no vlog style.

Return ONLY valid JSON:
{
  "landscape_summary": "<2-3 sentence overview of competition for this topic>",
  "content_gaps": ["<topic area no one is covering well>"],
  "overused_angles": ["<angle that's been done to death>"],
  "underserved_audiences": ["<audience segment not being served>"],
  "competitor_weaknesses": [
    {"channel_type": "<e.g. tutorial channel, review channel>", "weakness": "<what they do poorly>", "opportunity": "<how to capitalize>"}
  ],
  "top_performing_formats": ["<format that gets views in this niche>"],
  "recommended_differentiation": "<the specific angle @VRealAI should take to win>",
  "estimated_competition_level": "low|medium|high|saturated",
  "winning_title_formulas": ["<title formula that performs well in this niche>"],
  "sample_competitor_videos": [
    {"estimated_title_type": "<type>", "angle": "<their angle>", "weakness": "<what's missing>", "opportunity": "<how to do better>"}
  ]
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as CompetitorAnalysis;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
