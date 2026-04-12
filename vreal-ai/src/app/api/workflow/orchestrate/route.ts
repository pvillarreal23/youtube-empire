export const dynamic = 'force-dynamic';

// NOTE: For production this should be a background job (queue-based) because the full
// pipeline can exceed Next.js's 25-second edge timeout. Locally it runs fine as a route.

const BASE_URL = process.env.NEXT_PUBLIC_APP_URL ?? 'http://localhost:3000';

// ── Types ──────────────────────────────────────────────────────────────────────

interface OrchestrateRequest {
  topic: string;
  tool_name: string;
  key_insight: string;
  publish_date?: string;
  run_live_research?: boolean;
  skip_voiceover?: boolean;
  channel_stats?: {
    subscribers: number;
    avg_views: number;
    total_videos: number;
  };
}

interface PipelineMeta {
  stages_completed: string[];
  stages_failed: string[];
  total_duration_ms: number;
  qc_approved: boolean;
  qc_score: number | null;
  recommended_title: string;
  live_research_used: boolean;
  warnings: string[];
}

interface VideoProductionPackage {
  package_id: string;
  topic: string;
  tool_name: string;
  generated_at: string;
  live_research: object | null;
  script: object;
  seo: object;
  qc: object;
  video_editor_brief: object;
  shorts_brief: object;
  thumbnail: object | null;
  affiliate_brief: object;
  newsletter_draft: object;
  distribution_plan: object;
  voiceover: object | null;
  pipeline_meta: PipelineMeta;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

async function callApi(path: string, body: object): Promise<object> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`${path} returned ${res.status}: ${text}`);
  }
  return res.json() as Promise<object>;
}

// ── Marcus Webb — Workflow Orchestrator ────────────────────────────────────────

export async function POST(request: Request) {
  const startTime = Date.now();

  const meta: PipelineMeta = {
    stages_completed: [],
    stages_failed: [],
    total_duration_ms: 0,
    qc_approved: false,
    qc_score: null,
    recommended_title: '',
    live_research_used: false,
    warnings: [],
  };

  try {
    const body = await request.json() as Partial<OrchestrateRequest>;

    if (!body.topic?.trim() || !body.tool_name?.trim() || !body.key_insight?.trim()) {
      return Response.json(
        { error: 'Missing required fields: topic, tool_name, key_insight' },
        { status: 400 }
      );
    }

    const {
      topic,
      tool_name,
      key_insight,
      publish_date,
      run_live_research = true,
      skip_voiceover = false,
      channel_stats,
    } = body as OrchestrateRequest;

    // ── Stage 1: Live Research (optional) ─────────────────────────────────────
    let live_research: object | null = null;
    if (run_live_research !== false) {
      try {
        live_research = await callApi('/api/research/live', { topic, tool_name, key_insight });
        meta.stages_completed.push('live_research');
      } catch (e) {
        meta.stages_failed.push('live_research');
        meta.warnings.push(`live_research skipped: ${e instanceof Error ? e.message : String(e)}`);
      }
    }
    // multi-agent script pipeline handles live research internally
    meta.live_research_used = run_live_research !== false;

    // ── Stage 2: Script (required) ────────────────────────────────────────────
    let script: Record<string, unknown>;
    try {
      script = await callApi('/api/script/multi-agent', { topic, tool_name, key_insight }) as Record<string, unknown>;
      meta.stages_completed.push('script');
    } catch (e) {
      // Fall back to the basic script route if multi-agent isn't available yet
      try {
        script = await callApi('/api/script', { topic, tool_name, key_insight }) as Record<string, unknown>;
        meta.stages_completed.push('script');
        meta.warnings.push('script: used /api/script fallback (multi-agent not available)');
      } catch (e2) {
        meta.stages_failed.push('script');
        meta.total_duration_ms = Date.now() - startTime;
        return Response.json(
          { error: 'Script generation failed — pipeline cannot continue', details: e2 instanceof Error ? e2.message : String(e2) },
          { status: 500 }
        );
      }
    }

    // ── Stage 3: SEO + QC (parallel, both need script) ────────────────────────
    const titles = script.titles as string[] | undefined;
    const hook = script.hook as string | undefined;
    const hook_tts = script.hook_tts as string | undefined;
    const chapters = script.chapters as unknown[] | undefined;
    const cta = script.cta as string | undefined;
    const cta_tts = script.cta_tts as string | undefined;
    const thumbnail_spec = script.thumbnail_spec as object | undefined;
    const cta_type = script.cta_type as string | undefined;
    const sections = script.sections as object | undefined;

    const [seoResult, qcResult] = await Promise.allSettled([
      callApi('/api/seo', { topic, tool_name, titles, hook, chapters }),
      callApi('/api/qc', { hook, hook_tts, chapters, cta, cta_tts, titles, thumbnail_spec, cta_type }),
    ]);

    let seo: Record<string, unknown> = {};
    if (seoResult.status === 'fulfilled') {
      seo = seoResult.value as Record<string, unknown>;
      meta.stages_completed.push('seo');
    } else {
      meta.stages_failed.push('seo');
      meta.warnings.push(`seo: ${seoResult.reason instanceof Error ? seoResult.reason.message : String(seoResult.reason)}`);
    }

    let qc: Record<string, unknown> = {};
    if (qcResult.status === 'fulfilled') {
      qc = qcResult.value as Record<string, unknown>;
      meta.stages_completed.push('qc');
      meta.qc_approved = Boolean(qc.approved);
      meta.qc_score = typeof qc.score === 'number' ? qc.score : null;
    } else {
      meta.stages_failed.push('qc');
      meta.warnings.push(`qc: ${qcResult.reason instanceof Error ? qcResult.reason.message : String(qcResult.reason)}`);
    }

    const recommended_title = (seo.recommended_title as string | undefined) ?? (Array.isArray(titles) ? titles[0] : '') ?? '';
    meta.recommended_title = recommended_title;

    // ── Stage 4: Production assets (parallel) ─────────────────────────────────
    const hasIdeogram = Boolean(process.env.IDEOGRAM_API_KEY);

    const [videoEditorResult, shortsResult, thumbnailResult] = await Promise.allSettled([
      callApi('/api/video-editor/brief', {
        video_title: recommended_title,
        hook_tts,
        chapters,
        cta_tts,
        thumbnail_spec,
      }),
      callApi('/api/shorts/brief', {
        video_title: recommended_title,
        hook_tts,
        chapters,
        cta_tts,
      }),
      hasIdeogram
        ? callApi('/api/thumbnail', { thumbnail_spec, video_title: recommended_title })
        : Promise.reject(new Error('IDEOGRAM_API_KEY not set — thumbnail skipped')),
    ]);

    let video_editor_brief: object = {};
    if (videoEditorResult.status === 'fulfilled') {
      video_editor_brief = videoEditorResult.value;
      meta.stages_completed.push('video_editor_brief');
    } else {
      meta.stages_failed.push('video_editor_brief');
      meta.warnings.push(`video_editor_brief: ${videoEditorResult.reason instanceof Error ? videoEditorResult.reason.message : String(videoEditorResult.reason)}`);
    }

    let shorts_brief: object = {};
    if (shortsResult.status === 'fulfilled') {
      shorts_brief = shortsResult.value;
      meta.stages_completed.push('shorts_brief');
    } else {
      meta.stages_failed.push('shorts_brief');
      meta.warnings.push(`shorts_brief: ${shortsResult.reason instanceof Error ? shortsResult.reason.message : String(shortsResult.reason)}`);
    }

    let thumbnail: object | null = null;
    if (thumbnailResult.status === 'fulfilled') {
      thumbnail = thumbnailResult.value;
      meta.stages_completed.push('thumbnail');
    } else {
      if (hasIdeogram) {
        meta.stages_failed.push('thumbnail');
        meta.warnings.push(`thumbnail: ${thumbnailResult.reason instanceof Error ? thumbnailResult.reason.message : String(thumbnailResult.reason)}`);
      } else {
        meta.warnings.push('thumbnail: skipped (no IDEOGRAM_API_KEY)');
      }
    }

    // ── Stage 5: Distribution (parallel) ──────────────────────────────────────
    const [affiliateResult, newsletterResult, distributionResult] = await Promise.allSettled([
      callApi('/api/affiliate/brief', { tool_name, topic, video_title: recommended_title }),
      callApi('/api/newsletter/draft', {
        video_title: recommended_title,
        topic,
        tool_name,
        hook,
        key_insight,
        chapters,
        subscriber_count: channel_stats?.subscribers ?? 0,
      }),
      callApi('/api/distribution/plan', {
        video_title: recommended_title,
        topic,
        tool_name,
        hook,
        key_insight,
        publish_date: publish_date ?? new Date().toISOString(),
      }),
    ]);

    let affiliate_brief: object = {};
    if (affiliateResult.status === 'fulfilled') {
      affiliate_brief = affiliateResult.value;
      meta.stages_completed.push('affiliate_brief');
    } else {
      meta.stages_failed.push('affiliate_brief');
      meta.warnings.push(`affiliate_brief: ${affiliateResult.reason instanceof Error ? affiliateResult.reason.message : String(affiliateResult.reason)}`);
    }

    let newsletter_draft: object = {};
    if (newsletterResult.status === 'fulfilled') {
      newsletter_draft = newsletterResult.value;
      meta.stages_completed.push('newsletter_draft');
    } else {
      meta.stages_failed.push('newsletter_draft');
      meta.warnings.push(`newsletter_draft: ${newsletterResult.reason instanceof Error ? newsletterResult.reason.message : String(newsletterResult.reason)}`);
    }

    let distribution_plan: object = {};
    if (distributionResult.status === 'fulfilled') {
      distribution_plan = distributionResult.value;
      meta.stages_completed.push('distribution_plan');
    } else {
      meta.stages_failed.push('distribution_plan');
      meta.warnings.push(`distribution_plan: ${distributionResult.reason instanceof Error ? distributionResult.reason.message : String(distributionResult.reason)}`);
    }

    // ── Stage 6: Voiceover (optional, expensive) ──────────────────────────────
    let voiceover: object | null = null;
    if (!skip_voiceover) {
      try {
        voiceover = await callApi('/api/voiceover', { sections });
        meta.stages_completed.push('voiceover');
      } catch (e) {
        meta.stages_failed.push('voiceover');
        meta.warnings.push(`voiceover: ${e instanceof Error ? e.message : String(e)}`);
      }
    } else {
      meta.warnings.push('voiceover: skipped (skip_voiceover=true)');
    }

    // ── Assemble package ───────────────────────────────────────────────────────
    meta.total_duration_ms = Date.now() - startTime;

    const pkg: VideoProductionPackage = {
      package_id: `pkg_${Date.now()}`,
      topic,
      tool_name,
      generated_at: new Date().toISOString(),
      live_research,
      script,
      seo,
      qc,
      video_editor_brief,
      shorts_brief,
      thumbnail,
      affiliate_brief,
      newsletter_draft,
      distribution_plan,
      voiceover,
      pipeline_meta: meta,
    };

    return Response.json(pkg);
  } catch (e) {
    meta.total_duration_ms = Date.now() - startTime;
    return Response.json(
      { error: e instanceof Error ? e.message : String(e), pipeline_meta: meta },
      { status: 500 }
    );
  }
}
