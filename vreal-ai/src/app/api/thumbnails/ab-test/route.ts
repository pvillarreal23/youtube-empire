export const dynamic = 'force-dynamic';

interface ThumbnailAbTestRequest {
  video_title: string;
  topic: string;
  tool_name: string;
  current_thumbnail?: {
    main_text: string;
    sub_text?: string;
    color_accent: string;
  };
  ctr_current?: number;
}

interface ThumbnailVariant {
  variant_id: string;
  name: string;
  main_text: string;
  sub_text?: string;
  color_accent: string;
  background: string;
  layout_description: string;
  psychological_hook: string;
  expected_ctr_lift: string;
  test_duration_days: number;
}

interface ThumbnailAbTestResponse {
  hypothesis: string;
  variants: ThumbnailVariant[];
  testing_protocol: {
    metric: string;
    minimum_impressions: number;
    confidence_threshold: string;
    winner_criteria: string;
  };
  ideogram_prompts: string[];
  scheduling_recommendation: string;
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
    const body = await request.json() as Partial<ThumbnailAbTestRequest>;
    if (!body.video_title?.trim() || !body.topic?.trim()) {
      return Response.json({ error: 'Missing required fields: video_title, topic' }, { status: 400 });
    }

    const prompt = `You are the Thumbnail Specialist for @VRealAI. Design an A/B test for this video's thumbnail.

VIDEO TITLE: ${body.video_title}
TOPIC: ${body.topic}
TOOL: ${body.tool_name}
CURRENT THUMBNAIL: ${body.current_thumbnail ? JSON.stringify(body.current_thumbnail) : 'None (new video)'}
CURRENT CTR: ${body.ctr_current ? `${body.ctr_current}%` : 'Unknown'}

Brand palette: Navy #0A0F1E background, Cyan #00D4FF accent, Amber #FFB347 accent.
Channel is faceless — no faces in thumbnails, use bold text + screen captures + abstract visuals.

Return ONLY valid JSON:
{
  "hypothesis": "<what we're testing and why>",
  "variants": [
    {
      "variant_id": "A",
      "name": "<variant name>",
      "main_text": "<3-5 words, ALL CAPS>",
      "sub_text": "<optional supporting text>",
      "color_accent": "#00D4FF or #FFB347",
      "background": "#0A0F1E",
      "layout_description": "<describe visual layout: text position, graphic elements>",
      "psychological_hook": "<what psychological trigger this uses: curiosity, fear of missing out, etc>",
      "expected_ctr_lift": "<estimated CTR improvement>",
      "test_duration_days": 7
    }
  ],
  "testing_protocol": {
    "metric": "CTR",
    "minimum_impressions": 1000,
    "confidence_threshold": "95%",
    "winner_criteria": "<when to declare a winner>"
  },
  "ideogram_prompts": ["<Ideogram AI prompt for each variant thumbnail>"],
  "scheduling_recommendation": "<when to run the test for best results>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as ThumbnailAbTestResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
