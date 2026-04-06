import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const res = await fetch(`${BACKEND}/api/threads/${id}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fallback mock data when backend is unavailable
    const thread = {
      id,
      subject: id === 'thread-1' ? 'Q2 Content Strategy Review'
              : id === 'thread-2' ? 'YouTube Shorts Performance Metrics'
              : id === 'thread-3' ? 'Affiliate Program Expansion'
              : `Thread ${id}`,
      participants: ['ceo-agent', 'content-vp', 'analytics-vp'],
      status: 'active',
      updated_at: new Date().toISOString(),
      messages: [
        {
          id: `msg-${id}-1`,
          sender_type: 'agent',
          sender_agent_id: 'ceo-agent',
          sender_name: 'Marcus Chen',
          content: 'Let\'s review the quarterly roadmap. I want every channel aligned on priorities.',
          created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          status: 'delivered',
        },
        {
          id: `msg-${id}-2`,
          sender_type: 'agent',
          sender_agent_id: 'content-vp',
          sender_name: 'Sofia Rivera',
          content: 'Agreed. We should focus on improving retention — our average watch time is 4:20 but we\'re targeting 6:00 by Q2.',
          created_at: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
          status: 'delivered',
        },
        {
          id: `msg-${id}-3`,
          sender_type: 'agent',
          sender_agent_id: 'analytics-vp',
          sender_name: 'Priya Sharma',
          content: 'Watch time is up 23% month-over-month. The hook improvements are working. CTR is the current bottleneck — 3.8% vs. industry average of 5.2%.',
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          status: 'delivered',
        },
      ],
    };
    return NextResponse.json(thread);
  }
}
