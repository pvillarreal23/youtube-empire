import { NextResponse } from 'next/server';

export async function GET() {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: 'ELEVENLABS_API_KEY not configured' }, { status: 500 });
  }

  const res = await fetch('https://api.elevenlabs.io/v1/voices', {
    headers: { 'xi-api-key': apiKey },
  });

  if (!res.ok) {
    return NextResponse.json({ error: 'Failed to fetch voices' }, { status: res.status });
  }

  const data = await res.json();

  // Filter for English voices only, sort by category
  const voices = (data.voices || [])
    .filter((v: { labels?: { language?: string; accent?: string } }) => {
      const lang = v.labels?.language || '';
      const accent = v.labels?.accent || '';
      return lang === '' || lang.toLowerCase().includes('en') || accent.toLowerCase().includes('american') || accent.toLowerCase().includes('british');
    })
    .map((v: { voice_id: string; name: string; category: string; labels?: Record<string, string>; preview_url: string }) => ({
      voice_id: v.voice_id,
      name: v.name,
      category: v.category,
      labels: v.labels || {},
      preview_url: v.preview_url,
    }));

  return NextResponse.json({ voices, total: voices.length });
}
