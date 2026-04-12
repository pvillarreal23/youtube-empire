export const dynamic = 'force-dynamic';

interface CaptionsRequest {
  transcript: string;
  video_duration_seconds: number;
  format?: 'srt' | 'vtt' | 'ass';
}

interface CaptionsResponse {
  format: string;
  captions: string;
  word_count: number;
  estimated_accuracy: string;
  optimization_notes: string[];
}

async function callClaude(prompt: string): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'x-api-key': apiKey, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
    body: JSON.stringify({ model: 'claude-sonnet-4-6', max_tokens: 4096, messages: [{ role: 'user', content: prompt }] }),
  });
  if (!res.ok) throw new Error(`Anthropic API error ${res.status}: ${await res.text()}`);
  const data = await res.json() as { content: Array<{ type: string; text: string }> };
  const raw = data.content.find((b) => b.type === 'text')?.text ?? '';
  return raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/i, '').trim();
}

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<CaptionsRequest>;
    if (!body.transcript?.trim()) return Response.json({ error: 'Missing required field: transcript' }, { status: 400 });
    if (!body.video_duration_seconds || body.video_duration_seconds <= 0) {
      return Response.json({ error: 'Missing required field: video_duration_seconds' }, { status: 400 });
    }

    const format = body.format ?? 'srt';
    const wordCount = body.transcript.split(/\s+/).length;
    const wordsPerSecond = wordCount / body.video_duration_seconds;

    const prompt = `You are a professional caption formatter for @VRealAI YouTube channel. Format this TTS transcript into ${format.toUpperCase()} captions.

TRANSCRIPT (${wordCount} words, ~${wordsPerSecond.toFixed(1)} words/sec):
${body.transcript}

VIDEO DURATION: ${body.video_duration_seconds} seconds

Rules:
- Max 42 chars per caption line
- Max 2 lines per caption block
- Aim for 3-5 second display duration per block
- Break at natural speech pauses (em-dashes, ellipses, sentence ends)
- Start timestamps at 00:00:01,000

Return ONLY valid JSON:
{
  "format": "${format}",
  "captions": "<full ${format.toUpperCase()} formatted captions string with proper newlines>",
  "word_count": ${wordCount},
  "estimated_accuracy": "<timing accuracy estimate>",
  "optimization_notes": ["<note about caption quality or timing adjustments needed>"]
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as CaptionsResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
