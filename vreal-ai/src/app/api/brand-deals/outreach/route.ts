export const dynamic = 'force-dynamic';

interface BrandDealRequest {
  brand_name: string;
  brand_category: string;
  channel_stats: {
    subscribers: number;
    avg_views: number;
    niche: string;
  };
  deal_type?: 'integration' | 'dedicated' | 'affiliate_upgrade';
  target_rate?: number;
}

interface BrandDealResponse {
  subject_line: string;
  outreach_email: string;
  media_kit_talking_points: string[];
  rate_card: {
    integration_30s: string;
    integration_60s: string;
    dedicated_video: string;
    package_deal: string;
  };
  negotiation_tips: string[];
  contract_checklist: string[];
  red_flags: string[];
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
    const body = await request.json() as Partial<BrandDealRequest>;
    if (!body.brand_name?.trim() || !body.brand_category?.trim()) {
      return Response.json({ error: 'Missing required fields: brand_name, brand_category' }, { status: 400 });
    }

    const stats = body.channel_stats ?? { subscribers: 0, avg_views: 0, niche: 'AI tools' };

    const prompt = `You are the Business Development Lead for @VRealAI. Write a brand deal outreach package.

BRAND: ${body.brand_name} (${body.brand_category})
CHANNEL: @VRealAI — Faceless AI tools tutorials
SUBSCRIBERS: ${stats.subscribers.toLocaleString()}
AVG VIEWS: ${stats.avg_views.toLocaleString()}
NICHE: ${stats.niche}
DEAL TYPE: ${body.deal_type ?? 'integration'}
TARGET RATE: ${body.target_rate ? `$${body.target_rate}` : 'Market rate'}

Return ONLY valid JSON:
{
  "subject_line": "<email subject, professional and direct>",
  "outreach_email": "<full outreach email, 200-300 words, professional tone, includes stats, value prop, and clear ask>",
  "media_kit_talking_points": ["<key stat or fact to include in media kit>"],
  "rate_card": {
    "integration_30s": "<price range>",
    "integration_60s": "<price range>",
    "dedicated_video": "<price range>",
    "package_deal": "<bundle description and price>"
  },
  "negotiation_tips": ["<tip for negotiating with this brand category>"],
  "contract_checklist": ["<item to include in brand deal contract>"],
  "red_flags": ["<warning sign to watch for with this type of brand>"]
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as BrandDealResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
