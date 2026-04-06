export const dynamic = 'force-dynamic';

interface PlaylistOptimizeRequest {
  channel_name: string;
  existing_videos: Array<{ title: string; topic: string; views: number; tags?: string[] }>;
  channel_niche?: string;
}

interface PlaylistSuggestion {
  playlist_name: string;
  playlist_description: string;
  videos_included: string[];
  suggested_order: string[];
  expected_watch_time_boost: string;
  seo_keywords: string[];
  thumbnail_strategy: string;
}

interface PlaylistOptimizeResponse {
  current_organization_assessment: string;
  recommended_playlists: PlaylistSuggestion[];
  featured_playlist: string;
  channel_sections_order: string[];
  optimization_tips: string[];
  estimated_session_time_improvement: string;
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
    const body = await request.json() as Partial<PlaylistOptimizeRequest>;
    if (!body.channel_name?.trim() || !Array.isArray(body.existing_videos) || body.existing_videos.length === 0) {
      return Response.json({ error: 'Missing required fields: channel_name, existing_videos' }, { status: 400 });
    }

    const prompt = `You are the SEO Strategist for @VRealAI. Optimize the YouTube playlist structure to maximize session time and subscriber conversion.

CHANNEL: ${body.channel_name}
NICHE: ${body.channel_niche ?? 'AI tools tutorials'}
VIDEOS (${body.existing_videos.length} total):
${JSON.stringify(body.existing_videos)}

YouTube playlist strategy: Group by learning journey, not just topic. Think "beginner → intermediate → advanced" or "tool category" groupings.

Return ONLY valid JSON:
{
  "current_organization_assessment": "<assessment of how the current video library is organized and gaps>",
  "recommended_playlists": [
    {
      "playlist_name": "<name>",
      "playlist_description": "<SEO-optimized description for the playlist>",
      "videos_included": ["<video title>"],
      "suggested_order": ["<title in recommended watch order>"],
      "expected_watch_time_boost": "<estimated improvement>",
      "seo_keywords": ["<keyword>"],
      "thumbnail_strategy": "<how to make playlist thumbnail stand out>"
    }
  ],
  "featured_playlist": "<name of playlist to feature on channel homepage>",
  "channel_sections_order": ["<section name in order on channel page>"],
  "optimization_tips": ["<specific tip to improve playlist performance>"],
  "estimated_session_time_improvement": "<expected improvement in average session duration>"
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as PlaylistOptimizeResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
