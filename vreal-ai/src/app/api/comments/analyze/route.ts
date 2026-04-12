export const dynamic = 'force-dynamic';

interface CommentsRequest {
  video_id?: string;
  comments: string[];
  video_title: string;
  topic: string;
}

interface CommentInsight {
  category: 'praise' | 'question' | 'critique' | 'topic_request' | 'spam';
  count: number;
  examples: string[];
  action: string;
}

interface CommentsResponse {
  sentiment_score: number;
  total_analyzed: number;
  insights: CommentInsight[];
  top_questions: string[];
  next_video_ideas: string[];
  reply_templates: Array<{ trigger: string; reply: string }>;
  pinned_reply_suggestion: string;
  community_health: 'excellent' | 'good' | 'needs_attention';
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
    const body = await request.json() as Partial<CommentsRequest>;
    if (!Array.isArray(body.comments) || body.comments.length === 0) {
      return Response.json({ error: 'Missing required field: comments (non-empty array)' }, { status: 400 });
    }

    const prompt = `You are the Community Manager for @VRealAI. Analyze these YouTube comments for insights.

VIDEO TITLE: ${body.video_title ?? 'Unknown'}
TOPIC: ${body.topic ?? 'AI tools'}
COMMENTS (${body.comments.length} total):
${body.comments.slice(0, 100).map((c, i) => `${i + 1}. ${c}`).join('\n')}

Return ONLY valid JSON:
{
  "sentiment_score": <-100 to 100>,
  "total_analyzed": ${body.comments.length},
  "insights": [
    {"category": "praise|question|critique|topic_request|spam", "count": <n>, "examples": ["<comment excerpt>"], "action": "<recommended action>"}
  ],
  "top_questions": ["<recurring question from commenters>"],
  "next_video_ideas": ["<video idea suggested by comments>"],
  "reply_templates": [
    {"trigger": "<type of comment to trigger this reply>", "reply": "<reply text, direct and helpful>"}
  ],
  "pinned_reply_suggestion": "<suggested pinned comment reply from creator>",
  "community_health": "excellent|good|needs_attention",
  "summary": "<2-3 sentence community analysis>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as CommentsResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
