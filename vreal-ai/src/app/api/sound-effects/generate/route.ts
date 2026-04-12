import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'ELEVENLABS_API_KEY not configured' }, { status: 500 });
  }

  const body = await req.json();
  const { prompt, duration_seconds, prompt_influence } = body;

  if (!prompt || typeof prompt !== 'string') {
    return NextResponse.json({ error: 'prompt is required' }, { status: 400 });
  }

  const elevenRes = await fetch('https://api.elevenlabs.io/v1/sound-generation', {
    method: 'POST',
    headers: {
      'xi-api-key': apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: prompt,
      ...(duration_seconds && { duration_seconds }),
      prompt_influence: prompt_influence ?? 0.3,
    }),
  });

  if (!elevenRes.ok) {
    const err = await elevenRes.text();
    return NextResponse.json({ error: 'ElevenLabs error', detail: err }, { status: elevenRes.status });
  }

  const audioBuffer = await elevenRes.arrayBuffer();
  const audio_base64 = Buffer.from(audioBuffer).toString('base64');

  return NextResponse.json({
    audio_base64,
    content_type: 'audio/mpeg',
  });
}
