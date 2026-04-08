import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const res = await fetch(`${BACKEND}/api/tools/scenarios?${searchParams}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fallback mock data when backend is unavailable
    const scenarios = [
      {
        id: 'scenario-1',
        name: 'Script Generation Pipeline',
        description: 'Automated script generation for video content',
        tools: ['Claude AI', 'Notion', 'YouTube Studio'],
        agents: ['Scriptwriter', 'Hook Specialist', 'Voice Director'],
        frequency: 'daily',
        status: 'active',
        last_run: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'scenario-2',
        name: 'Performance Analysis',
        description: 'Weekly analytics review and reporting',
        tools: ['Google Analytics', 'Notion', 'Claude AI'],
        agents: ['Analytics VP', 'Data Analyst'],
        frequency: 'weekly',
        status: 'active',
        last_run: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'scenario-3',
        name: 'Content Approval Workflow',
        description: 'Quality assurance and approval process',
        tools: ['Notion', 'Claude AI'],
        agents: ['Content VP', 'Quality Assurance Lead'],
        frequency: 'continuous',
        status: 'active',
        last_run: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'scenario-4',
        name: 'Deployment Automation',
        description: 'Automated deployment to Vercel',
        tools: ['GitHub', 'Vercel'],
        agents: ['Automation Engineer', 'CEO Agent'],
        frequency: 'on-demand',
        status: 'active',
        last_run: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      },
    ];
    return NextResponse.json({ scenarios, total: scenarios.length });
  }
}
