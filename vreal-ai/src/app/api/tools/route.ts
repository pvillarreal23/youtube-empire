import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const res = await fetch(`${BACKEND}/api/tools?${searchParams}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fallback mock data when backend is unavailable
    const tools = [
      { id: 'tool-1', name: 'Claude AI', category: 'text', icon: '🧠', status: 'active', description: 'Core AI reasoning — all agent tasks, scripting, research, and strategy run on Claude', website: 'https://anthropic.com', api_key_env: 'ANTHROPIC_API_KEY', managed_by: 'ceo-agent' },
      { id: 'tool-2', name: 'ElevenLabs', category: 'voice', icon: '🎙️', status: 'active', description: 'Studio-quality AI voiceover generation for all video scripts', website: 'https://elevenlabs.io', api_key_env: 'ELEVENLABS_API_KEY', managed_by: 'voice-director' },
      { id: 'tool-3', name: 'InVideo AI', category: 'video', icon: '🎬', status: 'active', description: 'Automated video assembly — B-roll, captions, and final export', website: 'https://invideo.io', api_key_env: null, managed_by: 'video-editor' },
      { id: 'tool-4', name: 'Canva Pro', category: 'image', icon: '🎨', status: 'active', description: 'Thumbnail design and brand asset creation with AI-assisted layouts', website: 'https://canva.com', api_key_env: null, managed_by: 'thumbnail-designer' },
      { id: 'tool-5', name: 'YouTube Studio', category: 'publishing', icon: '📺', status: 'active', description: 'Channel management, upload scheduling, and real-time analytics', website: 'https://studio.youtube.com', api_key_env: 'YOUTUBE_API_KEY', managed_by: 'ai-and-tech-channel-manager' },
      { id: 'tool-6', name: 'YouTube Analytics API', category: 'analytics', icon: '📊', status: 'active', description: 'Programmatic access to views, CTR, watch time, and revenue data', website: 'https://console.cloud.google.com', api_key_env: 'YOUTUBE_API_KEY', managed_by: 'analytics-vp' },
      { id: 'tool-7', name: 'Make.com', category: 'automation', icon: '⚡', status: 'active', description: 'Workflow automation — connects all tools and triggers automated pipelines', website: 'https://make.com', api_key_env: null, managed_by: 'automation-engineer' },
      { id: 'tool-8', name: 'Notion', category: 'text', icon: '📓', status: 'active', description: 'Editorial calendar, SOPs, and agent knowledge base', website: 'https://notion.so', api_key_env: 'NOTION_API_KEY', managed_by: 'project-manager' },
      { id: 'tool-9', name: 'Beehiiv', category: 'email', icon: '✉️', status: 'active', description: 'Newsletter publishing and subscriber management platform', website: 'https://beehiiv.com', api_key_env: 'BEEHIIV_API_KEY', managed_by: 'newsletter-strategist' },
      { id: 'tool-10', name: 'vidIQ', category: 'analytics', icon: '🔍', status: 'active', description: 'YouTube SEO research — keywords, competitor analysis, trending topics', website: 'https://vidiq.com', api_key_env: null, managed_by: 'seo-specialist' },
      { id: 'tool-11', name: 'GitHub', category: 'automation', icon: '🐙', status: 'active', description: 'Code repository for agent skill files, prompts, and automation scripts', website: 'https://github.com', api_key_env: 'GITHUB_TOKEN', managed_by: 'automation-engineer' },
      { id: 'tool-12', name: 'Vercel', category: 'automation', icon: '▲', status: 'active', description: 'Dashboard hosting and continuous deployment via GitHub Actions', website: 'https://vercel.com', api_key_env: 'VERCEL_TOKEN', managed_by: 'automation-engineer' },
    ];
    return NextResponse.json(tools);
  }
}
