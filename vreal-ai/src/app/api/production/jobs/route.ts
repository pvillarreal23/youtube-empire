export const dynamic = 'force-dynamic';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
  const res = await fetch(`${API}/api/production/jobs`);
  const data = await res.json();
  return Response.json(data);
}

export async function POST(request: Request) {
  const body = await request.json();
  const res = await fetch(`${API}/api/production/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return Response.json(data, { status: res.status });
}
