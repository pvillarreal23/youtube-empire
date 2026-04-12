import { NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // No backend endpoint for channels yet — return mock data directly
    const channels = [
      {
        id: '1',
        name: 'V-Real AI',
        handle: '@VRealAI',
        subs: '—',
        subsCount: 0,
        views: '0',
        viewsCount: 0,
        freq: '3x/week',
        color: 'from-blue-600 to-cyan-500',
        growth: '+12%',
        vids: '0',
        vidsCount: 0,
        ctr: '0%',
        revenue: '$0',
        revenueAmount: 0,
        nextVideo: 'Apr 2',
      },
      {
        id: '2',
        name: 'Cash Flow Code',
        subs: '—',
        subsCount: 0,
        views: '—',
        viewsCount: 0,
        freq: '2x/week',
        color: 'from-green-600 to-emerald-500',
        growth: '—',
        vids: '—',
        vidsCount: 0,
        ctr: '—',
        revenue: '—',
        revenueAmount: 0,
        nextVideo: 'Month 7',
      },
      {
        id: '3',
        name: 'Mind Shift',
        subs: '—',
        subsCount: 0,
        views: '—',
        viewsCount: 0,
        freq: '1x/week',
        color: 'from-purple-600 to-pink-500',
        growth: '—',
        vids: '—',
        vidsCount: 0,
        ctr: '—',
        revenue: '—',
        revenueAmount: 0,
        nextVideo: 'Month 13',
      },
    ];

    return NextResponse.json(channels);
  } catch {
    return NextResponse.json([]);
  }
}
