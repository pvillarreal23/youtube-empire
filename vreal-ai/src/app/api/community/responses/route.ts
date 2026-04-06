export const dynamic = 'force-dynamic';

interface CommunityResponsesRequest {
  comments: Array<{ id?: string; text: string; author?: string; likes?: number }>;
  video_title: string;
  creator_voice?: string;
}

interface CommentResponse {
  comment_id?: string;
  original_comment: string;
  suggested_reply: string;
  reply_type: 'answer' | 'acknowledge' | 'redirect' | 'pin_candidate' | 'skip';
  priority: 'high' | 'medium' | 'low';
  reason: string;
}

interface CommunityResponsesResult {
  responses: CommentResponse[];
  reply_count: number;
  skip_count: number;
  pin_recommendation?: CommentResponse;
  engagement_tips: string[];
}

async function callClaude(prompt: string): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: 'claude-sonnet-4-6', max_tokens: 3000, messages: [{ role: 'user', content: prompt }] }),
  });
  if (!res.ok) throw new Error(`Anthropic API error ${res.status}: ${await res.text()}`);
  const data = await res.json() as { content: Array<{ type: string; text: string }> };
  const raw = data.content.find((b) => b.type === 'text')?.text ?? '';
  return raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/i, '').trim();
}

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<CommunityResponsesRequest>;
    if (!Array.isArray(body.comments) || body.comments.length === 0) {
      return Response.json({ error: 'Missing required field: comments (non-empty array)' }, { status: 400 });
    }

    const commentsJson = JSON.stringify(body.comments.slice(0, 30));
    const voice = body.creator_voice ?? 'Direct, helpful, no fluff. Matches the opinionated but approachable tone of an AI tools expert.';

    const prompt = `You are the Community Manager for @VRealAI. Generate replies to these YouTube comments.

VIDEO: ${body.video_title ?? 'Recent video'}
CREATOR VOICE: ${voice}

COMMENTS:
${commentsJson}

For each comment: decide whether to reply, what to say, and priority. Skip spam/irrelevant comments.
High priority: questions with many likes, constructive feedback, potential viral replies.

Return ONLY valid JSON:
{
  "responses": [
    {
      "comment_id": "<id if provided>",
      "original_comment": "<first 100 chars of comment>",
      "suggested_reply": "<reply text, max 200 chars, matches creator voice>",
      "reply_type": "answer|acknowledge|redirect|pin_candidate|skip",
      "priority": "high|medium|low",
      "reason": "<why this reply strategy>"
    }
  ],
  "reply_count": <number of non-skip responses>,
  "skip_count": <number of skipped>,
  "pin_recommendation": <best pin_candidate response or null>,
  "engagement_tips": ["<tip to improve this video's comment engagement>"]
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as CommunityResponsesResult;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
