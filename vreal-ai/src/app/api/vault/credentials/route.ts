import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const res = await fetch(`${BACKEND}/api/vault/credentials?${searchParams}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fallback mock data when backend is unavailable
    const vaultEntries = [
      // Workstations
      { id: 'ws-1', service: 'MacBook Pro M3', account_name: 'pedro@VRealAI.com', category: 'workstation', platform_url: '', notes: 'Primary development machine', api_key_hint: '', managed_by: 'operations-vp', status: 'active' },
      // API Keys
      { id: 'api-1', service: 'Anthropic Claude', account_name: 'pedro@VRealAI.com', category: 'api', platform_url: 'https://console.anthropic.com', notes: 'Claude API — all agent reasoning', api_key_hint: 'sk-ant-...', managed_by: 'ceo-agent', status: 'active' },
      { id: 'api-2', service: 'YouTube Data API', account_name: 'vrealai.creator@gmail.com', category: 'api', platform_url: 'https://console.cloud.google.com', notes: 'Analytics + upload automation', api_key_hint: 'AIza...', managed_by: 'analytics-vp', status: 'active' },
      { id: 'api-3', service: 'ElevenLabs', account_name: 'pedro@VRealAI.com', category: 'api', platform_url: 'https://elevenlabs.io', notes: 'AI voiceover generation', api_key_hint: 'xi-...', managed_by: 'voice-director', status: 'active' },
      { id: 'api-4', service: 'GitHub', account_name: 'pvillarreal23', category: 'api', platform_url: 'https://github.com', notes: 'Repo access token — deploy + code', api_key_hint: 'ghp_...', managed_by: 'automation-engineer', status: 'active' },
      // Tools
      { id: 'tool-1', service: 'Vercel', account_name: 'pedro@VRealAI.com', category: 'tool', platform_url: 'https://vercel.com', notes: 'Dashboard hosting + deploys', api_key_hint: 'vercel_...', managed_by: 'automation-engineer', status: 'active' },
      { id: 'tool-2', service: 'Notion', account_name: 'pedro@VRealAI.com', category: 'tool', platform_url: 'https://notion.so', notes: 'Editorial calendar + SOPs', api_key_hint: 'secret_...', managed_by: 'project-manager', status: 'active' },
      { id: 'tool-3', service: 'InVideo AI', account_name: 'pedro@VRealAI.com', category: 'tool', platform_url: 'https://invideo.io', notes: 'B-roll assembly + captions', api_key_hint: '', managed_by: 'video-editor', status: 'active' },
      { id: 'tool-4', service: 'Canva Pro', account_name: 'pedro@VRealAI.com', category: 'tool', platform_url: 'https://canva.com', notes: 'Thumbnail design + brand assets', api_key_hint: '', managed_by: 'thumbnail-designer', status: 'active' },
      // Social accounts
      { id: 'soc-1', service: 'YouTube Studio', account_name: '@TheAIEdge', category: 'social', platform_url: 'https://studio.youtube.com', notes: 'V-Real AI main channel', api_key_hint: '', managed_by: 'ai-and-tech-channel-manager', status: 'active' },
      { id: 'soc-2', service: 'Instagram', account_name: '@VRealAI', category: 'social', platform_url: 'https://instagram.com/VRealAI', notes: 'Clips + behind-the-scenes', api_key_hint: '', managed_by: 'social-media-manager', status: 'active' },
      { id: 'soc-3', service: 'X / Twitter', account_name: '@VRealAI', category: 'social', platform_url: 'https://x.com/VRealAI', notes: 'Thread repurposing + engagement', api_key_hint: '', managed_by: 'secretary-agent', status: 'active' },
      // Hosting
      { id: 'host-1', service: 'Vercel Pro', account_name: 'pedro@VRealAI.com', category: 'hosting', platform_url: 'https://vercel.com/dashboard', notes: 'Dashboard + Next.js app hosting', api_key_hint: '', managed_by: 'automation-engineer', status: 'active' },
    ];
    return NextResponse.json(vaultEntries);
  }
}
