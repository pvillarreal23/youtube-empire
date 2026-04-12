/**
 * /api/visual-director/generate
 *
 * Step 2 of the Zara feedback loop:
 *   Step 1: POST /api/visual-director/brief  → Zara returns prompt + settings for review
 *   Step 2: POST /api/visual-director/generate → Pedro approves, this route sends to Ideogram
 *
 * Body: {
 *   prompt: string;            — from Zara's brief (may be edited by user)
 *   negative_prompt?: string;  — from Zara's brief
 *   visual_type: 'thumbnail' | 'banner' | 'ideogram_still';
 *   aspect_ratio?: string;     — ASPECT_1_1 | ASPECT_16_9 | ASPECT_9_16 (default: ASPECT_16_9)
 *   style_type?: string;       — DESIGN | REALISTIC (default: DESIGN for thumbnails, REALISTIC for stills)
 *   brief_id?: string;         — optional tracking id
 * }
 *
 * Returns: { images: Array<{ url: string }>, brief_id?: string, model: string }
 */

export const dynamic = 'force-dynamic';

interface GenerateRequest {
  prompt: string;
  negative_prompt?: string;
  visual_type: 'thumbnail' | 'banner' | 'ideogram_still';
  aspect_ratio?: string;
  style_type?: string;
  brief_id?: string;
}

const ASPECT_MAP: Record<string, string> = {
  thumbnail:     'ASPECT_16_9',
  banner:        'ASPECT_16_9',
  ideogram_still: 'ASPECT_1_1',
};

const STYLE_MAP: Record<string, string> = {
  thumbnail:     'DESIGN',
  banner:        'DESIGN',
  ideogram_still: 'REALISTIC',
};

export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<GenerateRequest>;

    if (!body.prompt?.trim()) {
      return Response.json({ error: 'Missing required field: prompt' }, { status: 400 });
    }

    const visual_type = (body.visual_type ?? 'thumbnail') as GenerateRequest['visual_type'];
    const aspect_ratio = body.aspect_ratio ?? ASPECT_MAP[visual_type] ?? 'ASPECT_16_9';
    const style_type   = body.style_type   ?? STYLE_MAP[visual_type]  ?? 'DESIGN';

    const ideogramKey = process.env.IDEOGRAM_API_KEY;
    if (!ideogramKey) {
      return Response.json({ error: 'IDEOGRAM_API_KEY not configured' }, { status: 500 });
    }

    const payload = {
      image_request: {
        prompt:               body.prompt,
        negative_prompt:      body.negative_prompt ?? '',
        model:                'V_2_TURBO',
        aspect_ratio,
        magic_prompt_option:  'OFF',
        style_type,
        num_images:           4,
      },
    };

    const res = await fetch('https://api.ideogram.ai/generate', {
      method:  'POST',
      headers: {
        'Api-Key':      ideogramKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.text();
      return Response.json({ error: `Ideogram API error ${res.status}: ${err}` }, { status: 502 });
    }

    const data = await res.json() as { data: Array<{ url: string; is_image_safe: boolean }> };

    return Response.json({
      images:   data.data ?? [],
      brief_id: body.brief_id,
      model:    'V_2_TURBO',
      settings: { aspect_ratio, style_type, visual_type },
    });
  } catch (e) {
    return Response.json({ error: String(e) }, { status: 500 });
  }
}

/**
 * GET /api/visual-director/generate — returns the feedback loop flow spec
 * Useful for the dashboard to render the Zara propose → approve → generate UI
 */
export async function GET() {
  return Response.json({
    flow: [
      {
        step: 1,
        route:   'POST /api/visual-director/brief',
        label:   'Zara proposes',
        description: 'Send topic + scene_description + visual_type + mood. Zara returns a full prompt, settings, shot notes.',
        editable: true,
      },
      {
        step: 2,
        route:   'POST /api/visual-director/generate',
        label:   'You approve & generate',
        description: "Review Zara's prompt. Edit if needed. Send to this endpoint. Returns 4 image options from Ideogram.",
        editable: false,
      },
    ],
    status: 'ready',
    note: 'magic_prompt_option is always OFF — Zara writes precise prompts that must not be rewritten by Ideogram.',
  });
}
