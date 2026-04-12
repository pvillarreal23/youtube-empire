import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const res = await fetch(`${BACKEND}/api/feed/unread_count?${searchParams}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fallback mock data when backend is unavailable
    const unreadData = {
      total: 12,
      by_channel: {
        general: 5,
        announcements: 3,
        content: 2,
        analytics: 2,
      },
    };
    return NextResponse.json(unreadData);
  }
}

export async function POST(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const res = await fetch(`${BACKEND}/api/feed/unread_count?${searchParams}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    return NextResponse.json(await res.json());
  } catch {
    // Fallback mock data when backend is unavailable
    const response = {
      status: 'marked_read',
      channel: 'all',
      marked_at: new Date().toISOString(),
    };
    return NextResponse.json(response);
  }
}
