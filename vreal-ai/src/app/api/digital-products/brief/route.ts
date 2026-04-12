export const dynamic = 'force-dynamic';

interface DigitalProductRequest {
  topic: string;
  tool_name: string;
  video_title: string;
  audience_size?: number;
}

interface DigitalProduct {
  product_type: 'course' | 'template' | 'ebook' | 'prompt_pack' | 'notion_template' | 'checklist';
  title: string;
  description: string;
  price_point: string;
  delivery_format: string;
  estimated_creation_time: string;
  sales_potential: string;
  gumroad_description: string;
}

interface DigitalProductsResponse {
  recommended_products: DigitalProduct[];
  launch_sequence: string[];
  pricing_strategy: string;
  community_offer: string;
  upsell_path: string;
  estimated_monthly_revenue: string;
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
    const body = await request.json() as Partial<DigitalProductRequest>;
    if (!body.topic?.trim() || !body.tool_name?.trim()) {
      return Response.json({ error: 'Missing required fields: topic, tool_name' }, { status: 400 });
    }

    const prompt = `You are the Product Lead for @VRealAI. Create a digital products brief based on this video's topic.

VIDEO TITLE: ${body.video_title}
TOPIC: ${body.topic}
TOOL COVERED: ${body.tool_name}
AUDIENCE SIZE: ${body.audience_size ? body.audience_size.toLocaleString() + ' subscribers' : 'Growing'}

Create digital products that complement this video content and monetize the audience.

Return ONLY valid JSON:
{
  "recommended_products": [
    {
      "product_type": "course|template|ebook|prompt_pack|notion_template|checklist",
      "title": "<product title>",
      "description": "<2-3 sentence product description>",
      "price_point": "<e.g. $27, $97, $197>",
      "delivery_format": "<PDF|Notion|video course|zip file>",
      "estimated_creation_time": "<e.g. 2-3 hours>",
      "sales_potential": "<estimated monthly sales at current audience size>",
      "gumroad_description": "<Gumroad product page description, 200-300 chars>"
    }
  ],
  "launch_sequence": ["<step in launch sequence>"],
  "pricing_strategy": "<pricing rationale and strategy>",
  "community_offer": "<exclusive offer for YouTube members or email subscribers>",
  "upsell_path": "<how products connect: free lead magnet → low ticket → high ticket>",
  "estimated_monthly_revenue": "<projected revenue at current audience size>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as DigitalProductsResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
