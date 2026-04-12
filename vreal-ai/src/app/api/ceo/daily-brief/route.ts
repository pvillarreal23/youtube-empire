export const dynamic = 'force-dynamic';

interface DailyBriefRequest {
  date?: string;
  channel_stats: {
    subscribers: number;
    views_today: number;
    revenue_today: number;
    videos_in_queue: number;
  };
  pending_tasks?: string[];
  recent_performance?: Array<{ title: string; views: number; published: string }>;
}

interface DailyBriefResponse {
  date: string;
  executive_summary: string;
  kpi_status: Array<{ metric: string; value: string; status: 'on_track' | 'behind' | 'ahead'; action_needed: boolean }>;
  todays_priorities: Array<{ priority: number; task: string; time_estimate: string; category: string }>;
  decisions_needed: string[];
  opportunities: string[];
  risks: string[];
  weekly_goal_progress: string;
  motivational_note: string;
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
    const body = await request.json() as Partial<DailyBriefRequest>;
    if (!body.channel_stats) {
      return Response.json({ error: 'Missing required field: channel_stats' }, { status: 400 });
    }

    const date = body.date ?? new Date().toISOString().split('T')[0];

    const prompt = `You are the Chief of Staff for @VRealAI — a solo YouTube creator running an AI tools channel. Generate the daily CEO brief.

DATE: ${date}
CHANNEL STATS TODAY:
- Subscribers: ${body.channel_stats.subscribers.toLocaleString()}
- Views today: ${body.channel_stats.views_today.toLocaleString()}
- Revenue today: $${body.channel_stats.revenue_today.toFixed(2)}
- Videos in queue: ${body.channel_stats.videos_in_queue}

PENDING TASKS: ${JSON.stringify(body.pending_tasks ?? [])}
RECENT VIDEOS: ${JSON.stringify(body.recent_performance ?? [])}

Return ONLY valid JSON:
{
  "date": "${date}",
  "executive_summary": "<2-3 sentence daily situation report>",
  "kpi_status": [
    {"metric": "<metric name>", "value": "<current value>", "status": "on_track|behind|ahead", "action_needed": true}
  ],
  "todays_priorities": [
    {"priority": 1, "task": "<specific task>", "time_estimate": "<e.g. 2 hours>", "category": "content|business|growth|ops"}
  ],
  "decisions_needed": ["<decision the creator needs to make today>"],
  "opportunities": ["<opportunity to act on today>"],
  "risks": ["<risk to address>"],
  "weekly_goal_progress": "<progress toward this week's targets>",
  "motivational_note": "<brief, direct motivational note — no fluff>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as DailyBriefResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
