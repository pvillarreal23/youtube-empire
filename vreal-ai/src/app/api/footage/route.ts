export const dynamic = 'force-dynamic';
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('query') ?? 'ai tools';
  const per_page = searchParams.get('per_page') ?? '10';
  if (!process.env.PEXELS_API_KEY) return Response.json({ videos: [], message: 'Add PEXELS_API_KEY to Vercel env vars — free at pexels.com/api' });
  const res = await fetch('https://api.pexels.com/videos/search?query=' + encodeURIComponent(query) + '&per_page=' + per_page, { headers: { Authorization: process.env.PEXELS_API_KEY } });
  if (!res.ok) return Response.json({ error: 'Pexels error: ' + res.status }, { status: res.status });
  const data = await res.json();
  return Response.json({ videos: data.videos ?? [] });
}
