export const dynamic = 'force-dynamic';

interface ResearchRequest {
  topic: string;
  tool_name: string;
  key_insight: string;
}

interface ResearchFinding {
  category: 'trend' | 'pain_point' | 'use_case' | 'competitor_gap' | 'audience_insight';
  finding: string;
  relevance: string;
  source_type: string;
}

interface ResearchResponse {
  topic_summary: string;
  search_angle: string;
  top_findings: ResearchFinding[];
  suggested_hook_angles: string[];
  suggested_chapter_expansions: string[];
  trending_keywords: string[];
  audience_questions: string[];
  competitor_weaknesses: string[];
  unique_angle: string;
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
    const body = await request.json() as Partial<ResearchRequest>;
    if (!body.topic?.trim() || !body.tool_name?.trim()) {
      return Response.json({ error: 'Missing required fields: topic, tool_name' }, { status: 400 });
    }

    const prompt = `You are Aria Chen — Research & Intelligence Lead for @VRealAI. Conduct deep research synthesis for this video topic.

TOPIC: ${body.topic}
TOOL: ${body.tool_name}
KEY INSIGHT: ${body.key_insight ?? ''}

Based on your knowledge of AI tools, YouTube trends, and creator audience behavior, synthesize research that will make this video stand out.

Return ONLY valid JSON:
{
  "topic_summary": "<2-3 sentence synthesis of the current state of this topic>",
  "search_angle": "<the specific angle that will rank and resonate>",
  "top_findings": [
    {"category": "trend|pain_point|use_case|competitor_gap|audience_insight", "finding": "<finding>", "relevance": "<why this matters for the video>", "source_type": "industry_trend|community_feedback|tool_update|competitor_analysis"}
  ],
  "suggested_hook_angles": ["<3-5 hook angle ideas based on research>"],
  "suggested_chapter_expansions": ["<3-5 specific chapter topics that will add value>"],
  "trending_keywords": ["<10-15 keywords with search volume potential>"],
  "audience_questions": ["<5-8 questions the target audience is asking right now>"],
  "competitor_weaknesses": ["<3-5 gaps in existing YouTube content on this topic>"],
  "unique_angle": "<the one thing @VRealAI can say that competitors haven't>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as ResearchResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
