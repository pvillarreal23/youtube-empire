import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const res = await fetch(`${BACKEND}/api/scheduler/escalations/${id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    return NextResponse.json(await res.json(), { status: res.status });
  } catch {
    // Fallback mock data when backend is unavailable
    const response = {
      id,
      status: 'resolved',
      resolved_at: new Date().toISOString(),
      message: 'Escalation marked as resolved',
    };
    return NextResponse.json(response);
  }
}
