export const dynamic = 'force-dynamic';

interface PerformanceRequest {
  video_title: string;
  topic: string;
  views: number;
  watch_time_hours: number;
  avg_view_duration_seconds: number;
  ctr: number;
  likes: number;
  comments: number;
  subscribers_gained: number;
  published_at: string;
  days_since_publish: number;
}

interface PerformanceResponse {
  overall_score: number;
  grade: 'S' | 'A' | 'B' | 'C' | 'D';
  ctr_analysis: { rating: string; benchmark: string; recommendation: string };
  retention_analysis: { rating: string; benchmark: string; recommendation: string };
  engagement_analysis: { rating: string; engagement_rate: number; recommendation: string };
  growth_analysis: { subscribers_per_1k_views: number; rating: string };
  top_strengths: string[];
  improvement_areas: string[];
  action_items: Array<{ priority: 'high' | 'medium' | 'low'; action: string }>;
  revenue_estimate: string;
  projection_30d: { views: number; subscribers: number };
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
    const body = await request.json() as Partial<PerformanceRequest>;
    if (!body.video_title?.trim() || body.views === undefined) {
      return Response.json({ error: 'Missing required fields: video_title, views' }, { status: 400 });
    }

    const engagementRate = body.views > 0 ? (((body.likes ?? 0) + (body.comments ?? 0)) / body.views) * 100 : 0;

    const prompt = `You are the Analytics Director for @VRealAI. Analyze this video's performance metrics.

VIDEO: ${body.video_title}
TOPIC: ${body.topic}
METRICS:
- Views: ${body.views} (over ${body.days_since_publish ?? 0} days)
- Watch time: ${body.watch_time_hours ?? 0} hours
- Avg view duration: ${body.avg_view_duration_seconds ?? 0}s
- CTR: ${body.ctr ?? 0}%
- Likes: ${body.likes ?? 0}
- Comments: ${body.comments ?? 0}
- Engagement rate: ${engagementRate.toFixed(2)}%
- Subscribers gained: ${body.subscribers_gained ?? 0}

AI Tools channel benchmarks: CTR 4-8% good, 8%+ excellent; AVD 40-60% good; engagement 2-4% good.

Return ONLY valid JSON:
{
  "overall_score": <0-100>,
  "grade": "S|A|B|C|D",
  "ctr_analysis": {"rating": "poor|below_avg|average|good|excellent", "benchmark": "4-8% for AI tutorials", "recommendation": "<specific fix>"},
  "retention_analysis": {"rating": "poor|below_avg|average|good|excellent", "benchmark": "40-60% AVD for tutorials", "recommendation": "<specific fix>"},
  "engagement_analysis": {"rating": "poor|below_avg|average|good|excellent", "engagement_rate": ${engagementRate.toFixed(2)}, "recommendation": "<specific fix>"},
  "growth_analysis": {"subscribers_per_1k_views": <calc>, "rating": "poor|average|good|excellent"},
  "top_strengths": ["<what's working>"],
  "improvement_areas": ["<what needs work>"],
  "action_items": [{"priority": "high|medium|low", "action": "<specific action to improve performance>"}],
  "revenue_estimate": "<CPM estimate and total revenue at current views>",
  "projection_30d": {"views": <projected 30-day total>, "subscribers": <projected 30-day gained>}
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as PerformanceResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
