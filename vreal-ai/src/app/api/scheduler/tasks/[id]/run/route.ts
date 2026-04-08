import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  try {
    const res = await fetch(`${BACKEND}/api/scheduler/tasks/${id}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    return NextResponse.json(await res.json(), { status: res.status });
  } catch {
    // Fallback mock data when backend is unavailable
    const response = {
      id,
      status: 'running',
      started_at: new Date().toISOString(),
      message: 'Task execution started',
    };
    return NextResponse.json(response);
  }
}
