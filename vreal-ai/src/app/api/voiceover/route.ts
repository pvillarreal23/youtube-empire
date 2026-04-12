export const dynamic = 'force-dynamic';

import { PRODUCTION_BIBLE } from '@/config/production-bible';

const { voiceId: DEFAULT_VOICE_ID, model, settings: defaultSettings } = PRODUCTION_BIBLE.elevenlabs;
const tutorialSettings = defaultSettings;
const hookSettings = { ...defaultSettings, stability: 0.50, style: 0.15 };

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { text, voiceId = DEFAULT_VOICE_ID, mode = 'tutorial' } = body as { text: string; voiceId?: string; mode?: 'hook' | 'tutorial' };
    if (!text || !text.trim()) return new Response(JSON.stringify({ error: 'Missing text' }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    const apiKey = process.env.ELEVENLABS_API_KEY;
    if (!apiKey) return new Response(JSON.stringify({ error: 'ElevenLabs API key not configured' }), { status: 500, headers: { 'Content-Type': 'application/json' } });
    const voiceSettings = mode === 'hook' ? hookSettings : tutorialSettings;
    const res = await fetch('https://api.elevenlabs.io/v1/text-to-speech/' + voiceId, { method: 'POST', headers: { 'xi-api-key': apiKey, 'Content-Type': 'application/json', Accept: 'audio/mpeg' }, body: JSON.stringify({ text, model_id: model, voice_settings: { ...voiceSettings, use_speaker_boost: true } }) });
    if (!res.ok) return new Response(JSON.stringify({ error: 'ElevenLabs error' }), { status: res.status, headers: { 'Content-Type': 'application/json' } });
    const buf = await res.arrayBuffer();
    return new Response(buf, { status: 200, headers: { 'Content-Type': 'audio/mpeg', 'Content-Disposition': 'attachment; filename="voiceover.mp3"', 'Cache-Control': 'no-store' } });
  } catch (e) {
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : String(e) }), { status: 500, headers: { 'Content-Type': 'application/json' } });
  }
}
