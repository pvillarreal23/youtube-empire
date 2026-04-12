import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const res = await fetch(`${BACKEND}/api/social/accounts?${searchParams}`, {
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Backend ${res.status}`);
    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    // Fallback mock data when backend is unavailable
    const socialAccounts = [
      // YouTube
      { id: 'yt-1', platform: 'youtube', account_name: 'VRealAI', display_name: 'V-Real AI', channel_brand: 'V-Real AI — AI & Automation (@VRealAI)', managed_by: 'ai-and-tech-channel-manager', status: 'active', followers: '—' },
      { id: 'yt-2', platform: 'youtube', account_name: 'CashFlowCode', display_name: 'Cash Flow Code', channel_brand: 'Cash Flow Code — Business & Finance', managed_by: 'finance-and-business-channel-manager', status: 'pending_creation', followers: '—' },
      { id: 'yt-3', platform: 'youtube', account_name: 'MindShiftYT', display_name: 'Mind Shift', channel_brand: 'Mind Shift — Psychology & Behavior', managed_by: 'psychology-and-behavior-channel-manager', status: 'pending_creation', followers: '—' },
      // Instagram
      { id: 'ig-1', platform: 'instagram', account_name: 'VRealAI', display_name: 'V-Real AI', channel_brand: 'V-Real AI — AI & Automation', managed_by: 'social-media-manager', status: 'active', followers: '—' },
      { id: 'ig-2', platform: 'instagram', account_name: 'cashflowcode', display_name: 'Cash Flow Code', channel_brand: 'Cash Flow Code — Business & Finance', managed_by: 'social-media-manager', status: 'pending_creation', followers: '—' },
      { id: 'ig-3', platform: 'instagram', account_name: 'mindshift.io', display_name: 'Mind Shift', channel_brand: 'Mind Shift — Psychology & Behavior', managed_by: 'social-media-manager', status: 'pending_creation', followers: '—' },
      // TikTok
      { id: 'tt-1', platform: 'tiktok', account_name: 'VRealAI', display_name: 'V-Real AI', channel_brand: 'V-Real AI — AI & Automation', managed_by: 'shorts-and-clips-agent', status: 'active', followers: '—' },
      { id: 'tt-2', platform: 'tiktok', account_name: 'cashflowcode', display_name: 'Cash Flow Code', channel_brand: 'Cash Flow Code — Business & Finance', managed_by: 'shorts-and-clips-agent', status: 'pending_creation', followers: '—' },
      // Twitter/X
      { id: 'tw-1', platform: 'twitter', account_name: 'VRealAI', display_name: 'V-Real AI', channel_brand: 'V-Real AI — AI & Automation', managed_by: 'secretary-agent', status: 'active', followers: '—' },
      { id: 'tw-2', platform: 'twitter', account_name: 'cashflowcode', display_name: 'Cash Flow Code', channel_brand: 'Cash Flow Code — Business & Finance', managed_by: 'secretary-agent', status: 'pending_creation', followers: '—' },
      // LinkedIn
      { id: 'li-1', platform: 'linkedin', account_name: 'VRealAI', display_name: 'V-Real AI', channel_brand: 'V-Real AI — AI & Automation', managed_by: 'community-manager', status: 'active', followers: '—' },
    ];
    return NextResponse.json(socialAccounts);
  }
}
