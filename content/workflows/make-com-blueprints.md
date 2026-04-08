# V-Real AI — Make.com Automation Blueprints

## Overview

These are Make.com scenario templates for automating the V-Real AI content
pipeline. Each blueprint describes the trigger, modules, and connections
you need to build in Make.com.

You need:
- Make.com account (free tier works to start)
- Anthropic API key (for Claude modules)
- YouTube account + Google API connection
- Email provider (ConvertKit, Mailchimp, or Beehiiv)
- Social accounts connected (Twitter/X, Instagram, TikTok, LinkedIn)

---

## Blueprint 1: Content Pipeline (Topic → Script → SEO Package)

**What it does:** You submit a topic → Make.com runs it through Research,
Hook, Scriptwriter, and SEO agents automatically → outputs a complete
video package to Google Docs.

### Scenario Setup

```
TRIGGER: Webhook (Custom)
   ↓
MODULE 1: HTTP — Claude API (Researcher Agent)
   → System prompt: [Senior Researcher prompt]
   → User message: "Research this topic for V-Real AI: {{topic}}"
   → Output: research_text
   ↓
MODULE 2: HTTP — Claude API (Hook Specialist Agent)
   → System prompt: [Hook Specialist prompt]
   → User message: "Create 3 hooks for: {{topic}}. Research: {{research_text}}"
   → Output: hooks_text
   ↓
MODULE 3: HTTP — Claude API (Scriptwriter Agent)
   → System prompt: [Scriptwriter prompt]
   → User message: "Write script. Topic: {{topic}}. Hook: {{hooks_text}}. Research: {{research_text}}"
   → Output: script_text
   ↓
MODULE 4: HTTP — Claude API (SEO Specialist Agent)
   → System prompt: [SEO Specialist prompt]
   → User message: "Create SEO package. Topic: {{topic}}. Script title from: {{script_text}}"
   → Output: seo_text
   ↓
MODULE 5: Google Docs — Create Document
   → Title: "V-Real AI Script — {{topic}}"
   → Content: Combine research_text + hooks_text + script_text + seo_text
   ↓
MODULE 6: Slack/Email — Send Notification
   → "Your script package for '{{topic}}' is ready: {{google_doc_url}}"
```

### Claude API HTTP Module Settings

For each Claude module, use:
```
URL: https://api.anthropic.com/v1/messages
Method: POST
Headers:
  x-api-key: {{anthropic_api_key}}
  anthropic-version: 2023-06-01
  content-type: application/json

Body:
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 4096,
  "system": "{{agent_system_prompt}}",
  "messages": [
    {"role": "user", "content": "{{your_prompt_here}}"}
  ]
}
```

Parse response: `{{body.content[0].text}}`

---

## Blueprint 2: Auto-Publish YouTube Metadata

**What it does:** When you upload a video to YouTube, this auto-generates
and applies the SEO-optimized title, description, tags, and chapters.

```
TRIGGER: YouTube — Watch New Video Upload
   ↓
MODULE 1: HTTP — Claude API (SEO Agent)
   → "Create SEO package for this video title: {{youtube.title}}"
   → Output: seo_package (title, description, tags)
   ↓
MODULE 2: Text Parser — Extract title, description, tags from seo_package
   ↓
MODULE 3: YouTube — Update Video
   → Title: {{optimized_title}}
   → Description: {{optimized_description}}
   → Tags: {{optimized_tags}}
   ↓
MODULE 4: Slack/Email — Notify
   → "SEO applied to: {{video_title}}"
```

---

## Blueprint 3: Auto-Repurpose into Shorts Scripts

**What it does:** Takes a finished script from Google Docs and generates
3 Shorts scripts + social media posts.

```
TRIGGER: Google Docs — Watch for New Document (in Scripts folder)
   ↓
MODULE 1: Google Docs — Get Document Content
   → Output: full_script
   ↓
MODULE 2: HTTP — Claude API (Shorts Agent)
   → "Extract 3 short-form clips from this script: {{full_script}}"
   → Output: shorts_scripts
   ↓
MODULE 3: HTTP — Claude API (Social Media Agent)
   → "Create social posts for: {{full_script}}"
   → Output: social_posts
   ↓
MODULE 4: Google Sheets — Add Row (Content Calendar)
   → Date, Video Title, Short 1 script, Short 2 script, Short 3 script
   ↓
MODULE 5: Google Sheets — Add Row (Social Calendar)
   → Platform, Post Content, Scheduled Date
```

---

## Blueprint 4: Weekly Newsletter Auto-Draft

**What it does:** Every Friday, pulls your latest video data and drafts
a newsletter.

```
TRIGGER: Schedule — Every Friday at 9am
   ↓
MODULE 1: YouTube — List Videos (last 7 days)
   → Output: latest_videos (title, url, description)
   ↓
MODULE 2: HTTP — Claude API (Newsletter Agent)
   → "Write newsletter for this week's V-Real AI content:
      Videos published: {{latest_videos}}
      Include: 3 subject line options, preview text, full body, CTA"
   → Output: newsletter_draft
   ↓
MODULE 3: ConvertKit/Mailchimp — Create Draft
   → Subject: {{subject_line_option_1}}
   → Body: {{newsletter_body}}
   ↓
MODULE 4: Slack/Email — Notify
   → "Newsletter draft ready for review"
```

---

## Blueprint 5: Trend Alert → Video Idea Pipeline

**What it does:** Monitors Google Trends and AI news, generates
video ideas when something spikes.

```
TRIGGER: Schedule — Daily at 8am
   ↓
MODULE 1: Google Trends — Get Trending Topics (category: Technology)
   → Output: trending_topics
   ↓
MODULE 2: RSS — Fetch latest from AI news feeds
   → Sources: The Verge AI, TechCrunch AI, AI News
   → Output: latest_news
   ↓
MODULE 3: HTTP — Claude API (Trend Researcher)
   → "Analyze these trends and news for V-Real AI video opportunities:
      Trends: {{trending_topics}}
      News: {{latest_news}}
      Give me top 3 video ideas with: title, keyword, why NOW, urgency score (1-10)"
   → Output: video_ideas
   ↓
MODULE 4: Google Sheets — Add Rows (Ideas Backlog)
   → Date, Idea, Keyword, Urgency Score
   ↓
MODULE 5 (conditional): IF urgency_score > 8
   → Slack/Email: "URGENT video opportunity: {{idea}}"
```

---

## Blueprint 6: Comment Response Bot

**What it does:** Monitors YouTube comments, drafts responses
for high-value comments, sends for your approval.

```
TRIGGER: Schedule — Every 2 hours
   ↓
MODULE 1: YouTube — List New Comments
   → Filter: comments with questions or > 5 likes
   → Output: comments_to_respond
   ↓
MODULE 2: Iterator — For each comment
   ↓
MODULE 3: HTTP — Claude API (Community Manager)
   → "You are the Community Manager for V-Real AI. Draft a reply to this
      YouTube comment. Be helpful, authentic, and encourage engagement.
      Never be generic. Comment: {{comment.text}}"
   → Output: draft_reply
   ↓
MODULE 4: Google Sheets — Add Row (Pending Replies)
   → Video, Comment, Draft Reply, Approve Link
   ↓
MODULE 5: Slack/Email — "{{count}} comment replies ready for review"
```

---

## Getting Started

### Step 1: Start with Blueprint 1
The content pipeline is the highest-value automation. It turns a
single topic into a complete video package in ~2 minutes.

### Step 2: Add Blueprint 4
The newsletter auto-draft saves you hours weekly and keeps your
email list engaged.

### Step 3: Scale with Blueprints 2, 3, 5, 6
Add these as your channel grows and publishing frequency increases.

### Cost Estimate
- Make.com: Free tier = 1,000 operations/month (enough for ~20 video packages)
- Claude API: ~$0.50-2.00 per full video package (4 agent calls)
- Total: Under $50/month for a fully automated content pipeline
