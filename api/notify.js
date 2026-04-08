/**
 * api/notify.js — Review Queue for Creator AI Pipeline
 *
 * POST /api/notify  { title, script, topic, timestamp }
 *   Called by Make.com after Claude generates a script.
 *   Stores the pending review and returns the review URL.
 *
 * POST /api/notify  { action: 'approve'|'reject', reviewId }
 *   Called by the review page when Pedro approves or rejects.
 *   On approve: triggers the Make.com continuation webhook (ElevenLabs, etc.)
 *
 * GET /api/notify
 *   Returns the latest pending review (for the review page to display).
 */

const fs = require('fs');

const STORE_PATH = '/tmp/pending-review.json';

// In-memory fallback if /tmp is not writable
let memoryFallback = null;

function loadReview() {
  try {
    if (fs.existsSync(STORE_PATH)) {
      return JSON.parse(fs.readFileSync(STORE_PATH, 'utf8'));
    }
  } catch {}
  return memoryFallback;
}

function saveReview(review) {
  memoryFallback = review;
  try {
    if (review) {
      fs.writeFileSync(STORE_PATH, JSON.stringify(review));
    } else {
      if (fs.existsSync(STORE_PATH)) fs.unlinkSync(STORE_PATH);
    }
  } catch {}
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();

  // ── GET: return the current pending review ──────────────────────────────
  if (req.method === 'GET') {
    const pendingReview = loadReview();
    if (!pendingReview) {
      return res.status(200).json({ status: 'no_pending' });
    }
    return res.status(200).json(pendingReview);
  }

  // ── POST ────────────────────────────────────────────────────────────────
  if (req.method === 'POST') {
    const body = req.body || {};

    // ── Approve / Reject action from the review page ──
    if (body.action === 'approve') {
      const pendingReview = loadReview();
      if (pendingReview) {
        pendingReview.status = 'approved';
        saveReview(pendingReview);
      }

      const webhookUrl = process.env.MAKE_CONTINUE_WEBHOOK_URL;
      if (!webhookUrl) {
        // Webhook not configured yet — tell the UI so it can show a helpful message
        return res.status(200).json({
          success: true,
          noWebhook: true,
          message: 'Approved, but MAKE_CONTINUE_WEBHOOK_URL is not set in Vercel env. Add it to auto-trigger the voiceover step.'
        });
      }

      try {
        // Call the Make.com continuation webhook (triggers ElevenLabs → video → YouTube)
        const payload = pendingReview
          ? { script: pendingReview.script, title: pendingReview.title, topic: pendingReview.topic }
          : {};
        const upstream = await fetch(webhookUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        return res.status(200).json({ success: true, webhookCalled: true, upstreamStatus: upstream.status });
      } catch (err) {
        return res.status(502).json({ error: `Failed to call continuation webhook: ${err.message}` });
      }
    }

    if (body.action === 'reject') {
      const pendingReview = loadReview();
      if (pendingReview) {
        pendingReview.status = 'rejected';
        saveReview(pendingReview);
      }
      return res.status(200).json({ success: true, status: 'rejected' });
    }

    // ── New script submitted by Make.com ──────────────────────────────────
    const { title, script, topic, timestamp } = body;

    if (!script) {
      return res.status(400).json({ error: 'Missing required field: script' });
    }

    const pendingReview = {
      id: Date.now().toString(),
      title: title || topic || 'New Video Script',
      script,
      topic: topic || '',
      timestamp: timestamp || new Date().toISOString(),
      status: 'pending',
    };

    saveReview(pendingReview);

    const reviewUrl = `${process.env.VERCEL_URL
      ? 'https://' + process.env.VERCEL_URL
      : 'https://creator-ai-dashboard.vercel.app'}/review`;

    console.log(`[notify] New script queued for review: "${pendingReview.title}" — ${reviewUrl}`);

    return res.status(200).json({
      success: true,
      reviewUrl,
      id: pendingReview.id,
    });
  }

  return res.status(405).json({ error: 'Method not allowed' });
};
