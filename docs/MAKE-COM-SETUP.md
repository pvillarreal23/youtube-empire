# Make.com Scenario Blueprints for V-Real AI
## Complete setup guide — create these scenarios in Make.com

---

## SCENARIO 1: VOICEOVER GENERATION (ElevenLabs)
**Trigger**: Webhook → receives text + voice settings
**Output**: MP3 file saved to Google Drive, URL returned

### Steps to create:
1. New Scenario → Add **Webhooks > Custom webhook**
   - Name it: "VReal AI - Voiceover"
   - Copy the webhook URL → paste into .env as MAKE_WEBHOOK_VOICEOVER

2. Add module: **HTTP > Make a request**
   - URL: `https://api.elevenlabs.io/v1/text-to-speech/{{1.voice_id}}`
   - Method: POST
   - Headers:
     - `xi-api-key`: `sk_09ea908f52bbf89daaf97e48cbb0599153b1cf16a3e47529`
     - `Content-Type`: `application/json`
     - `Accept`: `audio/mpeg`
   - Body type: Raw
   - Content type: JSON
   - Request content:
     ```
     {
       "text": "{{1.text}}",
       "model_id": "{{1.model_id}}",
       "voice_settings": {
         "stability": {{1.stability}},
         "similarity_boost": {{1.similarity}},
         "style": {{1.style}},
         "use_speaker_boost": {{1.speaker_boost}}
       }
     }
     ```
   - Parse response: Yes
   - ⚠️ Set "Download file" to YES (this returns binary audio)

3. Add module: **Google Drive > Upload a file**
   - Folder: VReal-AI/audio/{{1.episode_id}}
   - File name: `{{1.filename}}`
   - Data: Output from HTTP module (the MP3 binary)

4. Add module: **Webhooks > Webhook response**
   - Status: 200
   - Body:
     ```
     {
       "status": "success",
       "file_url": "{{3.webContentLink}}",
       "file_id": "{{3.id}}",
       "filename": "{{1.filename}}"
     }
     ```

### Test payload (paste into webhook test):
```json
{
  "agent_id": "video-editor",
  "scenario": "voiceover",
  "episode_id": "ep001",
  "voice_id": "CjK4w2V6sbgFJY05zTGt",
  "model_id": "eleven_multilingual_v2",
  "stability": 0.65,
  "similarity": 0.75,
  "style": 0.0,
  "speaker_boost": false,
  "filename": "ep001-block1-test.mp3",
  "text": "Sarah Chen's phone buzzed at nine forty-seven AM. Emergency meeting."
}
```

---

## SCENARIO 2: FOOTAGE DOWNLOAD (Pexels)
**Trigger**: Webhook → receives search query + scene info
**Output**: Video file saved to Google Drive, URL returned

### Steps to create:
1. New Scenario → Add **Webhooks > Custom webhook**
   - Name it: "VReal AI - Footage"
   - Copy webhook URL → paste into .env as MAKE_WEBHOOK_VIDEO

2. Add module: **HTTP > Make a request**
   - URL: `https://api.pexels.com/videos/search`
   - Method: GET
   - Headers:
     - `Authorization`: `gFP6k1P1QCW6W19BCMugJ5GjEFaAL7pBiUZeP5Vj4eTzfKvgw8ntdPOe`
   - Query string:
     - `query`: `{{1.query}}`
     - `per_page`: `3`
     - `min_duration`: `{{1.min_duration}}`
     - `min_width`: `1920`
     - `orientation`: `landscape`
   - Parse response: Yes

3. Add module: **Array aggregator** (or use Set Variable)
   - Extract the first video's HD file URL:
   - `{{2.body.videos[1].video_files[1].link}}`

4. Add module: **HTTP > Get a file**
   - URL: the video file link from step 3
   - (This downloads the actual MP4)

5. Add module: **Google Drive > Upload a file**
   - Folder: VReal-AI/footage/{{1.episode_id}}
   - File name: `scene_{{1.scene_number}}_pexels.mp4`
   - Data: Output from HTTP Get a file

6. Add module: **Webhooks > Webhook response**
   - Body:
     ```
     {
       "status": "success",
       "file_url": "{{5.webContentLink}}",
       "file_id": "{{5.id}}",
       "scene_number": "{{1.scene_number}}"
     }
     ```

### Test payload:
```json
{
  "agent_id": "video-editor",
  "scenario": "footage",
  "episode_id": "ep001",
  "scene_number": "01",
  "query": "neural network dark visualization",
  "min_duration": 5
}
```

---

## SCENARIO 3: YOUTUBE UPLOAD
**Trigger**: Webhook → receives video file URL + metadata
**Output**: YouTube video ID returned

### Steps to create:
1. New Scenario → Add **Webhooks > Custom webhook**
   - Name it: "VReal AI - YouTube Upload"
   - Copy webhook URL → paste into .env as MAKE_WEBHOOK_UPLOAD

2. Add module: **HTTP > Get a file**
   - URL: `{{1.video_url}}` (Google Drive direct link to final MP4)

3. Add module: **YouTube > Upload a video**
   - Connection: Connect your @VRealAI YouTube account
   - Title: `{{1.title}}`
   - Description: `{{1.description}}`
   - Tags: `{{1.tags}}`
   - Category: `{{1.category_id}}`
   - Privacy: `{{1.privacy}}`
   - File: Output from HTTP module

4. Add module (optional): **HTTP > Get a file**
   - URL: `{{1.thumbnail_url}}` (thumbnail image)

5. Add module (optional): **YouTube > Set a thumbnail**
   - Video ID: from step 3
   - File: from step 4

6. Add module: **YouTube > Create a comment**
   - Video ID: from step 3
   - Text: `{{1.pinned_comment}}`

7. Add module: **Webhooks > Webhook response**
   - Body:
     ```
     {
       "status": "success",
       "video_id": "{{3.id}}",
       "video_url": "https://youtube.com/watch?v={{3.id}}"
     }
     ```

### Test payload:
```json
{
  "agent_id": "video-editor",
  "scenario": "upload",
  "episode_id": "ep001",
  "video_url": "https://drive.google.com/uc?id=FILE_ID",
  "title": "The AI Shift That's Coming for Marketers (Most Aren't Ready)",
  "description": "AI is transforming marketing...",
  "tags": "AI marketing,AI for marketers,AI 2026",
  "category_id": "27",
  "privacy": "public",
  "pinned_comment": "This entire video was researched, scripted, narrated, and produced using AI."
}
```

---

## SCENARIO 4: FULL EPISODE PRODUCTION (Master Orchestrator)
**Trigger**: Webhook → receives episode_id
**Output**: Calls scenarios 1-3 in sequence, produces complete episode

### Steps to create:
1. New Scenario → Add **Webhooks > Custom webhook**
   - Name it: "VReal AI - Full Production"
   - Copy webhook URL → this is your master trigger

2. Add module: **Iterator**
   - Array: `{{1.voiceover_blocks}}` (array of text blocks)

3. Inside iterator → **HTTP > Make a request**
   - URL: Your VOICEOVER webhook URL from Scenario 1
   - Method: POST
   - Body: each block's text + voice settings

4. Add module: **Iterator**
   - Array: `{{1.footage_scenes}}` (array of scene queries)

5. Inside iterator → **HTTP > Make a request**
   - URL: Your FOOTAGE webhook URL from Scenario 2
   - Method: POST
   - Body: each scene's query + settings

6. Add module: **Webhooks > Webhook response**
   - Return all file URLs for local FFmpeg assembly

### This scenario is OPTIONAL — you can also just trigger 1, 2, 3 individually.

---

## QUICK START — Get EP001 voiceover generated in 10 minutes:

1. Create Scenario 1 (Voiceover) in Make.com
2. Copy the webhook URL
3. Paste it into ~/youtube-empire/vreal-ai/backend/.env:
   ```
   MAKE_WEBHOOK_VOICEOVER=https://hook.us1.make.com/YOUR_URL_HERE
   ```
4. Restart the backend server
5. Call the API:
   ```
   curl -X POST http://localhost:8000/api/production/make/voiceover \
     -H "Content-Type: application/json" \
     -d '{"episode_id": "ep001", "block": 1}'
   ```

That's it. Make.com handles ElevenLabs, saves to Google Drive, returns the URL.
