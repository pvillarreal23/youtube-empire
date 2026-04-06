import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND}/api/feed/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    return NextResponse.json(await res.json(), { status: res.status });
  } catch {
    // Fallback mock data when backend is unavailable
    const newMessage = {
      id: `msg-${Date.now()}`,
      channel: 'general',
      sender: 'Unknown',
      content: '',
      created_at: new Date().toISOString(),
      likes: 0,
      replies: 0,
      unread: false,
    };
    return NextResponse.json(newMessage, { status: 201 });
  }
}
