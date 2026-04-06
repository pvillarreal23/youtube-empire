import { NextRequest, NextResponse } from 'next/server';

// Pedro V-Real v2 — Instant Voice Clone, uploaded Apr 4 2026
// Source: W 14th St voice memo (3:45, 225s), Whisper-cleaned, AAC 128kbps
const LOCKED_VOICE_ID = 'CjK4w2V6sbgFJY05zTGt';

// Voice settings — to be tuned once new voice clone is approved
const LOCKED_VOICE_SETTINGS = {
  stability: 0.45,
  similarity_boost: 0.80,
  style: 0.30,
  use_speaker_boost: true,
};

function cleanScript(text: string): string {
  return text
    .replace(/\[VISUAL:[^\]]*\]/g, '')  // strip [VISUAL: ...] tags
    .replace(/\[PAUSE\]/g, '...')        // replace [PAUSE] with ellipsis
    .replace(/\s+/g, ' ')               // collapse whitespace
    .trim();
}

export async function POST(req: NextRequest) {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'ELEVENLABS_API_KEY not configured' }, { status: 500 });
  }

  const body = await req.json();
  const { script_text, voice_id, section } = body;

  if (!script_text || typeof script_text !== 'string') {
    return NextResponse.json({ error: 'script_text is required' }, { status: 400 });
  }

  const cleaned = cleanScript(script_text);
  if (cleaned.length === 0) {
    return NextResponse.json({ error: 'script_text is empty after cleaning' }, { status: 400 });
  }

  const voiceId = voice_id || LOCKED_VOICE_ID;

  const elevenRes = await fetch(
    `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}/with-timestamps`,
    {
      method: 'POST',
      headers: {
        'xi-api-key': apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: cleaned,
        model_id: 'eleven_turbo_v2_5',
        voice_settings: LOCKED_VOICE_SETTINGS,
      }),
    }
  );

  if (!elevenRes.ok) {
    const err = await elevenRes.text();
    return NextResponse.json({ error: 'ElevenLabs error', detail: err }, { status: elevenRes.status });
  }

  const data = await elevenRes.json() as {
    audio_base64: string;
    alignment: {
      characters: string[];
      character_start_times_seconds: number[];
      character_end_times_seconds: number[];
    };
  };

  // Parse character-level alignment into word-level timestamps
  const { characters, character_start_times_seconds, character_end_times_seconds } = data.alignment;
  const word_timestamps: Array<{ word: string; start_ms: number; end_ms: number }> = [];

  let currentWord = '';
  let wordStartSec = 0;

  for (let i = 0; i < characters.length; i++) {
    const char = characters[i];
    const startSec = character_start_times_seconds[i];
    const endSec = character_end_times_seconds[i];

    if (char === ' ') {
      if (currentWord) {
        word_timestamps.push({
          word: currentWord,
          start_ms: Math.round(wordStartSec * 1000),
          end_ms: Math.round(endSec * 1000),
        });
        currentWord = '';
      }
    } else {
      if (!currentWord) {
        wordStartSec = startSec;
      }
      currentWord += char;
    }
  }

  // Push final word if exists
  if (currentWord) {
    const lastEndSec = character_end_times_seconds[characters.length - 1];
    word_timestamps.push({
      word: currentWord,
      start_ms: Math.round(wordStartSec * 1000),
      end_ms: Math.round(lastEndSec * 1000),
    });
  }

  return NextResponse.json({
    audio_base64: data.audio_base64,
    word_timestamps,
    character_count: characters.length,
  });
}
