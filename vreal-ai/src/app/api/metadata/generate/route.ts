/**
 * /api/metadata/generate  — Stage 11: Metadata Package
 *
 * Generates the complete YouTube upload package via Claude:
 * SEO title, full description (hook + body + timestamps + CTAs),
 * tags, chapters, pinned comment, end screen, cards, publish time,
 * and A/B title variants.
 *
 * Body: {
 *   video_title:         string
 *   script:              object  — the structured script from /api/script
 *   target_keyword:      string  — primary SEO keyword
 *   secondary_keywords:  string[]
 *   topic:               string
 * }
 */

export const dynamic = 'force-dynamic';

// ── Types ─────────────────────────────────────────────────────────────────────

interface MetadataRequest {
  video_title: string;
  script: Record<string, unknown>;
  target_keyword: string;
  secondary_keywords: string[];
  topic: string;
}

interface Timestamp {
  time: string;
  label: string;
}

interface Chapter {
  timestamp: string;
  title: string;
}

interface MetadataDescription {
  hook: string;
  body: string;
  timestamps: Timestamp[];
  links_section: string;
  hashtags: string;
  subscribe_cta: string;
}

interface MetadataResponse {
  seo_title: string;
  description: MetadataDescription;
  tags: string[];
  chapters: Chapter[];
  pinned_comment: string;
  end_screen_title: string;
  cards: string[];
  optimal_publish_time: string;
  ab_title_variants: string[];
}

interface AnthropicContent {
  type: string;
  text: string;
}

interface AnthropicResponse {
  content: AnthropicContent[];
}

// ── System prompt ─────────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `You are an expert YouTube SEO strategist for AI content. You write metadata that ranks AND gets clicks. Your titles have the keyword first but still sound human. Your descriptions are rich but natural. Your tags are specific, not broad. You know the YouTube algorithm rewards watch time, so you write first-comment questions that start discussions.

RULES:
- seo_title: keyword must appear in the first 40 characters; total length 50-60 characters; sounds like a human wrote it, not a bot
- description.hook: first 2 lines only (shown before "Show more"); must include the target keyword; must create urgency or curiosity; max 200 characters total
- description.body: 350+ words; natural keyword usage (target keyword 3-4x, secondary keywords once each); structured with clear paragraphs; NO bullet spam
- description.timestamps: derive from the script sections; format "0:00 - Label"
- description.hashtags: 8-12 hashtags; always include #AI #AITools #VRealAI; rest topic-specific
- tags: 8-12 tags; mix of exact-match, phrase-match, and long-tail; NO single-word broad tags like "AI"
- chapters: match the script section timestamps exactly
- pinned_comment: asks an engaging question related to the topic; under 150 characters; no hashtags
- end_screen_title: a related video topic the viewer would watch next
- cards: 2-3 suggestions with timestamps in the format "X:XX - Description"
- optimal_publish_time: always "Tuesday or Thursday, 3pm EST"
- ab_title_variants: 2 alternatives; each must be different angles (curiosity gap, list format, or bold claim)

Output ONLY valid JSON, no markdown fences, no commentary outside the JSON object.`;

// ── User message builder ──────────────────────────────────────────────────────

function buildUserMessage(req: MetadataRequest): string {
  const lines: string[] = [
    `Generate the complete YouTube metadata package for this video:`,
    ``,
    `Video Title: ${req.video_title}`,
    `Topic: ${req.topic}`,
    `Target Keyword: ${req.target_keyword}`,
    `Secondary Keywords: ${req.secondary_keywords.join(', ')}`,
    ``,
    `Script (use this to write accurate descriptions and timestamps):`,
    JSON.stringify(req.script, null, 2),
  ];
  return lines.join('\n');
}

// ── Claude helper ─────────────────────────────────────────────────────────────

async function generateMetadata(req: MetadataRequest): Promise<MetadataResponse> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key':         apiKey,
      'anthropic-version': '2023-06-01',
      'content-type':      'application/json',
    },
    body: JSON.stringify({
      model:      'claude-sonnet-4-6',
      max_tokens: 4096,
      system:     SYSTEM_PROMPT,
      messages:   [{ role: 'user', content: buildUserMessage(req) }],
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${err}`);
  }

  const data = await res.json() as AnthropicResponse;
  const raw = data.content.find((b) => b.type === 'text')?.text ?? '';
  const cleaned = raw
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/\s*```\s*$/i, '')
    .trim();

  return JSON.parse(cleaned) as MetadataResponse;
}

// ── Route handler ─────────────────────────────────────────────────────────────

export async function POST(request: Request): Promise<Response> {
  try {
    const body = await request.json() as Partial<MetadataRequest>;

    // Validate required fields
    if (!body.video_title?.trim()) {
      return Response.json({ error: 'Missing required field: video_title' }, { status: 400 });
    }
    if (!body.target_keyword?.trim()) {
      return Response.json({ error: 'Missing required field: target_keyword' }, { status: 400 });
    }
    if (!body.topic?.trim()) {
      return Response.json({ error: 'Missing required field: topic' }, { status: 400 });
    }
    if (!body.script || typeof body.script !== 'object') {
      return Response.json({ error: 'Missing required field: script (must be an object)' }, { status: 400 });
    }

    const metadata = await generateMetadata({
      video_title:        body.video_title,
      script:             body.script,
      target_keyword:     body.target_keyword,
      secondary_keywords: Array.isArray(body.secondary_keywords) ? body.secondary_keywords : [],
      topic:              body.topic,
    });

    return Response.json(metadata);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json(
      {
        error: message.includes('JSON')
          ? 'Failed to parse Claude response as JSON — retry'
          : message,
      },
      { status: 500 },
    );
  }
}

// ── Spec endpoint ─────────────────────────────────────────────────────────────

export async function GET(): Promise<Response> {
  return Response.json({
    stage:           11,
    name:            'Metadata Package Generator',
    description:     'Generates the complete YouTube upload package via Claude SEO strategist.',
    required_fields: ['video_title', 'script', 'target_keyword', 'topic'],
    optional_fields: ['secondary_keywords'],
    output_fields: [
      'seo_title',
      'description (hook, body, timestamps, links_section, hashtags, subscribe_cta)',
      'tags',
      'chapters',
      'pinned_comment',
      'end_screen_title',
      'cards',
      'optimal_publish_time',
      'ab_title_variants',
    ],
    model: 'claude-sonnet-4-6',
  });
}
