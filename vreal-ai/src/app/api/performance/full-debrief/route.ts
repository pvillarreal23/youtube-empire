export const dynamic = 'force-dynamic';

interface FullDebriefRequest {
  channel_name: string;
  period: string;
  videos: Array<{
    title: string;
    views: number;
    ctr: number;
    avg_view_duration_seconds: number;
    subscribers_gained: number;
    revenue: number;
  }>;
  channel_stats: {
    total_subscribers: number;
    total_views_period: number;
    watch_hours_period: number;
    revenue_period: number;
  };
}

interface FullDebriefResponse {
  executive_summary: string;
  period_grade: 'S' | 'A' | 'B' | 'C' | 'D';
  top_performer: { title: string; reason: string };
  worst_performer: { title: string; reason: string };
  trends: Array<{ metric: string; direction: 'up' | 'down' | 'flat'; change: string; insight: string }>;
  content_strategy_insights: string[];
  revenue_analysis: { cpm_estimate: string; top_revenue_driver: string; optimization: string };
  growth_trajectory: string;
  next_period_priorities: Array<{ priority: number; action: string; expected_impact: string }>;
  channel_health: 'thriving' | 'growing' | 'plateauing' | 'declining';
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
    const body = await request.json() as Partial<FullDebriefRequest>;
    if (!body.channel_name?.trim() || !Array.isArray(body.videos) || body.videos.length === 0) {
      return Response.json({ error: 'Missing required fields: channel_name, videos' }, { status: 400 });
    }

    const prompt = `You are the Analytics Director for @VRealAI. Generate a full channel performance debrief.

CHANNEL: ${body.channel_name}
PERIOD: ${body.period ?? 'Last 30 days'}
CHANNEL STATS: ${JSON.stringify(body.channel_stats ?? {})}
VIDEOS THIS PERIOD: ${JSON.stringify(body.videos)}

Return ONLY valid JSON:
{
  "executive_summary": "<3-4 sentence executive summary of the period>",
  "period_grade": "S|A|B|C|D",
  "top_performer": {"title": "<video title>", "reason": "<why it performed best>"},
  "worst_performer": {"title": "<video title>", "reason": "<why it underperformed and what to fix>"},
  "trends": [
    {"metric": "<metric name>", "direction": "up|down|flat", "change": "<percentage or absolute change>", "insight": "<what this means>"}
  ],
  "content_strategy_insights": ["<insight about what content is working>"],
  "revenue_analysis": {"cpm_estimate": "<estimated CPM>", "top_revenue_driver": "<biggest revenue source>", "optimization": "<how to increase revenue>"},
  "growth_trajectory": "<narrative assessment of growth pace and sustainability>",
  "next_period_priorities": [
    {"priority": 1, "action": "<specific action>", "expected_impact": "<expected outcome>"}
  ],
  "channel_health": "thriving|growing|plateauing|declining"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as FullDebriefResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
