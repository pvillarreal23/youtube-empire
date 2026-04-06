"use client";

import { useEffect, useState, useCallback } from "react";
import { RefreshCw, DollarSign, Zap, Activity, Clock } from "lucide-react";

interface ElevenLabsData {
  used: number;
  limit: number;
  percent: number;
  resetDate: string | null;
}

interface CostsData {
  elevenlabs: ElevenLabsData | null;
  timestamp: string;
}

const FIXED_COSTS = [
  { name: "Claude Max", category: "Subscription", cost: 200, period: "mo", status: "ACTIVE" },
  { name: "ElevenLabs Creator", category: "TTS", cost: 22, period: "mo", status: "ACTIVE" },
  { name: "Vercel", category: "Hosting", cost: 20, period: "mo", status: "ACTIVE" },
  { name: "Make.com", category: "Automation", cost: 29, period: "mo", status: "ACTIVE" },
  { name: "Claude API", category: "Usage", cost: 9, period: "mo", status: "ACTIVE", approx: true },
  { name: "OpenAI API", category: "Usage", cost: 15, period: "mo", status: "ACTIVE", approx: true },
];

const PENDING_COSTS = [
  { name: "Kling", cost: 30 },
  { name: "Screen Studio", cost: 29 },
  { name: "Ideogram", cost: 20 },
  { name: "TubeBuddy", cost: 49 },
  { name: "Canva", cost: 17 },
  { name: "Flux2", cost: 5, approx: true },
];

const TOTAL_MONTHLY = 295;
const TOTAL_YEARLY = TOTAL_MONTHLY * 12;
const PENDING_TOTAL = 150;

function formatNumber(n: number) {
  return n.toLocaleString();
}

function daysUntil(isoDate: string | null): number | null {
  if (!isoDate) return null;
  const diff = new Date(isoDate).getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

function formatResetDate(isoDate: string | null): string {
  if (!isoDate) return "—";
  return new Date(isoDate).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function CostsPage() {
  const [data, setData] = useState<CostsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const res = await fetch("/api/costs/live");
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch {
      // silently fail
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => fetchData(), 60_000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const el = data?.elevenlabs;
  const lastUpdated = data?.timestamp
    ? new Date(data.timestamp).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="px-6 py-4 border-b border-white/5 flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-xl font-semibold text-white">Cost Control</h2>
          {lastUpdated && (
            <p className="text-xs text-white/30 mt-0.5">Last updated {lastUpdated}</p>
          )}
        </div>
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-3 py-2 bg-white/[0.03] border border-white/10 rounded-lg text-xs text-white/50 hover:text-white hover:border-white/20 transition-all disabled:opacity-40"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Total confirmed */}
          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <DollarSign className="w-4 h-4 text-[#00D4FF]" />
              <span className="text-xs text-white/40 font-medium">Total Monthly</span>
            </div>
            <p className="text-2xl font-bold text-white">${TOTAL_MONTHLY}</p>
            <p className="text-xs text-white/30 mt-1">Confirmed</p>
          </div>

          {/* Claude API */}
          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-purple-400" />
              <span className="text-xs text-white/40 font-medium">Claude API</span>
            </div>
            <p className="text-2xl font-bold text-white">~$9</p>
            <p className="text-xs text-white/30 mt-1">per month</p>
          </div>

          {/* OpenAI API */}
          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-4 h-4 text-green-400" />
              <span className="text-xs text-white/40 font-medium">OpenAI API</span>
            </div>
            <p className="text-2xl font-bold text-white">~$15</p>
            <p className="text-xs text-white/30 mt-1">per month</p>
          </div>

          {/* ElevenLabs live */}
          <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2 h-2 rounded-full bg-[#00D4FF] animate-pulse" />
              <span className="text-xs text-white/40 font-medium">ElevenLabs</span>
            </div>
            {loading ? (
              <div className="h-8 w-24 bg-white/5 rounded animate-pulse" />
            ) : el ? (
              <>
                <p className="text-2xl font-bold text-[#00D4FF]">{el.percent}%</p>
                <p className="text-xs text-white/30 mt-1">
                  {formatNumber(el.used)} / {formatNumber(el.limit)} chars
                </p>
              </>
            ) : (
              <p className="text-sm text-white/30">Unavailable</p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Fixed Costs Table */}
          <div className="lg:col-span-2 bg-white/[0.02] border border-white/5 rounded-xl overflow-hidden">
            <div className="px-5 py-3.5 border-b border-white/5">
              <h3 className="text-sm font-semibold text-white">Fixed Stack</h3>
            </div>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="px-5 py-2.5 text-left text-xs text-white/30 font-medium">Service</th>
                  <th className="px-5 py-2.5 text-left text-xs text-white/30 font-medium">Category</th>
                  <th className="px-5 py-2.5 text-right text-xs text-white/30 font-medium">Cost</th>
                  <th className="px-5 py-2.5 text-center text-xs text-white/30 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {FIXED_COSTS.map((row) => (
                  <tr key={row.name} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                    <td className="px-5 py-3 text-white font-medium">{row.name}</td>
                    <td className="px-5 py-3 text-white/40">{row.category}</td>
                    <td className="px-5 py-3 text-right text-[#00D4FF] font-medium">
                      {row.approx ? "~" : ""}${row.cost}/mo
                    </td>
                    <td className="px-5 py-3 text-center">
                      <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        ACTIVE
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-white/[0.02]">
                  <td className="px-5 py-3 text-white font-bold" colSpan={2}>TOTAL</td>
                  <td className="px-5 py-3 text-right">
                    <span className="text-[#00D4FF] font-bold">${TOTAL_MONTHLY}/mo</span>
                    <span className="text-white/30 text-xs ml-2">${formatNumber(TOTAL_YEARLY)}/yr</span>
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>

          {/* Right column */}
          <div className="space-y-4">
            {/* ElevenLabs Live Card */}
            <div className="bg-white/[0.02] border border-white/5 rounded-xl p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-white">ElevenLabs Usage</h3>
                <span className="flex items-center gap-1 text-[10px] text-[#00D4FF]">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#00D4FF] animate-pulse" />
                  LIVE
                </span>
              </div>
              {loading ? (
                <div className="space-y-2">
                  <div className="h-2 bg-white/5 rounded-full animate-pulse" />
                  <div className="h-4 w-32 bg-white/5 rounded animate-pulse" />
                </div>
              ) : el ? (
                <>
                  <div className="mb-2">
                    <div className="flex justify-between text-xs mb-1.5">
                      <span className="text-white/40">{formatNumber(el.used)} used</span>
                      <span className="text-white/40">{formatNumber(el.limit)} limit</span>
                    </div>
                    <div className="w-full bg-white/5 rounded-full h-2">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          el.percent > 80
                            ? "bg-red-400"
                            : el.percent > 60
                            ? "bg-[#FFB347]"
                            : "bg-[#00D4FF]"
                        }`}
                        style={{ width: `${Math.min(el.percent, 100)}%` }}
                      />
                    </div>
                    <p className="text-right text-xs text-white/30 mt-1">{el.percent}%</p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-white/40 mt-3">
                    <Clock className="w-3.5 h-3.5 shrink-0" />
                    <span>
                      Resets {formatResetDate(el.resetDate)}
                      {daysUntil(el.resetDate) !== null && (
                        <span className="text-white/25"> ({daysUntil(el.resetDate)}d)</span>
                      )}
                    </span>
                  </div>
                </>
              ) : (
                <p className="text-xs text-white/30">API key not configured or unavailable</p>
              )}
            </div>

            {/* Pending Stack */}
            <div className="bg-white/[0.02] border border-[#FFB347]/20 rounded-xl overflow-hidden">
              <div className="px-5 py-3.5 border-b border-white/5 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-[#FFB347]">Pending Stack</h3>
                <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-[#FFB347]/10 text-[#FFB347] border border-[#FFB347]/20">
                  PENDING
                </span>
              </div>
              <div className="p-5 space-y-2">
                {PENDING_COSTS.map((item) => (
                  <div key={item.name} className="flex justify-between text-xs">
                    <span className="text-white/40">{item.name}</span>
                    <span className="text-[#FFB347]/70">
                      {item.approx ? "~" : ""}${item.cost}/mo
                    </span>
                  </div>
                ))}
                <div className="pt-3 mt-3 border-t border-white/5">
                  <p className="text-xs text-[#FFB347]/60">
                    Full launch stack adds{" "}
                    <span className="text-[#FFB347] font-semibold">~${PENDING_TOTAL}/mo</span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
