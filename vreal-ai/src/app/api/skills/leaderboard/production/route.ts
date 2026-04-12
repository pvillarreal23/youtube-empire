export const dynamic = 'force-dynamic';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET() {
  const res = await fetch(`${API}/api/skills/leaderboard/production`);
  const data = await res.json();
  return Response.json(data);
}
