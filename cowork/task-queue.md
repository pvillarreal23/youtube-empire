# Cowork Task Queue — V-Real AI

Status: PENDING = needs doing | DONE = completed | BLOCKED = waiting on something

---

## TASK 1: Update YouTube Channel Settings [DONE — Channel already exists]
**When:** Anytime — no dependencies
**Time needed:** ~20 minutes

### Prompt for Cowork:

Set up the V-Real AI YouTube channel. Here's everything you need:

1. GO TO youtube.com → Create channel
   - Channel name: V-Real AI
   - Handle: @VRealAI
   - If @VRealAI is taken, try @VRealAI_ or @TheVRealAI

2. CHANNEL SETTINGS (YouTube Studio → Customization):
   - Description:
     "You're not paranoid. You're observant.

     V-Real AI is an AI-powered documentary channel exploring how artificial intelligence is reshaping work, business, and daily life.

     New episodes every Tuesday and Thursday at 2PM EST.

     Built transparently with AI. Every tool, every workflow, every mistake — documented."

   - Channel keywords: AI tools, artificial intelligence, AI for business, AI documentary, AI marketing, AI automation, solopreneur AI, faceless YouTube

3. BRANDING (YouTube Studio → Customization → Branding):
   - Profile picture: Generate using Task 2 below first
   - Banner: Generate using Task 2 below first
   - Video watermark: Same as profile pic icon

4. DEFAULT UPLOAD SETTINGS (YouTube Studio → Settings → Upload defaults):
   - Description template:
     "You're not paranoid. You're observant.

     Subscribe for new AI documentaries every Tuesday & Thursday

     V-Real AI — exploring how AI is reshaping everything.

     #AI #ArtificialIntelligence #AITools"
   - Tags: AI, artificial intelligence, AI tools, AI documentary, AI for business
   - Category: Science & Technology
   - License: Standard YouTube License
   - Comments: Allow all comments

5. When done, send me the channel URL.

---

## TASK 2: Generate Brand Assets in Canva [PENDING] [PRIORITY: HIGH]
**When:** Before or alongside Task 1
**Time needed:** ~30 minutes
**Reference file:** /home/user/youtube-empire/brand/vreal-ai-brand-brief.md

### Prompt for Cowork:

I need you to create brand assets for V-Real AI YouTube channel using Canva (free or Pro).

PROFILE PICTURE (800x800):
1. Go to Canva → Custom size → 800 x 800 px
2. Set background color to #0A0A0F (near black)
3. Create a clean geometric "V" lettermark:
   - Use a bold, angular V shape
   - Left stroke: white (#F8FAFC)
   - Right stroke: electric blue (#3B82F6)
   - Keep it SIMPLE — must be recognizable at 40px (tiny YouTube comment size)
4. Give it generous padding (at least 30% margin on all sides)
5. Export as PNG → save as "vreal-ai-profile-800x800.png"

YOUTUBE BANNER (2560x1440):
1. Go to Canva → YouTube Channel Art template (2560 x 1440)
2. Background: #0A0A0F (near black)
3. Add a subtle gradient from center (#141420) fading to edges
4. In the CENTER SAFE ZONE (this is critical — all text must be centered):
   - "V-REAL AI" — large, Inter Black or Montserrat ExtraBold, white (#F8FAFC), ALL CAPS, wide letter spacing
   - Below: "YOU'RE NOT PARANOID. YOU'RE OBSERVANT." — medium, same font but lighter weight, white
   - Below: "New episodes Tuesday & Thursday" — small, regular weight, gray (#94A3B8)
5. Optional: subtle electric blue glow (#3B82F6 at 10% opacity) behind the logo text
6. Do NOT put important text outside the center — it gets cropped on mobile
7. Export as PNG → save as "vreal-ai-banner-2560x1440.png"

THUMBNAIL TEMPLATE (1280x720) — make 3 versions:

Version A — "Breakdown" style:
1. Canva → Custom size → 1280 x 720
2. Dark background (#0A0A0F)
3. Large bold text (3-4 words max), Inter ExtraBold, white
4. Blue accent line (#3B82F6) under the text
5. Right side: placeholder area for a visual/image
6. Small V-Real AI logo watermark, bottom-right, 15% opacity
7. Save as template

Version B — "Playbook" style:
1. Same size, dark background
2. Number-driven title area ("$50/MO AI STACK" style)
3. The number/dollar amount in amber (#F59E0B)
4. Rest of text in white
5. Clean, structured, grid-like feel
6. Save as template

Version C — "Story" style:
1. Same size, dark background
2. Minimal text (1-2 words), very large
3. More atmospheric — blurred background image area
4. Strong blue glow/atmosphere
5. Most cinematic of the three
6. Save as template

Upload all files to the repo at: /home/user/youtube-empire/brand/assets/
Or share them with me so I can place them.

---

## TASK 3: Set Up Make.com Pressure Test Scenarios [PENDING] [PRIORITY: MEDIUM]
**When:** After Pedro gets API keys for OpenAI/Gemini/Grok
**Time needed:** ~30 minutes
**Requires:** Make.com account, API keys for OpenAI + Google Gemini + xAI Grok

### Prompt for Cowork:

I need you to create 3 Make.com scenarios that act as API proxies for our multi-model pressure testing. Our cloud server gets 403 blocked when calling OpenAI, Gemini, and Grok directly, so Make.com will relay the requests.

CREATE THESE 3 SCENARIOS IN MAKE.COM:

1. "Pressure Test — OpenAI (ChatGPT)"
   - Trigger: Webhook (Custom webhook) → click "Add" to create a new webhook
   - Module: HTTP → Make a request
     - URL: https://api.openai.com/v1/chat/completions
     - Method: POST
     - Headers:
       - Authorization: Bearer [PASTE YOUR OPENAI API KEY]
       - Content-Type: application/json
     - Body type: Raw → JSON
     - Body: {"model": "gpt-4o", "messages": [{"role": "user", "content": "{{1.prompt}}"}], "max_tokens": {{1.max_tokens}}}
   - Add a "JSON" module after HTTP to parse the response
   - Final module: Webhook response → return JSON:
     {"text": "{{parseJSON.choices[0].message.content}}"}
   - Turn ON the scenario
   - Copy the webhook URL

2. "Pressure Test — Gemini"
   - Trigger: Webhook (Custom webhook)
   - Module: HTTP → Make a request
     - URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
     - Method: POST
     - Headers:
       - Content-Type: application/json
       - x-goog-api-key: [PASTE YOUR GEMINI API KEY]
     - Body: {"contents": [{"parts": [{"text": "{{1.prompt}}"}]}], "generationConfig": {"maxOutputTokens": {{1.max_tokens}}}}
   - Parse response JSON
   - Webhook response: {"text": "{{parseJSON.candidates[0].content.parts[0].text}}"}
   - Turn ON, copy webhook URL

3. "Pressure Test — Grok"
   - Trigger: Webhook (Custom webhook)
   - Module: HTTP → Make a request
     - URL: https://api.x.ai/v1/chat/completions
     - Method: POST
     - Headers:
       - Authorization: Bearer [PASTE YOUR GROK API KEY]
       - Content-Type: application/json
     - Body: {"model": "grok-3", "messages": [{"role": "user", "content": "{{1.prompt}}"}], "max_tokens": {{1.max_tokens}}}
   - Parse response JSON
   - Webhook response: {"text": "{{parseJSON.choices[0].message.content}}"}
   - Turn ON, copy webhook URL

TEST EACH ONE: After creating, click "Run once" on each scenario, then use the "Send a test request" option. Send this test payload:
{"model": "test", "prompt": "Say hello in one sentence.", "max_tokens": 100, "source": "pressure_test"}

If it returns a response with "text" containing a greeting, it works.

GIVE ME THE 3 WEBHOOK URLs when done. Format:
MAKE_WEBHOOK_PRESSURE_OPENAI=https://hook.us1.make.com/xxx
MAKE_WEBHOOK_PRESSURE_GEMINI=https://hook.us1.make.com/yyy
MAKE_WEBHOOK_PRESSURE_GROK=https://hook.us1.make.com/zzz

---

## TASK 4: Add API Keys to .env [PENDING] [PRIORITY: MEDIUM]
**When:** When Pedro has the API keys ready
**Time needed:** ~5 minutes
**Requires:** API keys for OpenAI, Google Gemini, xAI Grok

### Prompt for Cowork:

I need you to add API keys to two .env files on the server. Open a terminal and run these commands (replace the placeholder values with real keys):

```bash
cd /home/user/youtube-empire

# Add to both .env files
# Replace YOUR_KEY_HERE with the actual API keys

# OpenAI (get from https://platform.openai.com/api-keys)
sed -i 's/^OPENAI_API_KEY=$/OPENAI_API_KEY=YOUR_KEY_HERE/' vreal-ai/.env
sed -i 's/^OPENAI_API_KEY=$/OPENAI_API_KEY=YOUR_KEY_HERE/' vreal-ai/backend/.env

# Gemini (get from https://aistudio.google.com/app/apikey)
sed -i 's/^GEMINI_API_KEY=$/GEMINI_API_KEY=YOUR_KEY_HERE/' vreal-ai/.env
sed -i 's/^GEMINI_API_KEY=$/GEMINI_API_KEY=YOUR_KEY_HERE/' vreal-ai/backend/.env

# Grok (get from https://console.x.ai)
sed -i 's/^GROK_API_KEY=$/GROK_API_KEY=YOUR_KEY_HERE/' vreal-ai/.env
sed -i 's/^GROK_API_KEY=$/GROK_API_KEY=YOUR_KEY_HERE/' vreal-ai/backend/.env
```

After adding the keys, restart the backend:
```bash
pkill -f uvicorn
cd /home/user/youtube-empire/vreal-ai/backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
```

Verify it's running:
```bash
curl http://127.0.0.1:8000/api/health
```
Should return: {"status":"ok"}

---

## TASK 5: Add Make.com Webhook URLs to .env [PENDING] [PRIORITY: MEDIUM]
**When:** After Task 3 is done (Make.com scenarios created)
**Time needed:** ~5 minutes
**Requires:** The 3 webhook URLs from Task 3

### Prompt for Cowork:

Add the Make.com pressure test webhook URLs to the .env files. Replace the URLs below with the actual ones from Task 3:

```bash
cd /home/user/youtube-empire

# Add webhook URLs (replace with actual URLs from Make.com)
sed -i 's|^MAKE_WEBHOOK_PRESSURE_OPENAI=$|MAKE_WEBHOOK_PRESSURE_OPENAI=PASTE_URL_HERE|' vreal-ai/.env
sed -i 's|^MAKE_WEBHOOK_PRESSURE_OPENAI=$|MAKE_WEBHOOK_PRESSURE_OPENAI=PASTE_URL_HERE|' vreal-ai/backend/.env

sed -i 's|^MAKE_WEBHOOK_PRESSURE_GEMINI=$|MAKE_WEBHOOK_PRESSURE_GEMINI=PASTE_URL_HERE|' vreal-ai/.env
sed -i 's|^MAKE_WEBHOOK_PRESSURE_GEMINI=$|MAKE_WEBHOOK_PRESSURE_GEMINI=PASTE_URL_HERE|' vreal-ai/backend/.env

sed -i 's|^MAKE_WEBHOOK_PRESSURE_GROK=$|MAKE_WEBHOOK_PRESSURE_GROK=PASTE_URL_HERE|' vreal-ai/.env
sed -i 's|^MAKE_WEBHOOK_PRESSURE_GROK=$|MAKE_WEBHOOK_PRESSURE_GROK=PASTE_URL_HERE|' vreal-ai/backend/.env
```

Then restart the backend:
```bash
pkill -f uvicorn
cd /home/user/youtube-empire/vreal-ai/backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
```

---

## TASK 6: Push EP001 Assets from Local Machine [PENDING] [PRIORITY: HIGH]
**When:** When Pedro has laptop access
**Time needed:** ~10 minutes
**Requires:** Laptop access with the 17 EP001 asset files

### Prompt for Cowork:

Pedro has EP001 assets on his local machine (17 files, ~176MB in output/ep001/). These need to be pushed to the cloud server.

On Pedro's laptop, open terminal and run:

```bash
cd /path/to/youtube-empire
git add output/ep001/
git commit -m "Add EP001 assets: voiceover, b-roll, music, SFX"
git push origin claude/improve-video-editing-mDM2y
```

If git push fails due to large files, use Git LFS:
```bash
git lfs install
git lfs track "*.mp3" "*.mp4" "*.wav" "*.png" "*.jpg"
git add .gitattributes
git add output/ep001/
git commit -m "Add EP001 assets via LFS"
git push origin claude/improve-video-editing-mDM2y
```

If that still fails (file too large), zip and upload manually:
```bash
cd output
zip -r ep001-assets.zip ep001/
# Upload ep001-assets.zip to Google Drive or similar, share the link
```

---

## TASK 7: Set Up Make.com YouTube Upload Scenario [PENDING] [PRIORITY: LOW]
**When:** After YouTube channel is set up (Task 1) and EP001 is ready
**Time needed:** ~20 minutes

### Prompt for Cowork:

Create a Make.com scenario that uploads videos to YouTube when triggered by our pipeline.

1. Create new scenario: "YouTube Upload — V-Real AI"
2. Trigger: Webhook (Custom webhook)
3. Module 1: YouTube → Upload a Video
   - Connect your YouTube account (the @VRealAI channel)
   - Title: {{1.title}}
   - Description: {{1.description}}
   - Tags: {{1.tags}}
   - Category: 28 (Science & Technology)
   - Privacy: Private (we'll manually switch to public after review)
   - File: {{1.video_url}} (URL to the video file)
4. Module 2: Webhook response → return {"video_id": "{{youtube_video_id}}", "status": "uploaded"}
5. Turn ON the scenario
6. Copy the webhook URL

Give me the webhook URL when done. Format:
MAKE_WEBHOOK_UPLOAD=https://hook.us1.make.com/xxx

---

## COMPLETED TASKS
(Move tasks here when done)

---

*Last updated: April 6, 2026*
*This file is at: /home/user/youtube-empire/cowork/task-queue.md*
*New tasks will be added as they come up.*
