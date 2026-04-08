export const dynamic = 'force-dynamic';

// ── Types ─────────────────────────────────────────────────────────────────────

interface ScriptRequest {
  topic: string;
  tool_name?: string;
  key_insight?: string;
  /** Injected by the quality gate when a rewrite is needed */
  rewrite_instructions?: string;
}

interface ScriptSection {
  name: 'HOOK' | 'CONTEXT' | 'THE MEAT' | 'YOUR TAKE' | 'CTA';
  timestamp: string;
  word_count: number;
  content: string;
}

interface ScriptResponse {
  title: string;
  hook_line: string;
  sections: ScriptSection[];
  total_word_count: number;
  estimated_duration: string;
  pedro_take: string;
}

// ── Personality-locked system prompt ──────────────────────────────────────────

const SYSTEM_PROMPT = `You are the scriptwriter for @VRealAI — Pedro's faceless AI YouTube channel. You write scripts that feel like a knowledgeable friend talking directly to you, not a corporate explainer video.

VOICE:
- Direct and confident. No hedging, no "maybe", no "it depends"
- Conversational but sharp. Like texting a smart friend who knows everything about AI
- First person. "I tested this", "Here's what I found", "This surprised me"
- Short sentences. Maximum 15 words per sentence. If longer, break it.
- Zero filler phrases. Never use: "In today's video", "Don't forget to subscribe", "Without further ado", "Let's dive in", "At the end of the day"

MANDATORY FORMAT — every script MUST follow this exact structure:
1. HOOK (0-30s): Bold claim or surprising fact. First 5 words must grab attention. No intro, no channel name mention.
2. CONTEXT (30s-1:30): Why this matters RIGHT NOW. The problem or opportunity.
3. THE MEAT (1:30-5:00): The actual tutorial/breakdown/comparison. Step by step. Specific. No fluff.
4. YOUR TAKE (5:00-5:45): Pedro's personal opinion. What he actually thinks. Controversial if warranted. This is what separates VRealAI from every other AI channel.
5. CTA (5:45-6:00): One specific action. Not "like and subscribe" — something tied to the topic. "Try this today and drop your result in the comments."

QUALITY RULES:
- Total word count: 750-900 words for a 6-minute video
- Reading level: 8th grade
- Every paragraph max 3 sentences
- Include [VISUAL: description] tags throughout so the editor knows what to show
- Include [PAUSE] for dramatic effect
- The YOUR TAKE section must include a specific, defensible opinion — not "it has pros and cons"

Output format — return ONLY valid JSON, no markdown fences:
{
  "title": "final video title",
  "hook_line": "first spoken line",
  "sections": [
    { "name": "HOOK", "timestamp": "0:00", "word_count": 75, "content": "full text with [VISUAL] tags" },
    { "name": "CONTEXT", "timestamp": "0:30", "word_count": 120, "content": "full text with [VISUAL] tags" },
    { "name": "THE MEAT", "timestamp": "1:30", "word_count": 450, "content": "full text with [VISUAL] tags" },
    { "name": "YOUR TAKE", "timestamp": "5:00", "word_count": 110, "content": "full text with [VISUAL] tags" },
    { "name": "CTA", "timestamp": "5:45", "word_count": 40, "content": "full text" }
  ],
  "total_word_count": 795,
  "estimated_duration": "6:00",
  "pedro_take": "the opinion expressed in YOUR TAKE section"
}`;

// ── Helper: call Claude via Anthropic API ──────────────────────────────────────

async function generateScript(req: ScriptRequest): Promise<ScriptResponse> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');

  const lines: string[] = [`Write a script for this topic: ${req.topic}`];
  if (req.tool_name) lines.push(`Tool featured: ${req.tool_name}`);
  if (req.key_insight) lines.push(`Key insight: ${req.key_insight}`);
  if (req.rewrite_instructions) {
    lines.push(`\nREWRITE INSTRUCTIONS (quality gate feedback — fix all of these issues):\n${req.rewrite_instructions}`);
  }

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 4096,
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content: lines.join('\n') }],
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${err}`);
  }

  const data = await res.json() as { content: Array<{ type: string; text: string }> };
  const raw = data.content.find((b) => b.type === 'text')?.text ?? '';
  const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/i, '').trim();

  return JSON.parse(cleaned) as ScriptResponse;
}

// ── Route handler ──────────────────────────────────────────────────────────────

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<ScriptRequest>;

    if (!body.topic?.trim()) {
      return Response.json(
        { error: 'Missing required field: topic' },
        { status: 400 },
      );
    }

    const script = await generateScript({
      topic: body.topic,
      tool_name: body.tool_name,
      key_insight: body.key_insight,
      rewrite_instructions: body.rewrite_instructions,
    });

    return Response.json(script);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json(
      { error: message.includes('JSON') ? 'Failed to parse AI response as JSON — retry' : message },
      { status: 500 },
    );
  }
}
