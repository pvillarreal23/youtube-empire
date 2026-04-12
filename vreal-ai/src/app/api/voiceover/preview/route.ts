import { NextRequest, NextResponse } from 'next/server';

const LOCKED_VOICE_ID = 'pNInz6obpgDQGcFmaJgB';
const LOCKED_VOICE_SETTINGS = {
  stability: 0.55,
  similarity_boost: 0.80,
  style: 0.20,
  use_speaker_boost: true,
};

function cleanAndTrim(text: string, wordLimit = 100): string {
  const cleaned = text
    .replace(/\[VISUAL:[^\]]*\]/g, '')
    .replace(/\[PAUSE\]/g, '...')
    .replace(/\s+/g, ' ')
    .trim();
  const words = cleaned.split(' ');
  return words.slice(0, wordLimit).join(' ');
}

export async function POST(req: NextRequest) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'ELEVENLABS_API_KEY not configured' }, { status: 500 });
  }

  const body = await req.json();
  const { text, voice_id } = body;

  if (!text) {
    return NextResponse.json({ error: 'text is required' }, { status: 400 });
  }

  const previewText = cleanAndTrim(text, 100);
  const voiceId = voice_id || LOCKED_VOICE_ID;

  const elevenRes = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream`,
    {
      method: 'POST',
      headers: { 'xi-api-key': apiKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        text: previewText,
        model_id: 'eleven_turbo_v2_5',
        voice_settings: LOCKED_VOICE_SETTINGS,
      }),
    }
  );

  if (!elevenRes.ok) {
    const err = await elevenRes.text();
    return NextResponse.json({ error: 'ElevenLabs error', detail: err }, { status: elevenRes.status });
  }

  return new NextResponse(elevenRes.body, {
    headers: { 'Content-Type': 'audio/mpeg', 'Transfer-Encoding': 'chunked', 'X-Voice-Id': voiceId },
  });
}
