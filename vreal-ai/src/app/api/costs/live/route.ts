export const dynamic = 'force-dynamic';

import { NextResponse } from 'next/server';

export async function GET() {
  const apiKey = process.env.ELEVENLABS_API_KEY;

  let elevenlabs = null;
  if (apiKey) {
    try {
      const res = await fetch('https://api.elevenlabs.io/v1/user/subscription', {
        headers: { 'xi-api-key': apiKey },
        cache: 'no-store',
      });
      if (res.ok) {
        const data = await res.json();
        const used = data.character_count ?? 0;
        const limit = data.character_limit ?? 100409;
        const resetDate = data.next_character_count_reset_unix
          ? new Date(data.next_character_count_reset_unix * 1000).toISOString()
          : null;
        elevenlabs = {
          used,
          limit,
          percent: limit > 0 ? Math.round((used / limit) * 100) : 0,
          resetDate,
        };
      }
    } catch {
      // return null for this service
    }
  }

  return NextResponse.json({
    elevenlabs,
    timestamp: new Date().toISOString(),
  });
}
