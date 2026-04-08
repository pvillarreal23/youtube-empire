export const dynamic = 'force-dynamic';
export async function POST(request: Request) {
  const { title, style } = await request.json() as { title: string; style?: string };
  if (!title) return Response.json({ error: 'title is required' }, { status: 400 });
  if (!process.env.IDEOGRAM_API_KEY) return Response.json({ url: null, message: 'Add IDEOGRAM_API_KEY to Vercel env vars — free at ideogram.ai/manage-api' });
  const prompt = 'YouTube thumbnail, bold white title text reading "' + title + '", dark dramatic background, glowing tech elements, cinematic lighting, 16:9' + (style ? ', ' + style : '');
  const res = await fetch('https://api.ideogram.ai/generate', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Api-Key': process.env.IDEOGRAM_API_KEY }, body: JSON.stringify({ image_request: { prompt, model: 'V_2', aspect_ratio: 'ASPECT_16_9', magic_prompt_option: 'AUTO', style_type: 'REALISTIC' } }) });
  if (!res.ok) { const err = await res.json().catch(() => ({})); return Response.json({ error: 'Ideogram error: ' + res.status, details: err }, { status: res.status }); }
  const data = await res.json();
  return Response.json({ url: data.data?.[0]?.url ?? null });
}
