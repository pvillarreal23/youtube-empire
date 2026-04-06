import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const res = await fetch(`${BACKEND}/api/scheduler/tasks?${searchParams}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fallback mock data when backend is unavailable
    const scheduledTasks = [
      {
        id: 'task-1',
        agent_id: 'content-vp',
        agent_name: 'Content VP',
        name: 'Weekly Content Strategy Sync',
        cron_expression: '0 9 * * MON',
        enabled: true,
        last_run: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
        category: 'content',
      },
      {
        id: 'task-2',
        agent_id: 'analytics-vp',
        agent_name: 'Analytics VP',
        name: 'Monthly Performance Report',
        cron_expression: '0 8 1 * *',
        enabled: true,
        last_run: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        category: 'analytics',
      },
      {
        id: 'task-3',
        agent_id: 'seo-specialist',
        agent_name: 'SEO Specialist',
        name: 'SEO Optimization Audit',
        cron_expression: '0 10 * * WED',
        enabled: true,
        last_run: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        category: 'content',
      },
      {
        id: 'task-4',
        agent_id: 'trend-researcher',
        agent_name: 'Trend Researcher',
        name: 'Weekly Trend Report',
        cron_expression: '0 7 * * FRI',
        enabled: true,
        last_run: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        category: 'research',
      },
      {
        id: 'task-5',
        agent_id: 'ceo-agent',
        agent_name: 'CEO Agent',
        name: 'Morning Briefing',
        cron_expression: '0 6 * * *',
        enabled: true,
        last_run: new Date(Date.now() - 18 * 60 * 60 * 1000).toISOString(),
        category: 'executive',
      },
      {
        id: 'task-6',
        agent_id: 'newsletter-strategist',
        agent_name: 'Newsletter Strategist',
        name: 'Weekly Newsletter Draft',
        cron_expression: '0 9 * * THU',
        enabled: true,
        last_run: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
        category: 'monetization',
      },
      {
        id: 'task-7',
        agent_id: 'quality-assurance-lead',
        agent_name: 'Quality Assurance Lead',
        name: 'Content Quality Review',
        cron_expression: '0 14 * * TUE,THU',
        enabled: true,
        last_run: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        category: 'operations',
      },
      {
        id: 'task-8',
        agent_id: 'community-manager',
        agent_name: 'Community Manager',
        name: 'YouTube Comment Engagement',
        cron_expression: '0 12 * * *',
        enabled: false,
        last_run: null,
        category: 'community',
      },
    ];
    return NextResponse.json(scheduledTasks);
  }
}
