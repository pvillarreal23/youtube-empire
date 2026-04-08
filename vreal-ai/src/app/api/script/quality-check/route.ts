export const dynamic = 'force-dynamic';

// ── Types ─────────────────────────────────────────────────────────────────────

interface ScriptSection {
  name: string;
  timestamp: string;
  word_count: number;
  content: string;
}

interface ScriptInput {
  title?: string;
  hook_line?: string;
  sections?: ScriptSection[];
  total_word_count?: number;
  estimated_duration?: string;
  pedro_take?: string;
}

interface CheckResult {
  status: 'PASS' | 'FAIL';
  reason: string;
}

interface WordCountCheck extends CheckResult {
  actual_count: number;
}

interface ForbiddenPhrasesCheck extends CheckResult {
  found: string[];
}

interface VisualTagsCheck extends CheckResult {
  count: number;
}

interface SentenceLengthCheck extends CheckResult {
  flagged: string[];
}

interface QualityChecks {
  hook_strength: CheckResult;
  personality_present: CheckResult;
  word_count: WordCountCheck;
  forbidden_phrases: ForbiddenPhrasesCheck;
  visual_tags: VisualTagsCheck;
  sentence_length: SentenceLengthCheck;
}

interface QualityCheckResponse {
  overall: 'PASS' | 'FAIL';
  score: number;
  checks: QualityChecks;
  rewrite_instructions: string;
  approved: boolean;
}

// ── Forbidden phrases ─────────────────────────────────────────────────────────

const FORBIDDEN_PHRASES = [
  "In today's video",
  "Don't forget to subscribe",
  "Without further ado",
  "Let's dive in",
  "at the end of the day",
];

// ── Programmatic checks ───────────────────────────────────────────────────────

function checkWordCount(script: ScriptInput): WordCountCheck {
  const count = script.total_word_count ?? 0;
  const inRange = count >= 750 && count <= 900;
  return {
    status: inRange ? 'PASS' : 'FAIL',
    actual_count: count,
    reason: inRange
      ? `Word count ${count} is within the 750–900 range.`
      : `Word count ${count} is ${count < 750 ? 'below the 750 minimum' : 'above the 900 maximum'}.`,
  };
}

function checkForbiddenPhrases(script: ScriptInput): ForbiddenPhrasesCheck {
  const allText = [
    script.hook_line ?? '',
    ...(script.sections ?? []).map((s) => s.content),
  ]
    .join(' ')
    .toLowerCase();

  const found = FORBIDDEN_PHRASES.filter((phrase) =>
    allText.includes(phrase.toLowerCase()),
  );

  return {
    status: found.length === 0 ? 'PASS' : 'FAIL',
    found,
    reason:
      found.length === 0
        ? 'No forbidden phrases detected.'
        : `Found ${found.length} forbidden phrase(s): ${found.map((p) => `"${p}"`).join(', ')}.`,
  };
}

function checkVisualTags(script: ScriptInput): VisualTagsCheck {
  const allText = (script.sections ?? []).map((s) => s.content).join(' ');
  const matches = allText.match(/\[VISUAL:/gi) ?? [];
  const count = matches.length;
  const passing = count >= 8;

  return {
    status: passing ? 'PASS' : 'FAIL',
    count,
    reason: passing
      ? `Found ${count} [VISUAL:] tags — meets the minimum of 8.`
      : `Only ${count} [VISUAL:] tag(s) found — need at least 8.`,
  };
}

function checkSentenceLength(script: ScriptInput): SentenceLengthCheck {
  const allText = [
    script.hook_line ?? '',
    ...(script.sections ?? []).map((s) => s.content),
  ].join(' ');

  // Split on sentence-ending punctuation; skip [VISUAL:...] and [PAUSE] tags
  const withoutTags = allText.replace(/\[[^\]]*\]/g, '');
  const sentences = withoutTags
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  const flagged = sentences.filter((s) => {
    const wordCount = s.split(/\s+/).filter(Boolean).length;
    return wordCount > 20;
  });

  return {
    status: flagged.length === 0 ? 'PASS' : 'FAIL',
    flagged,
    reason:
      flagged.length === 0
        ? 'No sentences exceed 20 words.'
        : `${flagged.length} sentence(s) exceed 20 words.`,
  };
}

// ── AI-based checks (hook strength + personality) ─────────────────────────────

interface AIChecksResult {
  hook_strength: CheckResult;
  personality_present: CheckResult;
}

async function runAIChecks(script: ScriptInput): Promise<AIChecksResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY not configured');

  const hookSection = script.sections?.find((s) => s.name === 'HOOK');
  const yourTakeSection = script.sections?.find((s) => s.name === 'YOUR TAKE');

  const prompt = `You are a quality reviewer for @VRealAI, Pedro's faceless AI YouTube channel. Evaluate the following script components strictly.

HOOK LINE: "${script.hook_line ?? ''}"
HOOK SECTION: "${hookSection?.content ?? ''}"
YOUR TAKE SECTION: "${yourTakeSection?.content ?? ''}"
PEDRO_TAKE: "${script.pedro_take ?? ''}"

Evaluate two things:

1. HOOK STRENGTH: Does the first line (hook_line) create IMMEDIATE curiosity? It must grab attention in the first 5 words without using generic openers. It should make the viewer unable to scroll past.
   - PASS: The hook creates genuine curiosity or presents a bold/surprising claim
   - FAIL: The hook is generic, vague, or fails to grab attention immediately

2. PERSONALITY PRESENT: Does the YOUR TAKE section express a SPECIFIC, DEFENSIBLE opinion that takes a real stance? Pedro's take must be controversial or at least clearly opinionated — NOT "it has pros and cons" or "it depends on your use case."
   - PASS: Clear, specific opinion that someone could disagree with
   - FAIL: Wishy-washy, both-sides, or no clear stance

Return ONLY valid JSON (no markdown):
{
  "hook_strength": { "status": "PASS" | "FAIL", "reason": "<one sentence explaining why>" },
  "personality_present": { "status": "PASS" | "FAIL", "reason": "<one sentence explaining why>" }
}`;

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json',
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 512,
      messages: [{ role: 'user', content: prompt }],
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${err}`);
  }

  const data = await res.json() as { content: Array<{ type: string; text: string }> };
  const raw = data.content.find((b) => b.type === 'text')?.text ?? '';
  const cleaned = raw.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/i, '').trim();

  return JSON.parse(cleaned) as AIChecksResult;
}

// ── Score + rewrite instructions ──────────────────────────────────────────────

function computeScore(checks: QualityChecks): number {
  // Each check is worth a weighted number of points
  const weights: Record<keyof QualityChecks, number> = {
    hook_strength: 20,
    personality_present: 20,
    word_count: 15,
    forbidden_phrases: 20,
    visual_tags: 15,
    sentence_length: 10,
  };

  let score = 0;
  for (const key of Object.keys(weights) as Array<keyof QualityChecks>) {
    if (checks[key].status === 'PASS') {
      score += weights[key];
    }
  }
  return score;
}

function buildRewriteInstructions(checks: QualityChecks): string {
  const failures: string[] = [];

  if (checks.hook_strength.status === 'FAIL') {
    failures.push(`HOOK: Rewrite the hook_line and HOOK section. ${checks.hook_strength.reason} The first 5 words must create immediate curiosity — bold claim or surprising fact.`);
  }
  if (checks.personality_present.status === 'FAIL') {
    failures.push(`YOUR TAKE: Rewrite the YOUR TAKE section with a specific, defensible opinion. ${checks.personality_present.reason} Take a real stance — controversial if warranted.`);
  }
  if (checks.word_count.status === 'FAIL') {
    const wc = checks.word_count as WordCountCheck;
    const direction = wc.actual_count < 750 ? 'expand' : 'cut';
    failures.push(`WORD COUNT: Script is ${wc.actual_count} words. ${direction.charAt(0).toUpperCase() + direction.slice(1)} content to hit 750–900 words. ${direction === 'expand' ? 'Add more specifics in THE MEAT section.' : 'Trim fluff in THE MEAT section.'}`);
  }
  if (checks.forbidden_phrases.status === 'FAIL') {
    const fp = checks.forbidden_phrases as ForbiddenPhrasesCheck;
    failures.push(`FORBIDDEN PHRASES: Remove these phrases entirely — they kill the voice: ${fp.found.map((p) => `"${p}"`).join(', ')}.`);
  }
  if (checks.visual_tags.status === 'FAIL') {
    const vt = checks.visual_tags as VisualTagsCheck;
    failures.push(`VISUAL TAGS: Only ${vt.count} [VISUAL:] tags found. Add at least ${8 - vt.count} more [VISUAL: description] tags throughout all sections — especially in THE MEAT.`);
  }
  if (checks.sentence_length.status === 'FAIL') {
    const sl = checks.sentence_length as SentenceLengthCheck;
    failures.push(`SENTENCE LENGTH: Break up these sentences that exceed 20 words:\n${sl.flagged.slice(0, 5).map((s) => `  - "${s.substring(0, 80)}..."`).join('\n')}`);
  }

  return failures.join('\n\n');
}

// ── Route handler ──────────────────────────────────────────────────────────────

export async function POST(request: Request) {
  try {
    const body = await request.json() as { script?: ScriptInput };

    if (!body.script || typeof body.script !== 'object') {
      return Response.json(
        { error: 'Missing required field: script (object)' },
        { status: 400 },
      );
    }

    const script = body.script;

    // Run deterministic checks in parallel with AI checks
    const [aiChecks, wordCountResult, forbiddenPhrasesResult, visualTagsResult, sentenceLengthResult] =
      await Promise.all([
        runAIChecks(script),
        Promise.resolve(checkWordCount(script)),
        Promise.resolve(checkForbiddenPhrases(script)),
        Promise.resolve(checkVisualTags(script)),
        Promise.resolve(checkSentenceLength(script)),
      ]);

    const checks: QualityChecks = {
      hook_strength: aiChecks.hook_strength,
      personality_present: aiChecks.personality_present,
      word_count: wordCountResult,
      forbidden_phrases: forbiddenPhrasesResult,
      visual_tags: visualTagsResult,
      sentence_length: sentenceLengthResult,
    };

    const score = computeScore(checks);
    const overall: 'PASS' | 'FAIL' = score >= 80 ? 'PASS' : 'FAIL';
    const rewriteInstructions = overall === 'FAIL' ? buildRewriteInstructions(checks) : '';

    const response: QualityCheckResponse = {
      overall,
      score,
      checks,
      rewrite_instructions: rewriteInstructions,
      approved: overall === 'PASS',
    };

    return Response.json(response);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json(
      { error: message.includes('JSON') ? 'Failed to parse AI response as JSON — retry' : message },
      { status: 500 },
    );
  }
}
