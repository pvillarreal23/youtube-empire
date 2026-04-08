/**
 * /api/thumbnail/generate  — Stage 10: Thumbnail Generator
 *
 * Generates 2 YouTube thumbnail variants via Ideogram for a given video.
 * Thumbnail style is LOCKED across all VRealAI videos for brand consistency.
 *
 * Body: {
 *   video_title:      string  — used in the prompt and returned as overlay text source
 *   topic:            string  — subject matter / context
 *   thumbnail_text:   string  — bold text to overlay client-side (not baked in)
 *   thumbnail_visual: string  — visual scene description from the visual brief
 * }
 *
 * Returns: {
 *   thumbnails: Array<{ url: string; variant: number }>,
 *   thumbnail_text: string,
 *   recommended_variant: number
 * }
 */

export const dynamic = 'force-dynamic';

// ── Types ─────────────────────────────────────────────────────────────────────

interface ThumbnailRequest {
  video_title: string;
  topic: string;
  thumbnail_text: string;
  thumbnail_visual: string;
}

interface IdeogramImage {
  url: string;
  is_image_safe: boolean;
}

interface IdeogramResponse {
  data: IdeogramImage[];
}

interface ThumbnailVariant {
  url: string;
  variant: number;
}

interface ThumbnailGenerateResponse {
  thumbnails: ThumbnailVariant[];
  thumbnail_text: string;
  recommended_variant: number;
}

// ── Locked thumbnail spec ─────────────────────────────────────────────────────

const THUMBNAIL_ASPECT_RATIO = 'ASPECT_16_9';  // 1280×720
const THUMBNAIL_STYLE        = 'DESIGN';
const THUMBNAIL_MODEL        = 'V_2_TURBO';
const THUMBNAIL_NEGATIVE     = 'blurry, low quality, text errors, crowded';

/**
 * Builds the locked Ideogram prompt from the incoming request.
 * The structure is fixed; only the topic-specific scene description changes.
 */
function buildPrompt(videoTitle: string, thumbnailVisual: string): string {
  return (
    `YouTube thumbnail for '${videoTitle}': ${thumbnailVisual}. ` +
    'Dark moody background, space for bold text overlay on left side, ' +
    'high contrast lighting, cinematic quality, AI/tech aesthetic, professional. ' +
    'Style: modern tech YouTube channel.'
  );
}

// ── Ideogram helper ───────────────────────────────────────────────────────────

async function generateVariant(
  apiKey: string,
  prompt: string,
): Promise<string> {
  const payload = {
    image_request: {
      prompt,
      negative_prompt:     THUMBNAIL_NEGATIVE,
      model:               THUMBNAIL_MODEL,
      aspect_ratio:        THUMBNAIL_ASPECT_RATIO,
      magic_prompt_option: 'OFF',
      style_type:          THUMBNAIL_STYLE,
      num_images:          1,
    },
  };

  const res = await fetch('https://api.ideogram.ai/generate', {
    method: 'POST',
    headers: {
      'Api-Key':      apiKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Ideogram API error ${res.status}: ${err}`);
  }

  const data = await res.json() as IdeogramResponse;
  const url = data.data?.[0]?.url;
  if (!url) throw new Error('Ideogram returned no image URL');
  return url;
}

// ── Route handler ─────────────────────────────────────────────────────────────

export async function POST(request: Request): Promise<Response> {
  try {
    const body = await request.json() as Partial<ThumbnailRequest>;

    // Validate required fields
    if (!body.video_title?.trim()) {
      return Response.json({ error: 'Missing required field: video_title' }, { status: 400 });
    }
    if (!body.thumbnail_visual?.trim()) {
      return Response.json({ error: 'Missing required field: thumbnail_visual' }, { status: 400 });
    }
    if (!body.thumbnail_text?.trim()) {
      return Response.json({ error: 'Missing required field: thumbnail_text' }, { status: 400 });
    }

    const apiKey = process.env.IDEOGRAM_API_KEY;
    if (!apiKey) {
      return Response.json({ error: 'IDEOGRAM_API_KEY not configured' }, { status: 500 });
    }

    const prompt = buildPrompt(body.video_title, body.thumbnail_visual);

    // Generate 2 variants in parallel — same prompt, independent seeds
    const [url1, url2] = await Promise.all([
      generateVariant(apiKey, prompt),
      generateVariant(apiKey, prompt),
    ]);

    const response: ThumbnailGenerateResponse = {
      thumbnails: [
        { url: url1, variant: 1 },
        { url: url2, variant: 2 },
      ],
      thumbnail_text:      body.thumbnail_text,
      recommended_variant: 1,
    };

    return Response.json(response);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message }, { status: 500 });
  }
}

// ── Spec endpoint ─────────────────────────────────────────────────────────────

export async function GET(): Promise<Response> {
  return Response.json({
    stage:       10,
    name:        'Thumbnail Generator',
    description: 'Generates 2 YouTube thumbnail variants via Ideogram. Style is LOCKED for brand consistency.',
    locked_spec: {
      aspect_ratio:        THUMBNAIL_ASPECT_RATIO,
      style:               THUMBNAIL_STYLE,
      model:               THUMBNAIL_MODEL,
      negative_prompt:     THUMBNAIL_NEGATIVE,
      variants:            2,
      magic_prompt:        'OFF',
      text_overlay:        'client-side (not baked into image)',
    },
    required_fields: ['video_title', 'topic', 'thumbnail_text', 'thumbnail_visual'],
  });
}
