export const dynamic = 'force-dynamic';

interface DistributionRequest {
  video_title: string;
  topic: string;
  tool_name: string;
  hook: string;
  key_insight: string;
  publish_date: string;
}

interface DistributionTask {
  platform: string;
  task: string;
  content: string;
  timing: string;
  priority: 'high' | 'medium' | 'low';
}

interface DistributionPlan {
  publish_checklist: string[];
  pre_publish_tasks: DistributionTask[];
  day_of_tasks: DistributionTask[];
  post_publish_tasks: DistributionTask[];
  community_post: string;
  twitter_thread: string[];
  linkedin_post: string;
  cross_promotion_notes: string;
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
    const body = await request.json() as Partial<DistributionRequest>;
    if (!body.video_title?.trim() || !body.topic?.trim()) {
      return Response.json({ error: 'Missing required fields: video_title, topic' }, { status: 400 });
    }

    const prompt = `You are the Distribution Manager for @VRealAI YouTube channel. Create a complete distribution plan.

VIDEO TITLE: ${body.video_title}
TOPIC: ${body.topic}
TOOL: ${body.tool_name}
KEY INSIGHT: ${body.key_insight}
PUBLISH DATE: ${body.publish_date}
HOOK EXCERPT: ${(body.hook ?? '').slice(0, 200)}

Return ONLY valid JSON:
{
  "publish_checklist": ["<item before hitting publish>"],
  "pre_publish_tasks": [
    {"platform": "<YouTube|Community|Twitter|LinkedIn>", "task": "<task name>", "content": "<content/copy>", "timing": "<e.g. 2 hours before>", "priority": "high|medium|low"}
  ],
  "day_of_tasks": [
    {"platform": "<platform>", "task": "<task>", "content": "<content>", "timing": "<e.g. 1 hour after publish>", "priority": "high|medium|low"}
  ],
  "post_publish_tasks": [
    {"platform": "<platform>", "task": "<task>", "content": "<content>", "timing": "<e.g. 24 hours after>", "priority": "high|medium|low"}
  ],
  "community_post": "<YouTube Community tab post, 500 chars max>",
  "twitter_thread": ["<tweet 1 — hook>", "<tweet 2>", "<tweet 3 — CTA>"],
  "linkedin_post": "<LinkedIn post, professional tone, 1200 chars max>",
  "cross_promotion_notes": "<notes on playlists, end screens, cards to add>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as DistributionPlan;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
