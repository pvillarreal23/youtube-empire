import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const res = await fetch(`${BACKEND}/api/threads?${searchParams}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fallback mock data when backend is unavailable
    const threads = [
      {
        id: 'thread-1',
        subject: 'Q2 Content Strategy Review',
        participants: ['ceo-agent', 'content-vp', 'analytics-vp'],
        messages: [],
        status: 'active',
        updated_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'thread-2',
        subject: 'YouTube Shorts Performance Metrics',
        participants: ['analytics-vp', 'shorts-and-clips-agent', 'social-media-manager'],
        messages: [],
        status: 'active',
        updated_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
      },
      {
        id: 'thread-3',
        subject: 'Affiliate Program Expansion',
        participants: ['monetization-vp', 'affiliate-coordinator', 'partnership-manager'],
        messages: [],
        status: 'resolved',
        updated_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
      },
    ];
    return NextResponse.json(threads);
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND}/api/threads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    return NextResponse.json(await res.json(), { status: res.status });
  } catch {
    // Fallback mock data when backend is unavailable
    const newThread = {
      id: `thread-${Date.now()}`,
      subject: 'New Thread',
      participants: [],
      messages: [],
      status: 'active',
      updated_at: new Date().toISOString(),
    };
    return NextResponse.json(newThread, { status: 201 });
  }
}
