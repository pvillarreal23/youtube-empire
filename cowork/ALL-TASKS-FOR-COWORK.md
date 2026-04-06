ALWAYS ALLOW COMMENTS ON ALL YOUTUBE VIDEOS AND COMMUNITY POSTS.

---

# V-REAL AI — ALL COWORK TASKS
# Copy this entire prompt and give it to cowork. Do them in order.

---

## TASK 1: UPDATE YOUTUBE CHANNEL SETTINGS
The V-Real AI YouTube channel (@VRealAI) already exists. Update these settings:

Go to YouTube Studio → Customization → Basic info:

Channel Description (replace whatever is there with this):
"You're not paranoid. You're observant.

V-Real AI is an AI-powered documentary channel exploring how artificial intelligence is reshaping work, business, and daily life.

New episodes every Tuesday and Thursday at 2PM EST.

Built transparently with AI. Every tool, every workflow, every mistake — documented."

Channel keywords: AI tools, artificial intelligence, AI for business, AI documentary, AI marketing, AI automation, solopreneur AI, faceless YouTube

Go to YouTube Studio → Settings → Upload defaults:
- Description template:
"You're not paranoid. You're observant.

Subscribe for new AI documentaries every Tuesday & Thursday

V-Real AI — exploring how AI is reshaping everything.

#AI #ArtificialIntelligence #AITools"
- Tags: AI, artificial intelligence, AI tools, AI documentary, AI for business
- Category: Science & Technology
- Comments: ALLOW ALL COMMENTS (important — never restrict comments)

Go to YouTube Studio → Customization → Branding:
- Upload the profile picture and banner from Task 2 below
- Video watermark: same as profile pic

---

## TASK 2: CREATE BRAND ASSETS IN CANVA
Use Canva (free or Pro) to create these:

PROFILE PICTURE (800x800):
1. Canva → Custom size → 800 x 800 px
2. Background color: #0A0A0F (near black)
3. Create a clean geometric "V" lettermark:
   - Bold, angular V shape
   - Left stroke: white (#F8FAFC)
   - Right stroke: electric blue (#3B82F6)
   - Keep it SIMPLE — must be recognizable when tiny
4. Generous padding (30% margin on all sides)
5. Export as PNG

YOUTUBE BANNER (2560x1440):
1. Canva → YouTube Channel Art template (2560 x 1440)
2. Background: #0A0A0F (near black)
3. Subtle gradient from center (#141420) fading to edges
4. ALL text must be in the CENTER (gets cropped on mobile otherwise):
   - "V-REAL AI" — large, Inter Black or Montserrat ExtraBold, white, ALL CAPS, wide letter spacing
   - Below: "YOU'RE NOT PARANOID. YOU'RE OBSERVANT." — medium, same font lighter weight, white
   - Below: "New episodes Tuesday & Thursday" — small, gray (#94A3B8)
5. Optional: subtle electric blue glow (#3B82F6 at 10% opacity) behind logo text
6. Export as PNG

THUMBNAIL TEMPLATES (1280x720) — make 3 versions:

Version A "Breakdown":
- Dark background (#0A0A0F)
- Large bold text (3-4 words max), white
- Blue accent line (#3B82F6) under text
- Right side: placeholder for image
- Small V-Real AI watermark bottom-right at 15% opacity

Version B "Playbook":
- Dark background
- Number/dollar in amber (#F59E0B), rest white
- Clean structured grid feel

Version C "Story":
- Dark background
- Minimal text (1-2 words), very large
- Atmospheric blurred background area
- Blue glow/atmosphere, most cinematic

Save all templates. Upload profile pic and banner to YouTube (Task 1).

---

## TASK 3: SET UP DISCORD SERVER
Create a Discord server for the V-Real AI community.

1. Create server:
   - Name: V-Real AI
   - Icon: Use the same profile pic from Task 2
   - Template: Community Server

2. Create these categories and channels:

WELCOME
  #rules — Server rules (see below)
  #introductions — New members introduce themselves
  #announcements — Video drops, updates (only admins post)

AI TALK
  #ai-tools — Discuss AI tools, share finds
  #ai-news — Breaking AI news and takes
  #prompt-sharing — Share useful prompts
  #ask-vreal — Ask questions, get community answers

BEHIND THE SCENES
  #building-in-public — How V-Real AI is built (AI pipeline updates)
  #episode-discussion — Discuss latest episodes
  #feedback — Suggestions for future episodes

RESOURCES
  #free-resources — Free AI tools, guides, templates
  #deals-and-discounts — AI tool deals (affiliate links go here)

3. Set up roles:
   - @V-Real Crew — default role for all members (blue color #3B82F6)
   - @OG — for first 100 members (gold color #F59E0B)
   - @Mod — moderators
   - @Pedro — admin

4. Welcome message (put in #rules):
"Welcome to V-Real AI.

You're not paranoid. You're observant.

This is a community for marketing professionals, solopreneurs, and anyone adapting to the AI shift. We're building an AI-powered documentary channel — transparently — and documenting everything along the way.

Rules:
1. Be respectful. No spam, no self-promo without permission.
2. Share what you know. This community grows when everyone contributes.
3. Ask questions. There are no dumb questions about AI.
4. No politics, no drama. We're here to build.
5. Have fun. Drop memes. Be human.

New episodes drop Tuesday & Thursday at 2PM EST.
Subscribe on YouTube: @VRealAI"

5. Server settings:
   - Verification level: Medium (must be registered for 5+ minutes)
   - Enable Community features
   - Set #announcements as the community updates channel

6. Give me the Discord invite link when done (set to never expire).

---

## TASK 4: SET UP MAKE.COM PRESSURE TEST SCENARIOS
Our cloud server gets 403 blocked when calling OpenAI, Gemini, and Grok directly. Make.com will relay the requests.

NOTE: You need API keys for OpenAI, Google Gemini, and xAI Grok first. If Pedro doesn't have these yet, skip this task and come back later.

Create 3 Make.com scenarios:

SCENARIO 1: "Pressure Test — OpenAI (ChatGPT)"
- Trigger: Webhook (Custom webhook) → click "Add"
- Module: HTTP → Make a request
  - URL: https://api.openai.com/v1/chat/completions
  - Method: POST
  - Headers: Authorization: Bearer [OPENAI API KEY], Content-Type: application/json
  - Body (Raw JSON): {"model": "gpt-4o", "messages": [{"role": "user", "content": "{{1.prompt}}"}], "max_tokens": {{1.max_tokens}}}
- Add JSON parse module
- Final: Webhook response → {"text": "{{parseJSON.choices[0].message.content}}"}
- Turn ON, copy webhook URL

SCENARIO 2: "Pressure Test — Gemini"
- Trigger: Webhook
- HTTP request:
  - URL: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
  - Method: POST
  - Headers: Content-Type: application/json, x-goog-api-key: [GEMINI API KEY]
  - Body: {"contents": [{"parts": [{"text": "{{1.prompt}}"}]}], "generationConfig": {"maxOutputTokens": {{1.max_tokens}}}}
- Webhook response: {"text": "{{parseJSON.candidates[0].content.parts[0].text}}"}
- Turn ON, copy webhook URL

SCENARIO 3: "Pressure Test — Grok"
- Trigger: Webhook
- HTTP request:
  - URL: https://api.x.ai/v1/chat/completions
  - Method: POST
  - Headers: Authorization: Bearer [GROK API KEY], Content-Type: application/json
  - Body: {"model": "grok-3", "messages": [{"role": "user", "content": "{{1.prompt}}"}], "max_tokens": {{1.max_tokens}}}
- Webhook response: {"text": "{{parseJSON.choices[0].message.content}}"}
- Turn ON, copy webhook URL

TEST each one with: {"model": "test", "prompt": "Say hello in one sentence.", "max_tokens": 100, "source": "pressure_test"}

Give me all 3 webhook URLs when done:
MAKE_WEBHOOK_PRESSURE_OPENAI=https://hook.us1.make.com/xxx
MAKE_WEBHOOK_PRESSURE_GEMINI=https://hook.us1.make.com/yyy
MAKE_WEBHOOK_PRESSURE_GROK=https://hook.us1.make.com/zzz

---

## TASK 5: ADD API KEYS TO SERVER
When Pedro has API keys ready, add them to the server.

Open terminal and run (replace YOUR_KEY_HERE with real keys):

cd /home/user/youtube-empire

sed -i 's/^OPENAI_API_KEY=$/OPENAI_API_KEY=YOUR_KEY_HERE/' vreal-ai/.env
sed -i 's/^OPENAI_API_KEY=$/OPENAI_API_KEY=YOUR_KEY_HERE/' vreal-ai/backend/.env

sed -i 's/^GEMINI_API_KEY=$/GEMINI_API_KEY=YOUR_KEY_HERE/' vreal-ai/.env
sed -i 's/^GEMINI_API_KEY=$/GEMINI_API_KEY=YOUR_KEY_HERE/' vreal-ai/backend/.env

sed -i 's/^GROK_API_KEY=$/GROK_API_KEY=YOUR_KEY_HERE/' vreal-ai/.env
sed -i 's/^GROK_API_KEY=$/GROK_API_KEY=YOUR_KEY_HERE/' vreal-ai/backend/.env

Then restart the backend:
pkill -f uvicorn
cd /home/user/youtube-empire/vreal-ai/backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

Verify: curl http://127.0.0.1:8000/api/health
Should return: {"status":"ok"}

---

## TASK 6: ADD MAKE.COM WEBHOOK URLS TO SERVER
After Task 4 is done, add the webhook URLs.

Open terminal:

cd /home/user/youtube-empire

sed -i 's|^MAKE_WEBHOOK_PRESSURE_OPENAI=$|MAKE_WEBHOOK_PRESSURE_OPENAI=PASTE_URL_HERE|' vreal-ai/.env
sed -i 's|^MAKE_WEBHOOK_PRESSURE_OPENAI=$|MAKE_WEBHOOK_PRESSURE_OPENAI=PASTE_URL_HERE|' vreal-ai/backend/.env

sed -i 's|^MAKE_WEBHOOK_PRESSURE_GEMINI=$|MAKE_WEBHOOK_PRESSURE_GEMINI=PASTE_URL_HERE|' vreal-ai/.env
sed -i 's|^MAKE_WEBHOOK_PRESSURE_GEMINI=$|MAKE_WEBHOOK_PRESSURE_GEMINI=PASTE_URL_HERE|' vreal-ai/backend/.env

sed -i 's|^MAKE_WEBHOOK_PRESSURE_GROK=$|MAKE_WEBHOOK_PRESSURE_GROK=PASTE_URL_HERE|' vreal-ai/.env
sed -i 's|^MAKE_WEBHOOK_PRESSURE_GROK=$|MAKE_WEBHOOK_PRESSURE_GROK=PASTE_URL_HERE|' vreal-ai/backend/.env

Then restart backend:
pkill -f uvicorn
cd /home/user/youtube-empire/vreal-ai/backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &

---

## TASK 7: PUSH EP001 ASSETS FROM LOCAL MACHINE
When Pedro has laptop access. The 17 EP001 asset files (~176MB) need to get to the cloud server.

On Pedro's laptop terminal:

cd /path/to/youtube-empire
git add output/ep001/
git commit -m "Add EP001 assets: voiceover, b-roll, music, SFX"
git push origin claude/improve-video-editing-mDM2y

If push fails (files too large), use Git LFS:
git lfs install
git lfs track "*.mp3" "*.mp4" "*.wav" "*.png" "*.jpg"
git add .gitattributes
git add output/ep001/
git commit -m "Add EP001 assets via LFS"
git push origin claude/improve-video-editing-mDM2y

If that still fails, zip and upload to Google Drive:
cd output
zip -r ep001-assets.zip ep001/
Then share the Google Drive link.

---

## TASK 8: SET UP MAKE.COM YOUTUBE UPLOAD SCENARIO
After YouTube channel is ready and EP001 is done.

Create Make.com scenario: "YouTube Upload — V-Real AI"
1. Trigger: Webhook (Custom webhook)
2. Module: YouTube → Upload a Video
   - Connect the @VRealAI YouTube account
   - Title: {{1.title}}
   - Description: {{1.description}}
   - Tags: {{1.tags}}
   - Category: 28 (Science & Technology)
   - Privacy: Private (we switch to public manually after review)
   - File: {{1.video_url}}
3. Webhook response: {"video_id": "{{youtube_video_id}}", "status": "uploaded"}
4. Turn ON, copy webhook URL

Give me: MAKE_WEBHOOK_UPLOAD=https://hook.us1.make.com/xxx

---

WHEN ALL DONE, REPORT BACK WITH:
1. YouTube channel URL (confirm settings updated)
2. Discord server invite link
3. The 3 Make.com pressure test webhook URLs
4. The YouTube upload webhook URL
5. Confirmation that API keys are in .env
6. Confirmation that EP001 assets are pushed (or Google Drive link)
