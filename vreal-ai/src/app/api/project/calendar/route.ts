export const dynamic = 'force-dynamic';

// ── Seeded 4-week calendar for V-Real AI ────────────────────────────────────
const SEEDED_CALENDAR = {
  period: "Apr 7 – May 4, 2026",
  cadence: "2 videos per week (Tuesday + Thursday, 2PM EST)",
  channel: "@VRealAI",
  events: [
    // Week 1
    { date: "2026-04-07", day_of_week: "Tuesday",   type: "research",  title: "Research: Top 5 Free AI Tools 2025",        description: "Compile tool list, test each, capture UI screenshots for B-roll", time_block: "9am–10am" },
    { date: "2026-04-08", day_of_week: "Wednesday",  type: "record",    title: "Script + VO: Top 5 Free AI Tools",          description: "Generate script via /api/script, record ElevenLabs Daniel VO, prompt Zara for 3 B-roll clips", time_block: "10am–12pm" },
    { date: "2026-04-09", day_of_week: "Thursday",   type: "publish",   title: "PUBLISH EP001 — Top 5 Free AI Tools 2025",  description: "Final edit, Zara thumbnail via Ideogram, upload to YouTube with chapters", time_block: "2pm EST", dependencies: ["EP001 edit complete", "Thumbnail approved"] },
    { date: "2026-04-10", day_of_week: "Friday",     type: "research",  title: "Research: Make.com YouTube Automation",     description: "Map out Make.com scenario flow, document webhook setup, prepare screen recordings", time_block: "9am–10am" },
    { date: "2026-04-12", day_of_week: "Sunday",     type: "record",    title: "Script + VO: Make.com Automation Tutorial", description: "Script via /api/script, ElevenLabs VO, Zara briefs for automation B-roll", time_block: "10am–12pm" },
    // Week 2
    { date: "2026-04-14", day_of_week: "Tuesday",   type: "publish",   title: "PUBLISH EP002 — Automate YouTube with Make.com", description: "Upload, chapters, description with Make.com affiliate link", time_block: "2pm EST", dependencies: ["EP002 edit complete"] },
    { date: "2026-04-15", day_of_week: "Wednesday",  type: "research",  title: "Research: Kling AI Beginner Tutorial",      description: "Generate sample Kling clips for demo, document settings, test v2 features", time_block: "9am–10am" },
    { date: "2026-04-16", day_of_week: "Thursday",   type: "record",    title: "Script + VO: Kling AI Tutorial",            description: "Script, VO, Zara generates Kling demo clips as in-video examples", time_block: "10am–12pm" },
    { date: "2026-04-17", day_of_week: "Friday",     type: "edit",      title: "Edit EP003: Kling Tutorial",               description: "Assemble VO + Kling clips + motion graphics, add captions", time_block: "10am–1pm" },
    { date: "2026-04-19", day_of_week: "Sunday",     type: "community", title: "Community Post: Poll — Claude vs ChatGPT",  description: "Post YouTube community poll to drive engagement before EP004", time_block: "11am" },
    // Week 3
    { date: "2026-04-21", day_of_week: "Tuesday",   type: "publish",   title: "PUBLISH EP003 — Kling AI for Beginners",   description: "Upload with Kling affiliate referral link in description", time_block: "2pm EST", dependencies: ["EP003 edit complete"] },
    { date: "2026-04-22", day_of_week: "Wednesday",  type: "research",  title: "Research: Claude vs ChatGPT for Creators", description: "Benchmark both models on 10 creator tasks, document results", time_block: "9am–11am" },
    { date: "2026-04-23", day_of_week: "Thursday",   type: "record",    title: "Script + VO: Claude vs ChatGPT",           description: "Comparison script, ElevenLabs VO, Zara generates split-screen B-roll", time_block: "10am–12pm" },
    { date: "2026-04-24", day_of_week: "Friday",     type: "edit",      title: "Edit EP004: Claude vs ChatGPT",            description: "Assemble split-screen comparison, motion graphics, thumbnail", time_block: "10am–1pm" },
    { date: "2026-04-25", day_of_week: "Saturday",   type: "shorts",    title: "Shorts: 60-sec clip from EP003",           description: "Clip best Kling demo moment, add captions, post as YouTube Short", time_block: "30min" },
    // Week 4
    { date: "2026-04-28", day_of_week: "Tuesday",   type: "publish",   title: "PUBLISH EP004 — Claude vs ChatGPT",        description: "Upload with Anthropic affiliate in description", time_block: "2pm EST", dependencies: ["EP004 edit complete"] },
    { date: "2026-04-29", day_of_week: "Wednesday",  type: "research",  title: "Research: ElevenLabs Voice Cloning Guide", description: "Document voice cloning workflow, test custom voice creation, record demos", time_block: "9am–10am" },
    { date: "2026-04-30", day_of_week: "Thursday",   type: "record",    title: "Script + VO: ElevenLabs Voice Cloning",    description: "Script, VO with Daniel voice, Zara B-roll of audio waveforms", time_block: "10am–12pm" },
    { date: "2026-05-01", day_of_week: "Friday",     type: "analytics", title: "April Analytics Review",                   description: "Review views, CTR, watch time, subscriber growth — adjust May strategy", time_block: "9am–10am" },
    { date: "2026-05-04", day_of_week: "Monday",     type: "publish",   title: "PUBLISH EP005 — ElevenLabs Voice Cloning", description: "Upload with ElevenLabs affiliate link, community post announcing release", time_block: "2pm EST", dependencies: ["EP005 edit complete"] },
  ],
  weekly_schedule_template: {
    Monday:    ["Community post or Shorts repurposing"],
    Tuesday:   ["PUBLISH at 2PM EST — promote on social"],
    Wednesday: ["Research + outline next video"],
    Thursday:  ["Script + VO + Zara B-roll briefs OR publish 2nd video"],
    Friday:    ["Edit + thumbnail finalization"],
    Saturday:  ["Buffer / Shorts creation"],
    Sunday:    ["Script review + schedule posts"]
  },
  milestones: [
    { date: "2026-04-09", milestone: "EP001 live — channel launch 🚀" },
    { date: "2026-04-14", milestone: "EP002 live — 2nd video, pipeline proven" },
    { date: "2026-04-21", milestone: "EP003 live — first Kling tutorial" },
    { date: "2026-04-28", milestone: "EP004 live — comparison video (high-search)" },
    { date: "2026-05-01", milestone: "April analytics review — optimize strategy" },
    { date: "2026-05-04", milestone: "EP005 live — 5 videos in 4 weeks" },
  ],
  time_allocation: {
    research:     "~2h/week",
    scripting:    "~1h/week (AI-assisted)",
    voiceover:    "~30min/week",
    broll_briefs: "~30min/week (Zara handles generation)",
    editing:      "~3-4h/week",
    thumbnail:    "~30min/week (Zara + Ideogram)",
    publishing:   "~30min/week"
  },
  bottlenecks: [
    "Kling slow queue on free plan — upgrade to Standard for faster B-roll turnaround",
    "Ideogram 14 slow credits — 2 videos/week will burn through free credits; consider pay-per-use",
    "Edit time is the longest step — batch editing on weekends saves weekday flow",
    "Make.com automation reduces upload friction but requires Creatomate connection (now fixed)"
  ]
};

export async function GET() {
  return Response.json(SEEDED_CALENDAR);
}

interface CalendarRequest {
  start_date: string;
  weeks?: number;
  channel_cadence?: string;
  video_topics?: string[];
  channel_goals?: string[];
}

interface CalendarEvent {
  date: string;
  day_of_week: string;
  type: 'publish' | 'record' | 'edit' | 'research' | 'shorts' | 'community' | 'analytics';
  title: string;
  description: string;
  time_block: string;
  dependencies?: string[];
}

interface CalendarResponse {
  period: string;
  cadence: string;
  events: CalendarEvent[];
  weekly_schedule_template: Record<string, string[]>;
  milestones: Array<{ date: string; milestone: string }>;
  time_allocation: Record<string, string>;
  bottlenecks: string[];
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
    const body = await request.json() as Partial<CalendarRequest>;
    if (!body.start_date?.trim()) {
      return Response.json({ error: 'Missing required field: start_date' }, { status: 400 });
    }

    const weeks = body.weeks ?? 4;
    const cadence = body.channel_cadence ?? '2 videos per week';

    const prompt = `You are the Project Manager for @VRealAI (V-Real AI). Generate a ${weeks}-week content calendar.

START DATE: ${body.start_date}
POSTING CADENCE: ${cadence}
PLANNED TOPICS: ${JSON.stringify(body.video_topics ?? ['Top 5 free AI tools 2025', 'How to automate YouTube with Make.com', 'Kling AI tutorial for beginners', 'Claude vs ChatGPT for creators', 'Build a faceless YouTube channel with AI', 'ElevenLabs voice cloning guide', 'Ideogram AI for thumbnails', 'n8n automation for content creators'])}
CHANNEL GOALS: ${JSON.stringify(body.channel_goals ?? ['grow to 1000 subscribers in 90 days', 'monetize with affiliate links', 'build automated production pipeline'])}

@VRealAI workflow: AI voiceover (ElevenLabs Daniel voice), 100% faceless format, Zara visual director agent for thumbnails + B-roll, Make.com automation pipeline, Ideogram for thumbnails.
Typical production: Research (1h) → Script via /api/script (1h AI) → Voiceover via ElevenLabs (30min) → B-roll via Zara+Kling (1h) → Edit (2h) → Thumbnail via Zara+Ideogram (30min) → Upload (30min).
Channel brand: #0A0F1E navy, #00D4FF cyan, #FFB347 amber. Channel handle: @VRealAI.

Return ONLY valid JSON:
{
  "period": "<start date to end date>",
  "cadence": "${cadence}",
  "events": [
    {
      "date": "<YYYY-MM-DD>",
      "day_of_week": "<Monday etc>",
      "type": "publish|record|edit|research|shorts|community|analytics",
      "title": "<event title>",
      "description": "<what to do>",
      "time_block": "<e.g. 9am-11am>",
      "dependencies": ["<what must be done first>"]
    }
  ],
  "weekly_schedule_template": {
    "Monday": ["<task>"],
    "Tuesday": ["<task>"],
    "Wednesday": ["<task>"],
    "Thursday": ["<task>"],
    "Friday": ["<task>"]
  },
  "milestones": [{"date": "<YYYY-MM-DD>", "milestone": "<milestone description>"}],
  "time_allocation": {"research": "~2h/week", "scripting": "~4h/week", "recording": "~2h/week", "editing": "~6h/week", "distribution": "~2h/week"},
  "bottlenecks": ["<potential bottleneck in this schedule>"]
}`;

    const raw = await callClaude(prompt);
    const result = JSON.parse(raw) as CalendarResponse;
    return Response.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return Response.json({ error: message.includes('JSON') ? 'Failed to parse AI response — retry' : message }, { status: 500 });
  }
}
