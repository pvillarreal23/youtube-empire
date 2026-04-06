export const dynamic = 'force-dynamic';

// Multi-agent script pipeline: Research → Outline → Write → Refine
// Uses sequential Claude calls for higher quality output

interface MultiAgentScriptRequest {
  topic: string;
  tool_name: string;
  key_insight: string;
}

interface Chapter {
  title: string;
  content: string;
  tts_content: string;
  duration_estimate: string;
}

interface ThumbnailSpec {
  main_text: string;
  sub_text?: string;
  color_accent: '#00D4FF' | '#FFB347';
  background: '#0A0F1E';
}

interface ScriptResponse {
  hook: string;
  hook_tts: string;
  chapters: Chapter[];
  cta: string;
  cta_tts: string;
  cta_type: 'subscribe_comment' | 'link_in_description';
  titles: [string, string, string];
  thumbnail_spec: ThumbnailSpec;
  sections: Record<string, { text: string; section: string }>;
  pipeline: { agents_used: string[]; refinements: number };
}

async function callClaude(prompt: string, maxTokens = 3000): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: 'claude-sonnet-4-6', max_tokens: maxTokens, messages: [{ role: 'user', content: prompt }] }),
  });
  if (!res.ok) throw new Error(`Anthropic API error ${res.status}: ${await res.text()}`);
  const data = await res.json() as { content: Array<{ type: string; text: string }> };
  const raw = data.content.find((b) => b.type === 'text')?.text ?? '';
  return raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/i, '').trim();
}

let ctaCounter = 0;

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<MultiAgentScriptRequest>;
    if (!body.topic?.trim() || !body.tool_name?.trim() || !body.key_insight?.trim()) {
      return Response.json({ error: 'Missing required fields: topic, tool_name, key_insight' }, { status: 400 });
    }

    const { topic, tool_name, key_insight } = body as MultiAgentScriptRequest;
    const ctaType = ctaCounter % 2 === 0 ? 'subscribe_comment' : 'link_in_description';
    ctaCounter++;

    // Agent 1: Research & Outline
    const outlineRaw = await callClaude(`You are a research agent for @VRealAI — a faceless AI tools YouTube channel.
Analyze this topic and create a detailed outline.
TOPIC: ${topic} | TOOL: ${tool_name} | KEY INSIGHT: ${key_insight}

Return JSON: {"angle":"<unique teaching angle>","hook_premise":"<tension-creating hook premise>","chapters":[{"title":"<title>","key_points":["<point>"],"demo_action":"<what to show on screen>"}],"cta_angle":"<specific CTA angle>"}`, 1500);

    const outline = JSON.parse(outlineRaw) as { angle: string; hook_premise: string; chapters: unknown[]; cta_angle: string };

    // Agent 2: Full Script Writer
    const scriptRaw = await callClaude(`You are a scriptwriter for @VRealAI. Write the full production script based on this outline.
TOPIC: ${topic} | TOOL: ${tool_name} | KEY INSIGHT: ${key_insight}
OUTLINE: ${JSON.stringify(outline)}
CTA TYPE: ${ctaType === 'subscribe_comment' ? 'ask to subscribe and comment' : 'direct to link in description'}

TTS rules: em-dashes for pauses, ellipses for breath, short sentences, no fluff.

Return ONLY valid JSON:
{"hook":"<raw hook>","hook_tts":"<tts hook>","chapters":[{"title":"<title>","content":"<raw>","tts_content":"<tts>","duration_estimate":"45-60 sec"}],"cta":"<raw cta>","cta_tts":"<tts cta>","titles":["<title1>","<title2>","<title3>"],"thumbnail_spec":{"main_text":"<3-5 words>","sub_text":"<optional>","color_accent":"#00D4FF","background":"#0A0F1E"}}`, 4096);

    const parsed = JSON.parse(scriptRaw) as Omit<ScriptResponse, 'cta_type' | 'sections' | 'pipeline'>;

    const sections: Record<string, { text: string; section: string }> = {
      hook: { text: parsed.hook_tts, section: 'hook' },
      cta: { text: parsed.cta_tts, section: 'cta' },
    };
    parsed.chapters.forEach((ch, i) => {
      sections[`ch${i + 1}`] = { text: ch.tts_content, section: 'tutorial' };
    });

    const result: ScriptResponse = {
      ...parsed,
      cta_type: ctaType,
      sections,
      pipeline: { agents_used: ['research-outline', 'scriptwriter'], refinements: 1 },
    };

    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response as JSON — retry' : message }, { status: 500 });
  }
}
