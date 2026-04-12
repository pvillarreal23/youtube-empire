"use client";
import DashboardLayout, { Zone, DashboardData, API_URL, getAgentAvatar, getHumanName, getAgentTier, TIER_STYLES, DEPT_COLORS, AGENT_PERSONAS } from "./DashboardLayout";
import { useState, useRef, useEffect } from "react";
import type { AgentInfo, Thread, ThreadMsg, ActivityData, FeedMsg } from "./DashboardLayout";
import { Send, Bot, User, ChevronRight, Plus, Play, CheckCircle, AlertTriangle, Activity, XCircle, CircleDot, MessageSquare, Globe, KeyRound, Mail, Sparkles, FileText, TrendingUp, BarChart3 } from "lucide-react";

export default function NewDashboard() {
  return (
    <DashboardLayout>
      {(zone, data) => {
        switch (zone) {
          case "mission": return <MissionControl data={data} />;
          case "content": return <ContentEngine data={data} />;
          case "workforce": return <AIWorkforce data={data} />;
          case "growth": return <GrowthHub data={data} />;
          case "vault": return <VaultZone data={data} />;
          default: return <MissionControl data={data} />;
        }
      }}
    </DashboardLayout>
  );
}

// ============ MISSION CONTROL ============
function MissionControl({ data }: { data: DashboardData }) {
  return (
    <div className="space-y-6">
      {/* Autopilot status */}
      {data.activityData && (
        <div className="grid grid-cols-4 gap-3">
          <StatCard label="Agents Online" value={`${data.activityData.total_agents}`} icon={<Bot className="w-4 h-4 text-purple-400" />} accent="purple" />
          <StatCard label="Completed Today" value={`${data.activityData.completed_today}`} icon={<CheckCircle className="w-4 h-4 text-green-400" />} accent="green" />
          <StatCard label="Running Now" value={`${data.activityData.running_count}`} icon={<Play className="w-4 h-4 text-blue-400" />} accent="blue" />
          <StatCard label="Needs Review" value={`${data.activityData.pending_escalations}`} icon={<AlertTriangle className="w-4 h-4 text-amber-400" />} accent="amber" />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent activity */}
        <div className="lg:col-span-2 bg-white/[0.03] border border-white/10 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Recent Activity</h3>
            <span className="text-[10px] text-white/20">{data.activityData?.recent_runs?.length || 0} tasks</span>
          </div>
          <div className="max-h-[350px] overflow-y-auto divide-y divide-white/5">
            {data.activityData?.recent_runs?.map(r => {
              const tier = getAgentTier(r.agent_id);
              const ts = TIER_STYLES[tier];
              return (
                <div key={r.id} className="flex items-center gap-3 px-5 py-3 hover:bg-white/[0.02]">
                  <div className={`w-8 h-8 rounded-full overflow-hidden ring-2 ${ts.ring} shrink-0`}>
                    <img src={getAgentAvatar(r.agent_id)} className="w-full h-full object-cover" alt="" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold">{getHumanName(r.agent_id)}</span>
                      <span className={`text-[7px] px-1.5 py-0 rounded-full border font-medium ${ts.badge}`}>{tier}</span>
                    </div>
                    <p className="text-[10px] text-white/50 truncate">{r.task_name}</p>
                    {r.summary && <p className="text-[10px] text-white/25 truncate mt-0.5">{r.summary}</p>}
                  </div>
                  <span className={`text-[8px] px-1.5 py-0.5 rounded-full ${r.status === "complete" ? "bg-green-500/20 text-green-400" : r.status === "failed" ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"}`}>{r.status}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Escalations */}
        <div className="bg-white/[0.03] border border-white/10 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
            <h3 className="text-sm font-semibold flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-400" /> Escalations</h3>
          </div>
          <div className="p-4 space-y-2 max-h-[350px] overflow-y-auto">
            {(!data.activityData?.escalations || data.activityData.escalations.length === 0) ? (
              <p className="text-xs text-white/20 text-center py-8">All clear — no escalations</p>
            ) : data.activityData.escalations.map(e => (
              <div key={e.id} className="bg-amber-500/5 border border-amber-500/20 rounded-lg p-3">
                <p className="text-xs text-white/60">{e.reason}</p>
                <p className="text-[10px] text-white/25 mt-1">{getHumanName(e.agent_id)}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Tools */}
      <div>
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Sparkles className="w-4 h-4 text-purple-400" /> AI Tools</h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {[
            { name: "Trend Scanner", icon: "🔍", desc: "Find trending topics" },
            { name: "Competitor Spy", icon: "🕵️", desc: "Analyze rival channels" },
            { name: "Title Generator", icon: "✨", desc: "CTR-optimized titles" },
            { name: "Script Doctor", icon: "🩺", desc: "Improve any script" },
            { name: "Content Audit", icon: "📊", desc: "Full performance review" },
            { name: "Growth Plan", icon: "🚀", desc: "90-day strategy" },
            { name: "Newsletter Brief", icon: "✉️", desc: "Draft this week's issue" },
            { name: "Monetization Scan", icon: "💎", desc: "Find revenue gaps" },
          ].map(t => (
            <div key={t.name} className="bg-white/[0.03] border border-white/5 hover:border-white/20 rounded-xl p-3 cursor-pointer transition-all group">
              <span className="text-lg">{t.icon}</span>
              <p className="text-xs font-semibold mt-1.5 group-hover:text-white transition-colors">{t.name}</p>
              <p className="text-[10px] text-white/25">{t.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, icon, accent }: { label: string; value: string; icon: React.ReactNode; accent: string }) {
  return (
    <div className={`bg-${accent}-500/5 border border-${accent}-500/20 rounded-xl p-4`}>
      {icon}
      <p className="text-2xl font-bold mt-2">{value}</p>
      <p className="text-xs text-white/40">{label}</p>
    </div>
  );
}

// ============ CONTENT ENGINE ============
function ContentEngine({ data }: { data: DashboardData }) {
  const channels = [
    { name: "V-Real AI", color: "from-blue-600 to-cyan-500", subs: "0", freq: "3x/week" },
    { name: "Cash Flow Code", color: "from-green-600 to-emerald-500", subs: "—", freq: "2x/week" },
    { name: "Mind Shift", color: "from-purple-600 to-pink-500", subs: "—", freq: "1x/week" },
  ];

  return (
    <div className="space-y-6">
      {/* Channels */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {channels.map(c => (
          <div key={c.name} className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
            <div className={`w-full h-1.5 rounded-full bg-gradient-to-r ${c.color} mb-4`} />
            <h3 className="font-semibold mb-2">{c.name}</h3>
            <div className="grid grid-cols-2 gap-y-2 text-sm">
              <div><span className="text-white/40 text-xs">Subscribers</span><p className="font-medium">{c.subs}</p></div>
              <div><span className="text-white/40 text-xs">Frequency</span><p className="font-medium">{c.freq}</p></div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent threads related to content */}
      <div className="bg-white/[0.03] border border-white/10 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5">
          <h3 className="text-sm font-semibold">Content Threads</h3>
        </div>
        <div className="divide-y divide-white/5">
          {data.threads.slice(0, 5).map(t => (
            <div key={t.id} className="flex items-center gap-3 px-5 py-3 hover:bg-white/[0.02]">
              <div className="flex -space-x-1.5">
                {t.participants?.slice(0, 3).map(pid => (
                  <img key={pid} src={getAgentAvatar(pid)} className={`w-7 h-7 rounded-full object-cover ring-1 ring-[#0a0a0a] ring-2 ${TIER_STYLES[getAgentTier(pid)].ring}`} alt="" />
                ))}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{t.subject}</p>
                <p className="text-[10px] text-white/25">{t.participants?.length} agents</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============ AI WORKFORCE ============
function AIWorkforce({ data }: { data: DashboardData }) {
  const [prompt, setPrompt] = useState("");
  const [sending, setSending] = useState(false);

  const sendToAgents = async () => {
    if (!prompt.trim()) return;
    setSending(true);
    try {
      const ceo = data.agents.find(a => a.id.includes("ceo"));
      await fetch(`${API_URL}/api/threads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject: prompt.slice(0, 60), recipient_agent_ids: [ceo?.id || "ceo-agent"], content: prompt }),
      });
      setPrompt("");
    } catch (e) { console.error(e); }
    setSending(false);
  };

  return (
    <div className="space-y-6">
      {/* Command input */}
      <div className="bg-gradient-to-r from-purple-500/5 to-blue-500/5 border border-purple-500/20 rounded-xl p-5">
        <div className="flex items-center gap-3 mb-3">
          <Bot className="w-5 h-5 text-purple-400" />
          <h3 className="text-sm font-semibold">Command Your Team</h3>
          <span className="text-[10px] text-white/25">→ CEO delegates automatically</span>
        </div>
        <div className="flex gap-2">
          <input type="text" value={prompt} onChange={e => setPrompt(e.target.value)} onKeyDown={e => { if (e.key === "Enter") sendToAgents(); }}
            placeholder="What do you need your team to do?" className="flex-1 bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm text-white placeholder-white/25 focus:outline-none focus:border-purple-500/50" />
          <button onClick={sendToAgents} disabled={sending || !prompt.trim()} className="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg text-sm font-medium flex items-center gap-2">
            <Send className="w-4 h-4" /> {sending ? "..." : "Send"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Agent roster */}
        <div className="lg:col-span-2 bg-white/[0.03] border border-white/10 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-white/5 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Agent Roster ({data.agents.length})</h3>
          </div>
          <div className="max-h-[450px] overflow-y-auto divide-y divide-white/5">
            {data.activityData?.agent_statuses?.map(a => {
              const tier = getAgentTier(a.id);
              const ts = TIER_STYLES[tier];
              const dept = DEPT_COLORS[a.department] || DEPT_COLORS.general;
              return (
                <div key={a.id} className="flex items-center gap-3 px-5 py-2.5 hover:bg-white/[0.02]">
                  <div className={`w-9 h-9 rounded-full overflow-hidden ring-2 ${ts.ring} shrink-0`}>
                    <img src={getAgentAvatar(a.id)} className="w-full h-full object-cover" alt="" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold">{getHumanName(a.id) || a.name}</span>
                      <span className={`text-[7px] px-1.5 py-0 rounded-full border font-medium ${ts.badge}`}>{tier}</span>
                      <span className={`w-1.5 h-1.5 rounded-full ${a.status === "working" ? "bg-green-400 animate-pulse" : "bg-white/15"}`} />
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] text-white/40">{a.role}</span>
                      <span className="text-[10px] text-white/15">·</span>
                      <span className="text-[9px] flex items-center gap-0.5"><span className={`w-1 h-1 rounded-full ${dept.dot}`} /><span className="text-white/25">{dept.label}</span></span>
                    </div>
                    <p className="text-[10px] text-white/20 truncate">{a.current_task}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Feed */}
        <div className="bg-white/[0.03] border border-white/10 rounded-xl overflow-hidden">
          <div className="px-5 py-3 border-b border-white/5">
            <h3 className="text-sm font-semibold flex items-center gap-2"><MessageSquare className="w-4 h-4 text-cyan-400" /> Live Feed</h3>
          </div>
          <div className="max-h-[450px] overflow-y-auto p-3 space-y-2">
            {data.feedMessages.slice(0, 15).map(m => {
              const tier = m.agent_id !== "pedro" ? getAgentTier(m.agent_id) : null;
              const ts = tier ? TIER_STYLES[tier] : null;
              return (
                <div key={m.id} className="bg-white/[0.02] border border-white/5 rounded-lg p-2.5">
                  <div className="flex items-center gap-2 mb-1">
                    <img src={m.agent_id === "pedro" ? "/avatars/pedro.jpg" : getAgentAvatar(m.agent_id)} className={`w-5 h-5 rounded-full object-cover ring-1 ${ts?.ring || "ring-purple-500/60"}`} alt="" />
                    <span className="text-[10px] font-semibold">{m.agent_id === "pedro" ? "Pedro" : getHumanName(m.agent_id)}</span>
                    {ts && <span className={`text-[7px] px-1 py-0 rounded-full border ${ts.badge}`}>{tier}</span>}
                  </div>
                  <p className="text-[10px] text-white/50 leading-relaxed line-clamp-3">{m.content}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============ GROWTH HUB ============
function GrowthHub({ data }: { data: DashboardData }) {
  const [socialAccounts, setSocialAccounts] = useState<any[]>([]);
  useEffect(() => {
    fetch(`${API_URL}/api/social/accounts`).then(r => r.json()).then(setSocialAccounts).catch(() => {});
  }, []);

  const platformEmojis: Record<string, string> = { youtube: "📺", instagram: "📸", facebook: "📘", tiktok: "📱", snapchat: "👻", twitter: "𝕏", linkedin: "💼", threads: "🧵" };
  const byPlatform: Record<string, number> = {};
  socialAccounts.forEach(a => { byPlatform[a.platform] = (byPlatform[a.platform] || 0) + 1; });

  return (
    <div className="space-y-6">
      {/* Platform overview */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
        {Object.entries(platformEmojis).map(([p, emoji]) => (
          <div key={p} className="bg-white/[0.03] border border-white/5 rounded-xl p-3 text-center">
            <span className="text-lg">{emoji}</span>
            <p className="text-xs font-semibold mt-1 capitalize">{p}</p>
            <p className="text-[10px] text-white/30">{byPlatform[p] || 0} accounts</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Newsletter */}
        <div className="bg-gradient-to-b from-cyan-500/5 to-transparent border border-cyan-500/20 rounded-xl p-5">
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-4"><Mail className="w-4 h-4 text-cyan-400" /> Newsletter</h3>
          <div className="space-y-2">
            {["Write Weekly Issue", "Welcome Sequence", "Grow Subscriber List", "A/B Test Plan"].map(item => (
              <div key={item} className="flex items-center gap-2 px-3 py-2 bg-white/5 border border-white/5 rounded-lg cursor-pointer hover:border-cyan-500/30 transition-all">
                <ChevronRight className="w-3 h-3 text-cyan-400" />
                <span className="text-xs">{item}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Social quick stats */}
        <div className="bg-white/[0.03] border border-white/10 rounded-xl p-5">
          <h3 className="text-sm font-semibold flex items-center gap-2 mb-4"><Globe className="w-4 h-4 text-blue-400" /> Social Media</h3>
          <p className="text-3xl font-bold">{socialAccounts.length}</p>
          <p className="text-xs text-white/40 mb-3">accounts across {Object.keys(byPlatform).length} platforms</p>
          <p className="text-[10px] text-white/25">31 cross-followers per account on day 1</p>
          <p className="text-[10px] text-green-400 mt-2">{socialAccounts.filter(a => a.status === "active").length} active · {socialAccounts.filter(a => a.status === "pending_creation").length} pending creation</p>
        </div>
      </div>
    </div>
  );
}

// ============ VAULT ============
function VaultZone({ data }: { data: DashboardData }) {
  const [entries, setEntries] = useState<any[]>([]);
  useEffect(() => {
    fetch(`${API_URL}/api/vault/credentials`).then(r => r.json()).then(setEntries).catch(() => {});
  }, []);

  const categories = ["channel", "workstation", "social", "api", "tool", "hosting"];
  const catLabels: Record<string, { label: string; emoji: string }> = {
    channel: { label: "Channels", emoji: "📺" },
    workstation: { label: "Workstations", emoji: "🖥️" },
    social: { label: "Social Media", emoji: "📱" },
    api: { label: "API Keys", emoji: "🔑" },
    tool: { label: "Tools", emoji: "🔧" },
    hosting: { label: "Hosting", emoji: "☁️" },
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {categories.map(cat => {
          const count = entries.filter(e => e.category === cat).length;
          const info = catLabels[cat] || { label: cat, emoji: "📄" };
          return (
            <div key={cat} className="bg-white/[0.03] border border-white/10 rounded-xl p-4 text-center">
              <span className="text-lg">{info.emoji}</span>
              <p className="text-xl font-bold mt-1">{count}</p>
              <p className="text-[10px] text-white/40">{info.label}</p>
            </div>
          );
        })}
      </div>
      <div className="bg-white/[0.03] border border-white/10 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-white/5">
          <h3 className="text-sm font-semibold">{entries.length} Credentials</h3>
        </div>
        <div className="max-h-[500px] overflow-y-auto divide-y divide-white/5">
          {entries.slice(0, 30).map(e => (
            <div key={e.id} className="flex items-center gap-3 px-5 py-2.5 hover:bg-white/[0.02]">
              {e.managed_by && <img src={getAgentAvatar(e.managed_by)} className="w-6 h-6 rounded-full object-cover" alt="" />}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate">{e.service}</p>
                <p className="text-[10px] text-white/25 truncate font-mono">{e.account_name}</p>
              </div>
              <span className={`text-[8px] px-1.5 py-0.5 rounded-full ${e.status === "active" ? "bg-green-500/20 text-green-400" : "bg-white/5 text-white/25"}`}>{e.status}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
