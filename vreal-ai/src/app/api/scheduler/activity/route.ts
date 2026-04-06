import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// All 32 agents with realistic activity statuses
const AGENT_STATUSES = [
  { id: 'ceo-agent', name: 'CEO Agent', role: 'Chief Executive Officer', department: 'executive', avatar_color: 'yellow', status: 'working', current_task: 'Reviewing Q2 content strategy and approving budget allocation' },
  { id: 'content-vp', name: 'Content VP', role: 'VP of Content', department: 'content', avatar_color: 'purple', status: 'working', current_task: 'Auditing 5 video scripts — checking hook strength and retention' },
  { id: 'operations-vp', name: 'Operations VP', role: 'VP of Operations', department: 'operations', avatar_color: 'amber', status: 'working', current_task: 'Coordinating production pipeline for April uploads' },
  { id: 'analytics-vp', name: 'Analytics VP', role: 'VP of Analytics', department: 'analytics', avatar_color: 'emerald', status: 'working', current_task: 'Analyzing V-Real AI channel performance — CTR below target' },
  { id: 'monetization-vp', name: 'Monetization VP', role: 'VP of Monetization', department: 'monetization', avatar_color: 'red', status: 'done', current_task: 'Completed affiliate program audit — 3 new partners identified' },
  { id: 'ai-and-tech-channel-manager', name: 'AI & Tech Channel Manager', role: 'Channel Manager', department: 'content', avatar_color: 'blue', status: 'working', current_task: 'Scheduling 3 videos for April — optimizing publish times' },
  { id: 'finance-and-business-channel-manager', name: 'Finance & Business Channel Manager', role: 'Channel Manager', department: 'content', avatar_color: 'blue', status: 'done', current_task: 'Cash Flow Code launch plan drafted — awaiting CEO approval' },
  { id: 'psychology-and-behavior-channel-manager', name: 'Psychology & Behavior Channel Manager', role: 'Channel Manager', department: 'content', avatar_color: 'blue', status: 'done', current_task: 'Mind Shift channel brief complete — Month 13 launch' },
  { id: 'scriptwriter', name: 'Scriptwriter', role: 'Senior Scriptwriter', department: 'content', avatar_color: 'cyan', status: 'working', current_task: 'Writing script: "5 AI Tools Replacing Jobs in 2026"' },
  { id: 'hook-specialist', name: 'Hook Specialist', role: 'Hook Specialist', department: 'content', avatar_color: 'cyan', status: 'working', current_task: 'Generating 10 title/hook variants for April video lineup' },
  { id: 'storyteller', name: 'Storyteller', role: 'Narrative Specialist', department: 'content', avatar_color: 'cyan', status: 'done', current_task: 'Revised storytelling arc for "Make.com Automates Everything"' },
  { id: 'shorts-and-clips-agent', name: 'Shorts & Clips Agent', role: 'Short-Form Specialist', department: 'content', avatar_color: 'cyan', status: 'working', current_task: 'Clipping 3 Shorts from latest V-Real AI video' },
  { id: 'thumbnail-designer', name: 'Thumbnail Designer', role: 'Thumbnail Designer', department: 'content', avatar_color: 'cyan', status: 'working', current_task: 'Creating 2 A/B thumbnail variants for "Claude vs GPT-4o"' },
  { id: 'video-editor', name: 'Video Editor', role: 'Video Editor', department: 'content', avatar_color: 'cyan', status: 'done', current_task: 'Final cut exported — "How Make.com Automates Everything"' },
  { id: 'seo-specialist', name: 'SEO Specialist', role: 'SEO Specialist', department: 'content', avatar_color: 'cyan', status: 'working', current_task: 'Keyword research for 4 upcoming April videos' },
  { id: 'voice-director', name: 'Voice Director', role: 'Voice & Audio Director', department: 'content', avatar_color: 'cyan', status: 'done', current_task: 'Voiceover script annotated — ready for ElevenLabs render' },
  { id: 'project-manager', name: 'Project Manager', role: 'Project Manager', department: 'operations', avatar_color: 'amber', status: 'working', current_task: 'Updating editorial calendar — tracking 8 videos in pipeline' },
  { id: 'workflow-orchestrator', name: 'Workflow Orchestrator', role: 'Workflow Orchestrator', department: 'operations', avatar_color: 'amber', status: 'working', current_task: 'Routing 3 completed scripts to production queue' },
  { id: 'quality-assurance-lead', name: 'Quality Assurance Lead', role: 'QA Lead', department: 'operations', avatar_color: 'amber', status: 'working', current_task: 'QA review: checking brand consistency across April content' },
  { id: 'reflection-council', name: 'Reflection Council', role: 'Strategic Advisor', department: 'operations', avatar_color: 'amber', status: 'done', current_task: 'Post-mortem on March performance — recommendations filed' },
  { id: 'automation-engineer', name: 'Automation Engineer', role: 'Automation Engineer', department: 'operations', avatar_color: 'amber', status: 'working', current_task: 'Building YouTube upload automation via Make.com webhook' },
  { id: 'senior-researcher', name: 'Senior Researcher', role: 'Senior Researcher', department: 'analytics', avatar_color: 'emerald', status: 'working', current_task: 'Deep research: AI agent market trends for V-Real AI content' },
  { id: 'trend-researcher', name: 'Trend Researcher', role: 'Trend Researcher', department: 'analytics', avatar_color: 'emerald', status: 'done', current_task: 'Weekly trend report delivered — 5 viral topic opportunities' },
  { id: 'data-analyst', name: 'Data Analyst', role: 'Data Analyst', department: 'analytics', avatar_color: 'emerald', status: 'working', current_task: 'Building CTR benchmark model across V-Real AI top 10 videos' },
  { id: 'partnership-manager', name: 'Partnership Manager', role: 'Partnership Manager', department: 'monetization', avatar_color: 'red', status: 'done', current_task: 'Sponsor outreach sent to 4 AI tool companies' },
  { id: 'affiliate-coordinator', name: 'Affiliate Coordinator', role: 'Affiliate Coordinator', department: 'monetization', avatar_color: 'red', status: 'working', current_task: 'Setting up affiliate links for Make.com video description' },
  { id: 'digital-product-manager', name: 'Digital Product Manager', role: 'Digital Product Manager', department: 'monetization', avatar_color: 'red', status: 'done', current_task: 'AI Automation Starter Kit outline complete — ready for review' },
  { id: 'newsletter-strategist', name: 'Newsletter Strategist', role: 'Newsletter Strategist', department: 'monetization', avatar_color: 'red', status: 'working', current_task: 'Writing this week\'s newsletter — 847 subscribers waiting' },
  { id: 'community-manager', name: 'Community Manager', role: 'Community Manager', department: 'admin', avatar_color: 'pink', status: 'done', current_task: 'Replied to 23 YouTube comments — pinned top questions' },
  { id: 'social-media-manager', name: 'Social Media Manager', role: 'Social Media Manager', department: 'admin', avatar_color: 'pink', status: 'working', current_task: 'Scheduling Instagram + TikTok clips for the week' },
  { id: 'secretary-agent', name: 'Secretary Agent', role: 'Executive Secretary', department: 'admin', avatar_color: 'pink', status: 'working', current_task: 'Organizing weekly agent status reports for CEO review' },
  { id: 'compliance-officer', name: 'Compliance Officer', role: 'Compliance Officer', department: 'general', avatar_color: 'slate', status: 'done', current_task: 'Reviewed 2 sponsored video scripts for FTC compliance' },
];

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const res = await fetch(`${BACKEND}/api/scheduler/activity?${searchParams}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fallback mock data when backend is unavailable
    const working = AGENT_STATUSES.filter(a => a.status === 'working').length;
    const done = AGENT_STATUSES.filter(a => a.status === 'done').length;

    const activityData = {
      running_count: working,
      completed_today: done,
      pending_escalations: 1,
      total_agents: AGENT_STATUSES.length,
      agent_statuses: AGENT_STATUSES,
      recent_runs: [
        { id: 'run-1', agent_id: 'content-vp', task_name: 'Weekly script review — 5 scripts audited', status: 'complete', summary: 'All 5 scripts approved with minor revisions', completed_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(), thread_id: null },
        { id: 'run-2', agent_id: 'seo-specialist', task_name: 'Keyword research — April video lineup', status: 'complete', summary: '43 high-value keywords identified across 4 videos', completed_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(), thread_id: null },
        { id: 'run-3', agent_id: 'analytics-vp', task_name: 'CTR performance alert — below 4% threshold', status: 'escalated', summary: null, completed_at: null, thread_id: 'thread-1' },
        { id: 'run-4', agent_id: 'trend-researcher', task_name: 'Weekly trend report — AI & automation topics', status: 'complete', summary: '5 high-potential topics found: Claude 4, AI agents, automation ROI', completed_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(), thread_id: null },
        { id: 'run-5', agent_id: 'video-editor', task_name: 'Final export — Make.com Automates Everything', status: 'complete', summary: 'Video exported at 4K — ready for upload', completed_at: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(), thread_id: null },
        { id: 'run-6', agent_id: 'scriptwriter', task_name: 'Draft script — 5 AI Tools Replacing Jobs in 2026', status: 'in_progress', summary: null, completed_at: null, thread_id: null },
      ],
      escalations: [
        {
          id: 'esc-1',
          agent_id: 'analytics-vp',
          reason: 'V-Real AI CTR dropped below 4% — last 3 videos underperforming vs. 5.2% channel average',
          severity: 'high',
          thread_id: 'thread-1',
          created_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        },
      ],
    };
    return NextResponse.json(activityData);
  }
}
