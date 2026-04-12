// api/make.js — Vercel Serverless Proxy for Make.com API
// Keeps your API key server-side; the browser only calls /api/make

const MAKE_BASE = process.env.MAKE_BASE_URL || 'https://us2.make.com/api/v2';
const TEAM_ID   = process.env.MAKE_TEAM_ID  || '2078612';

// GET-allowed endpoint patterns (read-only dashboard data)
const ALLOWED_GET = [
  /^scenarios$/,
  /^scenarios\/\d+$/,
  /^scenarios\/\d+\/executions$/,
  /^scenarios\/\d+\/logs$/,
  /^scenarios\/\d+\/blueprint$/,
];

// PUT-allowed endpoints (blueprint updates only)
const ALLOWED_PUT = [
  /^scenarios\/\d+\/blueprint$/,
];

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') return res.status(200).end();

  const MAKE_API_KEY = process.env.MAKE_API_KEY;
  if (!MAKE_API_KEY) {
    return res.status(500).json({ error: 'MAKE_API_KEY environment variable is not set.' });
  }

  const { endpoint, ...queryParams } = req.query;
  if (!endpoint) {
    return res.status(400).json({ error: 'endpoint query param required' });
  }

  const isGet = req.method === 'GET';
  const isPut = req.method === 'PUT';

  if (isGet && !ALLOWED_GET.some(r => r.test(endpoint))) {
    return res.status(403).json({ error: `GET endpoint "${endpoint}" is not allowed.` });
  }
  if (isPut && !ALLOWED_PUT.some(r => r.test(endpoint))) {
    return res.status(403).json({ error: `PUT endpoint "${endpoint}" is not allowed.` });
  }
  if (!isGet && !isPut) {
    return res.status(405).json({ error: 'Only GET and PUT are supported.' });
  }

  const params = new URLSearchParams({ teamId: TEAM_ID, ...queryParams });
  const url = `${MAKE_BASE}/${endpoint}?${params}`;

  try {
    const upstreamOptions = {
      method: req.method,
      headers: {
        Authorization: `Token ${MAKE_API_KEY}`,
        'Content-Type': 'application/json',
      },
    };

    if (isPut && req.body) {
      upstreamOptions.body = JSON.stringify(req.body);
    }

    const upstream = await fetch(url, upstreamOptions);
    const data = await upstream.json();

    if (isGet) {
      res.setHeader('Cache-Control', 's-maxage=10, stale-while-revalidate=30');
    }
    return res.status(upstream.status).json(data);
  } catch (err) {
    return res.status(502).json({ error: `Upstream fetch failed: ${err.message}` });
  }
}
