export const dynamic = 'force-dynamic';

interface NewsletterRequest {
  video_title: string;
  topic: string;
  tool_name: string;
  hook: string;
  key_insight: string;
  chapters: Array<{ title: string; content: string }>;
  subscriber_count: number;
}

interface NewsletterResponse {
  subject_line: string;
  preview_text: string;
  body: string;
  cta_button_text: string;
  cta_url_placeholder: string;
  estimated_open_rate: string;
  send_timing: string;
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
    const body = await request.json() as Partial<NewsletterRequest>;
    if (!body.video_title?.trim() || !body.topic?.trim()) {
      return Response.json({ error: 'Missing required fields: video_title, topic' }, { status: 400 });
    }

    const prompt = `You are the Email Marketing Lead for @VRealAI. Write the newsletter for this new video release. When the video topic involves AI video generation tools, include the Kling AI referral (code: 7B4U73LULN88, url: https://klingai.com/?ref=7B4U73LULN88) in the This Week's Tool section of the email.

VIDEO TITLE: ${body.video_title}
TOPIC: ${body.topic}
TOOL: ${body.tool_name}
KEY INSIGHT: ${body.key_insight}
HOOK: ${body.hook}
CHAPTERS: ${JSON.stringify(body.chapters ?? [])}
SUBSCRIBER COUNT: ${body.subscriber_count ?? 0}

Write in the same voice as the channel: direct, opinionated, no fluff. This email drives YouTube views.

Return ONLY valid JSON:
{
  "subject_line": "<subject, 40-50 chars, creates curiosity>",
  "preview_text": "<preview text, 80-100 chars>",
  "body": "<full email body in plain text, 300-400 words. Start with the hook, tease the key insight, list 2-3 chapter highlights, end with CTA to watch. No HTML tags.>",
  "cta_button_text": "<button text, 3-5 words>",
  "cta_url_placeholder": "[VIDEO_URL]",
  "estimated_open_rate": "<estimated open rate based on subject line quality>",
  "send_timing": "<best time to send, e.g. Tuesday 9am EST>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as NewsletterResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
