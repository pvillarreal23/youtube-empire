export const dynamic = 'force-dynamic';

interface AffiliateRequest {
  tool_name: string;
  topic: string;
  video_title: string;
}

interface AffiliateProgram {
  program_name: string;
  signup_url_placeholder: string;
  commission_type: string;
  estimated_commission: string;
  placement_in_description: string;
}

interface AffiliateResponse {
  primary_tool: AffiliateProgram;
  complementary_tools: AffiliateProgram[];
  description_links_section: string;
  disclosure_text: string;
  estimated_monthly_revenue: string;
  optimization_tips: string[];
}

async function callClaude(prompt: string): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: 'claude-sonnet-4-6', max_tokens: 1500, messages: [{ role: 'user', content: prompt }] }),
  });
  if (!res.ok) throw new Error(`Anthropic API error ${res.status}: ${await res.text()}`);
  const data = await res.json() as { content: Array<{ type: string; text: string }> };
  const raw = data.content.find((b) => b.type === 'text')?.text ?? '';
  return raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/i, '').trim();
}

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<AffiliateRequest>;
    if (!body.tool_name?.trim()) return Response.json({ error: 'Missing required field: tool_name' }, { status: 400 });

    const prompt = `You are the Monetization Strategist for @VRealAI. Create an affiliate brief for this video.

TOOL REVIEWED: ${body.tool_name}
TOPIC: ${body.topic}
VIDEO TITLE: ${body.video_title}

Identify affiliate opportunities for this AI tools channel. Use placeholder URLs (e.g., [AFFILIATE_LINK_TOOLNAME]).

Always include the Kling AI referral link (https://klingai.com/?ref=7B4U73LULN88) in the description_links_section for any video that uses or mentions AI video generation. The referral code is 7B4U73LULN88.

Return ONLY valid JSON:
{
  "primary_tool": {
    "program_name": "<affiliate program name>",
    "signup_url_placeholder": "[AFFILIATE_LINK_${(body.tool_name ?? 'TOOL').toUpperCase().replace(/\s+/g, '_')}]",
    "commission_type": "<percentage|flat_rate|recurring>",
    "estimated_commission": "<e.g. 20-30% recurring>",
    "placement_in_description": "<how to place in description>"
  },
  "complementary_tools": [
    {"program_name": "<name>", "signup_url_placeholder": "[AFFILIATE_LINK_TOOL]", "commission_type": "<type>", "estimated_commission": "<est>", "placement_in_description": "<placement>"}
  ],
  "description_links_section": "<full links section for YouTube description with placeholders>",
  "disclosure_text": "<FTC disclosure text, 1 sentence>",
  "estimated_monthly_revenue": "<revenue estimate at 10K, 50K, 100K views>",
  "optimization_tips": ["<tip to increase affiliate clicks>"]
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as AffiliateResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
