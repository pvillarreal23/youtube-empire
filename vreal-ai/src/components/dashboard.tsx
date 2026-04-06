"use client";
import { useState, useEffect, useRef, useCallback } from "react";
import { BarChart3, PlayCircle, Youtube, Users, Eye, ThumbsUp, ArrowUpRight, ArrowDownRight, Target, Layers, Settings, Bell, Search, Plus, LayoutDashboard, Mic, Image, Type, Upload, LineChart, BookOpen, X, Edit3, Trash2, Save, ChevronRight, FileText, Clock, Zap, CheckCircle2, AlertCircle, RefreshCw, ExternalLink, MessageSquare, Send, Bot, User, ChevronDown, Mail, Sparkles, TrendingUp, UserPlus, Megaphone, PenTool, MailOpen, Activity, CircleDot, Play, AlertTriangle, CheckCircle, XCircle, Globe, KeyRound, Inbox, Wrench } from "lucide-react";
import { AGENT_PERSONAS, AVATAR_OVERRIDES, getAgentAvatar, getHumanName, TIER_LABELS, TIER_STYLES, AGENT_TIER_MAP, getAgentTier, DEPT_COLORS } from "@/lib/constants";
import type { Tier } from "@/lib/constants";
import SpeakButton from "@/components/SpeakButton";

type Tab = "overview" | "pipeline" | "channels" | "skills" | "automation" | "analytics" | "agents" | "newsletter" | "activity" | "feed" | "social" | "vault" | "inbox" | "tools";
interface SocialAccountInfo { id: string; platform: string; account_name: string; display_name: string; channel_brand: string; managed_by: string; status: string; followers: string; }
interface VaultEntry { id: string; service: string; account_name: string; category: string; platform_url: string; notes: string; api_key_hint: string; managed_by: string; status: string; }

interface AgentInfo { id: string; name: string; role: string; avatar_color: string; department: string; avatar?: string; reports_to: string | null; direct_reports: string[]; collaborates_with: string[]; }
interface ActivityData { running_count: number; completed_today: number; pending_escalations: number; total_agents: number; agent_statuses: { id: string; name: string; role: string; department: string; avatar_color: string; status: string; current_task: string }[]; recent_runs: { id: string; agent_id: string; task_name: string; status: string; summary: string | null; completed_at: string | null; thread_id: string | null }[]; escalations: { id: string; agent_id: string; reason: string; severity: string; thread_id: string; created_at: string }[] }
interface ScheduledTaskInfo { id: string; agent_id: string; agent_name: string; name: string; cron_expression: string; enabled: boolean; last_run: string | null; category: string }
interface FeedMsg { id: string; agent_id: string; agent_name: string; agent_color: string; channel: string; content: string; message_type: string; severity: string; thread_id: string | null; pinned: boolean; created_at: string; read: boolean }
const FEED_CHANNELS: Record<string, { name: string; emoji: string }> = { general: { name: "General", emoji: "💬" }, content: { name: "Content", emoji: "📝" }, operations: { name: "Operations", emoji: "⚙️" }, analytics: { name: "Analytics", emoji: "📊" }, monetization: { name: "Revenue", emoji: "💰" }, alerts: { name: "Alerts", emoji: "🚨" }, wins: { name: "Wins", emoji: "🏆" } };
interface ThreadMsg { id: string; sender_type: "user" | "agent"; sender_agent_id: string | null; sender_name?: string; content: string; created_at: string; status: string; }
interface Thread { id: string; subject: string; participants: string[]; messages: ThreadMsg[]; status: string; updated_at: string; }

// All API calls go through Next.js proxy routes — no direct backend calls

type Status = "RESEARCHED" | "TITLED" | "SCRIPTED" | "PRODUCTION" | "READY" | "SCHEDULED" | "LIVE";

interface PipelineItem { id: string; title: string; channel: string; status: Status; date: string; views: string; }
interface Channel { id: string; name: string; subs: string; views: string; freq: string; color: string; growth: string; vids: string; ctr: string; revenue: string; nextVideo: string; subsCount?: number; revenueAmount?: number; vidsCount?: number; }

const SC: Record<Status, string> = {
  RESEARCHED: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  TITLED: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  SCRIPTED: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
  PRODUCTION: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
  READY: "bg-green-500/20 text-green-400 border-green-500/30",
  SCHEDULED: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  LIVE: "bg-red-500/20 text-red-400 border-red-500/30",
};

const STATUSES: Status[] = ["RESEARCHED","TITLED","SCRIPTED","PRODUCTION","READY","SCHEDULED","LIVE"];

const initialChannels: Channel[] = [
  { id:"1", name:"V-Real AI", subs:"47", views:"—", freq:"3x/week", color:"from-cyan-600 to-blue-500", growth:"—", vids:"0", ctr:"—", revenue:"—", nextVideo:"EP001", subsCount: 47 },
  { id:"2", name:"Cash Flow Code", subs:"—", views:"—", freq:"2x/week", color:"from-green-600 to-emerald-500", growth:"—", vids:"—", ctr:"—", revenue:"—", nextVideo:"Planned" },
  { id:"3", name:"Mind Shift", subs:"—", views:"—", freq:"1x/week", color:"from-purple-600 to-pink-500", growth:"—", vids:"—", ctr:"—", revenue:"—", nextVideo:"Planned" },
];

const initialPipeline: PipelineItem[] = [
  { id:"1", title:"5 AI Tools Replacing Jobs in 2026", channel:"V-Real AI", status:"SCRIPTED", date:"Apr 2", views:"-" },
  { id:"2", title:"Claude vs GPT-4o: Real Comparison", channel:"V-Real AI", status:"SCRIPTED", date:"Apr 5", views:"-" },
  { id:"4", title:"How I Built a $10K/mo AI Business", channel:"Cash Flow Code", status:"PRODUCTION", date:"Apr 12", views:"-" },
  { id:"5", title:"The Psychology of Going Viral", channel:"Mind Shift", status:"TITLED", date:"Apr 14", views:"-" },
  { id:"6", title:"AI Agents Will Replace SaaS", channel:"V-Real AI", status:"SCRIPTED", date:"Apr 16", views:"-" },
  { id:"7", title:"Why Most Side Hustles Fail in 2026", channel:"Cash Flow Code", status:"PRODUCTION", date:"Apr 19", views:"-" },
  { id:"8", title:"How YouTube Algorithm Actually Works", channel:"Mind Shift", status:"TITLED", date:"Apr 21", views:"-" },
  { id:"3", title:"How Make.com Automates Everything", channel:"V-Real AI", status:"SCRIPTED", date:"Apr 9", views:"-" },
];

const SKILLS = [
  { name:"research.md", desc:"Find trending topics & keywords", icon:BookOpen, file:"skills/research.md", status:"ready" },
  { name:"script_writer.md", desc:"Write 8–12 min scripts", icon:FileText, file:"skills/script_writer.md", status:"ready" },
  { name:"title_optimizer.md", desc:"Generate CTR-optimized titles", icon:Type, file:"skills/title_optimizer.md", status:"ready" },
  { name:"thumbnail_designer.md", desc:"Create thumbnail briefs & A/B variants", icon:Image, file:"skills/thumbnail_designer.md", status:"ready" },
  { name:"voiceover_director.md", desc:"Annotate scripts for AI voice", icon:Mic, file:"skills/voiceover_director.md", status:"ready" },
  { name:"description_writer.md", desc:"Write SEO descriptions + tags", icon:FileText, file:"skills/description_writer.md", status:"ready" },
  { name:"upload_scheduler.md", desc:"Build upload calendar", icon:Upload, file:"skills/upload_scheduler.md", status:"ready" },
  { name:"analytics_reviewer.md", desc:"Analyze performance + recommendations", icon:LineChart, file:"skills/analytics_reviewer.md", status:"ready" },
];

const AUTOMATIONS = [
  { id:"1", name:"Run Research", desc:"Agent finds trending topics, keywords & competitor gaps", icon:BookOpen, color:"from-purple-600 to-blue-600", step:"Step 1", route:"/api/research/trending", bodyFn: (t:string) => ({ topic: t, platform: "youtube" }) },
  { id:"2", name:"Generate Script", desc:"Agent writes full 8-12 min narration script", icon:FileText, color:"from-blue-600 to-cyan-600", step:"Step 2", route:"/api/script/generate", bodyFn: (t:string) => ({ topic: t, duration_minutes: 10 }) },
  { id:"3", name:"Create Voiceover", desc:"ElevenLabs Daniel voice converts script to MP3", icon:Mic, color:"from-cyan-600 to-teal-600", step:"Step 3", route:"/api/voiceover", bodyFn: (t:string) => ({ text: t, voice_id: "onwK4e9ZLuTAKqWW03F9" }) },
  { id:"4", name:"Generate Thumbnail", desc:"Ideogram AI auto-generates YouTube thumbnail", icon:Image, color:"from-orange-600 to-red-600", step:"Step 4", route:"/api/thumbnail", bodyFn: (t:string) => ({ title: t }) },
  { id:"5", name:"Optimize SEO", desc:"Agent writes title, description, tags & chapters", icon:Type, color:"from-green-600 to-emerald-600", step:"Step 5", route:"/api/seo/optimize", bodyFn: (t:string) => ({ topic: t, platform: "youtube" }) },
  { id:"6", name:"Video Editor Brief", desc:"Nadia maps every shot, b-roll & text animation", icon:PlayCircle, color:"from-red-600 to-pink-600", step:"Step 6", route:"/api/video-editor/brief", bodyFn: (t:string) => ({ topic: t, video_type: "standard" }) },
  { id:"7", name:"Full Pipeline (All Steps)", desc:"Marcus orchestrates all 6 stages in one shot", icon:Zap, color:"from-amber-500 to-orange-600", step:"All Steps", route:"/api/workflow/orchestrate", bodyFn: (t:string) => ({ topic: t, tool_name: t, key_insight: `Key insight about ${t}`, run_live_research: true }) },
];

function Modal({ open, onClose, title, children }: { open:boolean; onClose:()=>void; title:string; children:React.ReactNode }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-[#141414] border border-white/10 rounded-2xl p-6 w-full max-w-lg mx-4">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">{title}</h3>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-white/10"><X className="w-5 h-5 text-white/60" /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

function StatCard({ label, value, change, up, icon: Icon }: { label:string; value:string; change:string; up:boolean; icon:any }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-xl p-5 hover:border-white/20 transition-all">
      <div className="flex items-center justify-between mb-3">
        <Icon className="w-5 h-5 text-white/40" />
        <span className={`flex items-center gap-1 text-xs font-medium ${up ? "text-green-400" : "text-red-400"}`}>
          {up ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}{change}
        </span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-sm text-white/50 mt-1">{label}</p>
    </div>
  );
}

// Bracket-style card for a single agent
function BracketCard({ agent }: { agent: AgentInfo }) {
  const tier = getAgentTier(agent.id);
  const ts = TIER_STYLES[tier];
  const dept = DEPT_COLORS[agent.department] || DEPT_COLORS.general;
  return (
    <div className={`${ts.bg} border ${ts.border} rounded-lg px-3 py-2 flex items-center gap-2.5 min-w-0`}>
      <div className={`w-8 h-8 rounded-full overflow-hidden shrink-0 ring-2 ${ts.ring}`}>
        <img src={getAgentAvatar(agent.id, agent.avatar)} alt={agent.name} className="w-full h-full object-cover" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-semibold truncate">{getHumanName(agent.id) || agent.name}</p>
        <div className="flex items-center gap-1 mt-0.5">
          <span className={`text-[8px] px-1.5 py-0 rounded-full border font-medium ${ts.badge}`}>{tier}</span>
          <span className="text-[8px] px-1.5 py-0 rounded-full border border-white/10 text-white/40 flex items-center gap-0.5">
            <span className={`w-1 h-1 rounded-full ${dept.dot}`} />{dept.label}
          </span>
        </div>
      </div>
    </div>
  );
}

// Bracket connector: a vertical line from parent down, then horizontal to each child
function BracketGroup({ parent, children, agents, depth }: { parent: AgentInfo; children: AgentInfo[]; agents: AgentInfo[]; depth: number }) {
  const grandchildren = (agentId: string) => agents.filter(a => a.reports_to === agentId);
  return (
    <div className="flex items-start gap-0">
      {/* Parent card + vertical connector */}
      <div className="flex flex-col items-center shrink-0" style={{ minWidth: 200 }}>
        <BracketCard agent={parent} />
        {children.length > 0 && (
          <div className="w-px h-4 bg-white/15" />
        )}
      </div>

      {/* Children bracket */}
      {children.length > 0 && (
        <div className="flex flex-col relative" style={{ marginLeft: -1 }}>
          {/* Horizontal connector from parent */}
          <div className="absolute left-0 top-5 w-4 h-px bg-white/15" style={{ marginLeft: -16 }} />

          {children.map((child, i) => {
            const gc = grandchildren(child.id);
            return (
              <div key={child.id} className="flex items-start relative">
                {/* Vertical bracket line */}
                {children.length > 1 && (
                  <div className="absolute left-0 bg-white/15" style={{
                    width: 1,
                    top: i === 0 ? 16 : 0,
                    bottom: i === children.length - 1 ? "calc(100% - 16px)" : 0,
                    height: i === 0 ? "calc(100% - 16px)" : i === children.length - 1 ? 16 : "100%",
                  }} />
                )}
                {/* Horizontal line to child */}
                <div className="w-6 h-px bg-white/15 shrink-0 mt-4" />

                <div className="py-1">
                  {gc.length > 0 && depth < 2 ? (
                    <BracketGroup parent={child} children={gc} agents={agents} depth={depth + 1} />
                  ) : (
                    <BracketCard agent={child} />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [tab, setTab] = useState<Tab>("overview");
  const [pipeline, setPipeline] = useState<PipelineItem[]>(initialPipeline);
  const [prodJobs, setProdJobs] = useState<any[]>([]);
  const [growthBoard, setGrowthBoard] = useState<any[]>([]);
  const [prodBoard, setProdBoard] = useState<any[]>([]);
  const [selectedAgentSkills, setSelectedAgentSkills] = useState<any>(null);
  const [channels, setChannels] = useState<Channel[]>(initialChannels);
  const [editItem, setEditItem] = useState<PipelineItem | null>(null);
  const [showNewModal, setShowNewModal] = useState(false);
  const [filterStatus, setFilterStatus] = useState<Status | "ALL">("ALL");
  const [newItem, setNewItem] = useState<Partial<PipelineItem>>({ title:"", channel:initialChannels[0].name, status:"RESEARCHED", date:"", views:"-" });
  const [autoStates, setAutoStates] = useState<Record<string, "idle"|"running"|"done">>(Object.fromEntries(AUTOMATIONS.map(a => [a.id, "idle"])));
  const [skillModal, setSkillModal] = useState<typeof SKILLS[0] | null>(null);
  const [pipelineTopic, setPipelineTopic] = useState("");
  const [pipelineTopicModal, setPipelineTopicModal] = useState<string | null>(null); // automation id pending topic
  const [pipelineResult, setPipelineResult] = useState<{ id: string; data: any } | null>(null);

  // === Agents Tab State ===
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [agentPrompt, setAgentPrompt] = useState("");
  const [activeThread, setActiveThread] = useState<Thread | null>(null);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [agentSending, setAgentSending] = useState(false);
  const [agentView, setAgentView] = useState<"chat" | "directory" | "departments" | "org">("chat");
  const msgEndRef = useRef<HTMLDivElement>(null);

  // === Activity Tab State ===
  const [activityData, setActivityData] = useState<ActivityData | null>(null);
  const [scheduledTasks, setScheduledTasks] = useState<ScheduledTaskInfo[]>([]);

  // === Feed State ===
  const [feedMessages, setFeedMessages] = useState<FeedMsg[]>([]);
  const [feedChannel, setFeedChannel] = useState("all");
  const [feedUnread, setFeedUnread] = useState<{ total: number; channels: Record<string, number> }>({ total: 0, channels: {} });
  const [feedInput, setFeedInput] = useState("");

  // === Social & Vault State ===
  const [socialAccounts, setSocialAccounts] = useState<SocialAccountInfo[]>([]);
  const [vaultEntries, setVaultEntries] = useState<VaultEntry[]>([]);
  const [socialFilter, setSocialFilter] = useState("all");

  // === Tools Tab State ===
  const [toolsList, setToolsList] = useState<any[]>([]);
  const [scenariosList, setScenariosList] = useState<Record<string, any>>({});

  // Fetch agents and activity on mount
  useEffect(() => {
    fetch(`/api/agents`).then(r => r.json()).then(d => setAgents(Array.isArray(d) ? d : d.agents || [])).catch(() => {});
    fetch(`/api/threads`).then(r => r.json()).then(d => setThreads(Array.isArray(d) ? d : d.threads || [])).catch(() => {});
    fetch(`/api/scheduler/activity`).then(r => r.json()).then(setActivityData).catch(() => {});
    fetch(`/api/scheduler/tasks`).then(r => r.json()).then(d => setScheduledTasks(Array.isArray(d) ? d : d.tasks || [])).catch(() => {});
    fetch(`/api/feed/messages?limit=50`).then(r => r.json()).then(d => setFeedMessages(Array.isArray(d) ? d : d.messages || [])).catch(() => {});
    fetch(`/api/feed/unread_count`).then(r => r.json()).then(setFeedUnread).catch(() => {});
    fetch(`/api/social/accounts`).then(r => r.json()).then(d => setSocialAccounts(Array.isArray(d) ? d : d.accounts || [])).catch(() => {});
    fetch(`/api/vault/credentials`).then(r => r.json()).then(d => setVaultEntries(Array.isArray(d) ? d : d.credentials || [])).catch(() => {});
    fetch(`/api/tools`).then(r => r.json()).then(d => setToolsList(Array.isArray(d) ? d : d.tools || [])).catch(() => {});
    fetch(`/api/tools/scenarios`).then(r => r.json()).then(d => setScenariosList(Array.isArray(d) ? {} : (d.scenarios || d))).catch(() => {});
    fetch(`/api/channels`).then(r => r.json()).then(d => setChannels(Array.isArray(d) ? d : d.channels || [])).catch(() => {});
    // Production jobs + skills leaderboards
    fetch(`/api/production/jobs`).then(r => r.json()).then(d => setProdJobs(Array.isArray(d) ? d : [])).catch(() => {});
    fetch(`/api/skills/leaderboard/growth`).then(r => r.json()).then(d => setGrowthBoard(Array.isArray(d) ? d : [])).catch(() => {});
    fetch(`/api/skills/leaderboard/production`).then(r => r.json()).then(d => setProdBoard(Array.isArray(d) ? d : [])).catch(() => {});
  }, []);

  // Poll activity + feed + production every 10 seconds
  useEffect(() => {
    const poll = setInterval(() => {
      fetch(`/api/scheduler/activity`).then(r => r.json()).then(setActivityData).catch(() => {});
      fetch(`/api/feed/messages?channel=${feedChannel}&limit=50`).then(r => r.json()).then(d => setFeedMessages(d.messages || [])).catch(() => {});
      fetch(`/api/feed/unread_count`).then(r => r.json()).then(setFeedUnread).catch(() => {});
      fetch(`/api/production/jobs`).then(r => r.json()).then(d => setProdJobs(Array.isArray(d) ? d : [])).catch(() => {});
      fetch(`/api/skills/leaderboard/growth`).then(r => r.json()).then(d => setGrowthBoard(Array.isArray(d) ? d : [])).catch(() => {});
    }, 10000);
    return () => clearInterval(poll);
  }, [feedChannel]);

  const resolveEscalation = async (id: string) => {
    await fetch(`/api/scheduler/escalations/${id}/resolve`, { method: "POST" }).catch(() => {});
    fetch(`/api/scheduler/activity`).then(r => r.json()).then(setActivityData).catch(() => {});
  };

  const triggerTask = async (id: string) => {
    await fetch(`/api/scheduler/tasks/${id}/run`, { method: "POST" }).catch(() => {});
    setTimeout(() => fetch(`/api/scheduler/activity`).then(r => r.json()).then(setActivityData).catch(() => {}), 2000);
  };

  const switchFeedChannel = (ch: string) => {
    setFeedChannel(ch);
    fetch(`/api/feed/messages?channel=${ch}&limit=50`).then(r => r.json()).then(d => setFeedMessages(d.messages || [])).catch(() => {});
  };

  const sendFeedMessage = async () => {
    if (!feedInput.trim()) return;
    await fetch(`/api/feed/send`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: feedInput, channel: feedChannel === "all" ? "general" : feedChannel }),
    }).catch(() => {});
    setFeedInput("");
    fetch(`/api/feed/messages?channel=${feedChannel}&limit=50`).then(r => r.json()).then(d => setFeedMessages(d.messages || [])).catch(() => {});
  };

  const markAllRead = async () => {
    await fetch(`/api/feed/mark_all_read?channel=${feedChannel}`, { method: "POST" }).catch(() => {});
    fetch(`/api/feed/unread_count`).then(r => r.json()).then(setFeedUnread).catch(() => {});
  };

  // Poll active thread for new messages
  useEffect(() => {
    if (!activeThread) return;
    const poll = setInterval(() => {
      fetch(`/api/threads/${activeThread.id}`).then(r => r.json()).then((t: Thread) => {
        setActiveThread(t);
      }).catch(() => {});
    }, 3000);
    return () => clearInterval(poll);
  }, [activeThread?.id]);

  // Scroll to bottom on new messages
  useEffect(() => { msgEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [activeThread?.messages?.length]);

  const sendToAgents = async () => {
    if (!agentPrompt.trim()) return;
    setAgentSending(true);
    try {
      // Find CEO agent
      const ceo = agents.find(a => a.id.includes("ceo"));
      const recipientId = ceo?.id || agents[0]?.id;
      if (!recipientId) { setAgentSending(false); return; }
      const res = await fetch(`/api/threads`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject: agentPrompt.slice(0, 60), recipient_agent_ids: [recipientId], content: agentPrompt }),
      });
      const thread = await res.json();
      setActiveThread({ ...thread, messages: [{ id: "user-0", sender_type: "user", sender_agent_id: null, content: agentPrompt, created_at: new Date().toISOString(), status: "sent" }] });
      setAgentPrompt("");
      setThreads(prev => [thread, ...prev]);
    } catch (e) { console.error(e); }
    setAgentSending(false);
  };

  const sendReply = async () => {
    if (!agentPrompt.trim() || !activeThread) return;
    setAgentSending(true);
    try {
      await fetch(`/api/threads/${activeThread.id}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: agentPrompt }),
      });
      setAgentPrompt("");
    } catch (e) { console.error(e); }
    setAgentSending(false);
  };

  const getAgentById = (id: string) => agents.find(a => a.id === id);

  const handleSaveEdit = () => { if (!editItem) return; setPipeline(prev => prev.map(p => p.id === editItem.id ? editItem : p)); setEditItem(null); };
  const handleDelete = (id: string) => setPipeline(prev => prev.filter(p => p.id !== id));
  const handleAddNew = () => {
    if (!newItem.title) return;
    const item: PipelineItem = { id: Date.now().toString(), title: newItem.title||"", channel: newItem.channel||initialChannels[0].name, status:(newItem.status as Status)||"RESEARCHED", date:newItem.date||"TBD", views:"-" };
    setPipeline(prev => [item, ...prev]);
    setNewItem({ title:"", channel:initialChannels[0].name, status:"RESEARCHED", date:"", views:"-" });
    setShowNewModal(false);
  };
  const handleStatusChange = (id: string, newStatus: Status) => setPipeline(prev => prev.map(p => p.id === id ? { ...p, status: newStatus } : p));
  const filteredPipeline = filterStatus === "ALL" ? pipeline : pipeline.filter(p => p.status === filterStatus);

  const triggerAutomation = async (id: string, topic: string) => {
    const auto = AUTOMATIONS.find(a => a.id === id);
    if (!auto) return;
    setAutoStates(prev => ({ ...prev, [id]: "running" }));
    setPipelineTopicModal(null);
    try {
      const res = await fetch(auto.route, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(auto.bodyFn(topic)),
      });
      const data = await res.json();
      setAutoStates(prev => ({ ...prev, [id]: "done" }));
      setPipelineResult({ id, data });
    } catch {
      setAutoStates(prev => ({ ...prev, [id]: "idle" }));
    }
  };

  const startAutomation = (id: string) => {
    if (pipelineTopic.trim()) {
      triggerAutomation(id, pipelineTopic.trim());
    } else {
      setPipelineTopicModal(id);
    }
  };

  // Compute stats from channels data
  const totalSubs = channels.reduce((sum, ch) => sum + (ch.subsCount || 0), 0);
  const totalRevenue = channels.reduce((sum, ch) => sum + (ch.revenueAmount || 0), 0);
  const totalVids = channels.reduce((sum, ch) => sum + (ch.vidsCount || 0), 0);

  const stats = [
    { label:"Total Monthly Revenue", value:`$${totalRevenue}`, change:"+0%", up:true, icon:Eye },
    { label:"Total Subscribers", value:totalSubs.toLocaleString(), change:"+0%", up:true, icon:Users },
    { label:"Videos Published", value:totalVids.toString(), change:"Month 0", up:true, icon:Clock },
    { label:"Tool Spend", value:"$0", change:"On budget", up:true, icon:Target },
  ];

  const tabs: { id: Tab; label: string; icon: typeof LayoutDashboard }[] = [
    { id:"overview", label:"Overview", icon:LayoutDashboard },
    { id:"pipeline", label:"Pipeline", icon:Layers },
    { id:"channels", label:"Channels", icon:Youtube },
    { id:"skills", label:"Skills", icon:BookOpen },
    { id:"automation", label:"Automation", icon:Zap },
    { id:"analytics", label:"Analytics", icon:BarChart3 },
    { id:"agents", label:"Agents", icon:MessageSquare },
    { id:"newsletter", label:"Newsletter", icon:Mail },
    { id:"activity", label:"Activity", icon:Activity },
    { id:"feed", label:"Feed", icon:MessageSquare },
    { id:"social", label:"Social", icon:Globe },
    { id:"vault", label:"Vault", icon:KeyRound },
    { id:"inbox", label:"Inbox", icon:Inbox },
    { id:"tools", label:"Tools", icon:Wrench },
  ];

  const sidebarSections: { label: string; items: { id: Tab; label: string; icon: typeof LayoutDashboard; badge?: number }[] }[] = [
    { label: "COMMAND", items: [
      { id: "overview", label: "Overview", icon: LayoutDashboard },
      { id: "inbox", label: "Inbox", icon: Inbox, badge: (activityData?.pending_escalations || 0) },
    ]},
    { label: "CONTENT", items: [
      { id: "pipeline", label: "Pipeline", icon: Layers },
      { id: "channels", label: "Channels", icon: Youtube },
      { id: "newsletter", label: "Newsletter", icon: Mail },
    ]},
    { label: "TEAM", items: [
      { id: "agents", label: "Agents", icon: MessageSquare },
      { id: "activity", label: "Activity", icon: Activity },
      { id: "feed", label: "Feed", icon: MessageSquare, badge: feedUnread.total || 0 },
    ]},
    { label: "OPERATIONS", items: [
      { id: "automation", label: "Automation", icon: Zap },
      { id: "tools", label: "Tools", icon: Wrench },
      { id: "social", label: "Social", icon: Globe },
      { id: "vault", label: "Vault", icon: KeyRound },
    ]},
    { label: "INSIGHTS", items: [
      { id: "analytics", label: "Analytics", icon: BarChart3 },
      { id: "skills", label: "Skills", icon: BookOpen },
    ]},
  ];

  const currentTabLabel = tabs.find(t => t.id === tab)?.label || "Overview";
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Mobile bottom nav — most important tabs for quick access
  const mobileBottomTabs: { id: Tab; label: string; icon: typeof LayoutDashboard }[] = [
    { id: "overview", label: "Home", icon: LayoutDashboard },
    { id: "pipeline", label: "Pipeline", icon: Layers },
    { id: "agents", label: "Agents", icon: Bot },
    { id: "feed", label: "Feed", icon: MessageSquare },
    { id: "inbox", label: "Inbox", icon: Inbox },
  ];

  return (
    <div className="h-screen bg-[#0a0a0a] text-white flex overflow-hidden">
      {/* ===== MOBILE OVERLAY MENU ===== */}
      {mobileMenuOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex">
          <div className="absolute inset-0 bg-black/60" onClick={() => setMobileMenuOpen(false)} />
          <div className="relative w-64 bg-[#0d0d0d] border-r border-white/[0.06] flex flex-col h-full animate-in slide-in-from-left">
            <div className="h-14 flex items-center justify-between px-4 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center">
                  <PlayCircle className="w-4 h-4" />
                </div>
                <span className="text-sm font-semibold">Creator AI</span>
              </div>
              <button onClick={() => setMobileMenuOpen(false)} className="p-1 rounded-lg hover:bg-white/10">
                <X className="w-5 h-5 text-white/50" />
              </button>
            </div>
            <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-4">
              {sidebarSections.map(section => (
                <div key={section.label}>
                  <p className="text-[10px] font-semibold text-white/25 uppercase tracking-[0.12em] px-2 mb-1">{section.label}</p>
                  <div className="space-y-0.5">
                    {section.items.map(item => {
                      const isActive = tab === item.id;
                      return (
                        <button
                          key={item.id}
                          onClick={() => { setTab(item.id); setMobileMenuOpen(false); }}
                          className={`w-full flex items-center gap-2.5 px-2.5 py-2.5 rounded-lg text-[13px] font-medium transition-all ${
                            isActive ? "bg-white/[0.08] text-white" : "text-white/40"
                          }`}
                        >
                          <item.icon className={`w-4 h-4 shrink-0 ${isActive ? "text-white" : "text-white/30"}`} />
                          <span className="flex-1 text-left">{item.label}</span>
                          {(item.badge || 0) > 0 && (
                            <span className="min-w-[18px] h-[18px] flex items-center justify-center bg-red-500/90 rounded-full text-[9px] font-bold px-1">{item.badge}</span>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* ===== LEFT SIDEBAR (desktop only) ===== */}
      <aside className="hidden md:flex w-60 shrink-0 bg-[#0d0d0d] border-r border-white/[0.06] flex-col h-screen sticky top-0 z-40">
        {/* Logo */}
        <div className="h-16 flex items-center gap-3 px-5 border-b border-white/[0.06]">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg shadow-orange-500/20">
            <PlayCircle className="w-5 h-5" />
          </div>
          <div>
            <span className="text-sm font-semibold tracking-tight">Creator AI</span>
            <p className="text-[10px] text-white/30 -mt-0.5">Agency Dashboard</p>
          </div>
        </div>

        {/* Nav sections */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
          {sidebarSections.map(section => (
            <div key={section.label}>
              <p className="text-[10px] font-semibold text-white/25 uppercase tracking-[0.12em] px-2 mb-1.5">{section.label}</p>
              <div className="space-y-0.5">
                {section.items.map(item => {
                  const isActive = tab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setTab(item.id)}
                      className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] font-medium transition-all group ${
                        isActive
                          ? "bg-white/[0.08] text-white shadow-sm"
                          : "text-white/40 hover:text-white/70 hover:bg-white/[0.04]"
                      }`}
                    >
                      <item.icon className={`w-4 h-4 shrink-0 ${isActive ? "text-white" : "text-white/30 group-hover:text-white/50"}`} />
                      <span className="flex-1 text-left">{item.label}</span>
                      {(item.badge || 0) > 0 && (
                        <span className="min-w-[18px] h-[18px] flex items-center justify-center bg-red-500/90 rounded-full text-[9px] font-bold px-1">
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Sidebar footer: bell + profile */}
        <div className="border-t border-white/[0.06] p-3 space-y-2">
          <button onClick={() => setTab("activity")} className="relative w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13px] text-white/40 hover:text-white/70 hover:bg-white/[0.04] transition-all">
            <Bell className="w-4 h-4" />
            <span>Notifications</span>
            {(activityData?.pending_escalations || 0) > 0 && (
              <span className="ml-auto min-w-[18px] h-[18px] flex items-center justify-center bg-red-500/90 rounded-full text-[9px] font-bold px-1">{activityData?.pending_escalations}</span>
            )}
          </button>
          <div className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-white/[0.04] transition-all cursor-pointer">
            <div className="w-8 h-8 rounded-full ring-2 ring-purple-500/40 overflow-hidden">
              <img src="/avatars/pedro.jpg" alt="Pedro" className="w-full h-full object-cover" />
            </div>
            <div className="leading-tight flex-1 min-w-0">
              <p className="text-[13px] font-semibold truncate">Pedro</p>
              <p className="text-[10px] text-white/30">Empire Operator</p>
            </div>
            <Settings className="w-3.5 h-3.5 text-white/20" />
          </div>
        </div>
      </aside>

      {/* ===== MAIN CONTENT ===== */}
      <main className="flex-1 overflow-y-auto min-w-0 pb-16 md:pb-0">
        {/* Top bar */}
        <div className="sticky top-0 z-30 h-14 bg-[#0a0a0a]/80 backdrop-blur-xl border-b border-white/[0.06] flex items-center px-4 md:px-8">
          {/* Mobile hamburger */}
          <button onClick={() => setMobileMenuOpen(true)} className="md:hidden p-1.5 -ml-1 mr-2 rounded-lg hover:bg-white/10">
            <Layers className="w-5 h-5 text-white/60" />
          </button>
          <div className="flex items-center gap-2 text-sm">
            <span className="text-white/30 hidden md:inline">Dashboard</span>
            <ChevronRight className="w-3.5 h-3.5 text-white/20 hidden md:inline" />
            <span className="font-medium">{currentTabLabel}</span>
            <SpeakButton text={`V-Real AI Dashboard — ${currentTabLabel}`} className="hidden md:inline-flex ml-1" />
          </div>
          {/* Mobile: notification badge */}
          <div className="ml-auto md:hidden flex items-center gap-2">
            {(activityData?.pending_escalations || 0) > 0 && (
              <button onClick={() => setTab("inbox")} className="relative p-1.5 rounded-lg hover:bg-white/10">
                <Bell className="w-5 h-5 text-white/60" />
                <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-[16px] flex items-center justify-center bg-red-500 rounded-full text-[8px] font-bold">{activityData?.pending_escalations}</span>
              </button>
            )}
          </div>
        </div>

        <div className="px-3 py-4 md:px-8 md:py-6 max-w-[1400px]">

        {tab === "overview" && (
          <div className="space-y-8">
            {/* Autopilot Status Bar */}
            {activityData && (
              <div className="bg-gradient-to-r from-purple-500/10 via-blue-500/5 to-cyan-500/10 border border-purple-500/20 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                    <span className="text-sm font-semibold">Autopilot Active</span>
                    <span className="text-[10px] text-white/30">— {activityData.total_agents} agents deployed</span>
                  </div>
                  <button onClick={() => setTab("activity")} className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1">View All <ChevronRight className="w-3 h-3" /></button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="flex items-center gap-2">
                    <Play className="w-4 h-4 text-green-400" />
                    <div><p className="text-lg font-bold">{activityData.running_count}</p><p className="text-[10px] text-white/30">Running Now</p></div>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-blue-400" />
                    <div><p className="text-lg font-bold">{activityData.completed_today}</p><p className="text-[10px] text-white/30">Completed Today</p></div>
                  </div>
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                    <div><p className="text-lg font-bold">{activityData.pending_escalations}</p><p className="text-[10px] text-white/30">Need Your Review</p></div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-purple-400" />
                    <div><p className="text-lg font-bold">{scheduledTasks.filter(t => t.enabled).length}</p><p className="text-[10px] text-white/30">Active Tasks</p></div>
                  </div>
                </div>
                {(activityData.escalations?.length ?? 0) > 0 && (
                  <div className="mt-3 pt-3 border-t border-white/5">
                    <p className="text-[10px] text-amber-400 font-semibold uppercase tracking-wider mb-2">Needs Your Attention</p>
                    {activityData.escalations?.slice(0, 3).map(e => (
                      <div key={e.id} className="flex items-center justify-between py-1.5">
                        <div className="flex items-center gap-2">
                          <AlertTriangle className="w-3 h-3 text-amber-400" />
                          <span className="text-xs text-white/60">{e.reason}</span>
                        </div>
                        <button onClick={() => resolveEscalation(e.id)} className="text-[10px] text-green-400 hover:text-green-300 px-2 py-0.5 border border-green-500/20 rounded">Resolve</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {stats.map(s => <StatCard key={s.label} {...s} />)}
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-lg font-semibold flex items-center gap-2"><Layers className="w-5 h-5 text-blue-400" />Content Pipeline</h2>
                  <button onClick={() => setTab("pipeline")} className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-1">View All <ChevronRight className="w-4 h-4" /></button>
                </div>
                <div className="space-y-2">
                  {pipeline.slice(0,5).map(item => (
                    <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all cursor-pointer" onClick={() => setEditItem(item)}>
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${item.status==="LIVE" ? "bg-red-500 animate-pulse" : item.status==="SCHEDULED" ? "bg-orange-500" : "bg-white/30"}`} />
                        <div><p className="text-sm font-medium">{item.title}</p><p className="text-xs text-white/40">{item.channel}</p></div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-white/40 hidden sm:inline">{item.date}</span>
                        <span className={`text-xs px-2 py-1 rounded-full border ${SC[item.status]}`}>{item.status}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h2 className="text-lg font-semibold flex items-center gap-2 mb-4"><Zap className="w-5 h-5 text-yellow-400" />Quick Actions</h2>
                <div className="space-y-2">
                  {AUTOMATIONS.slice(0,5).map(a => (
                    <button key={a.id} onClick={() => { setTab("automation"); }} className="w-full flex items-center gap-3 p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-all text-left">
                      <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${a.color} flex items-center justify-center flex-shrink-0`}><a.icon className="w-4 h-4" /></div>
                      <div><p className="text-sm font-medium">{a.name}</p><p className="text-xs text-white/40">{a.step}</p></div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
            {/* Live Production Jobs */}
            {prodJobs.length > 0 && (
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold flex items-center gap-2"><Target className="w-5 h-5 text-green-400" />Live Production Jobs</h2>
                  <button onClick={() => setTab("pipeline")} className="text-sm text-green-400 hover:text-green-300 flex items-center gap-1">View All <ChevronRight className="w-4 h-4" /></button>
                </div>
                <div className="space-y-2">
                  {prodJobs.slice(0,5).map((j: any) => {
                    const stages = ["research","scripted","voiceover","thumbnail","edited","seo","review","approved","published"];
                    const stageIdx = stages.indexOf(j.stage);
                    const progress = Math.round(((stageIdx+1)/stages.length)*100);
                    return (
                      <div key={j.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{j.title}</p>
                          <p className="text-xs text-white/40">{j.channel} — {j.current_agent_name || j.stage}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="w-20 h-2 bg-white/10 rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full" style={{width:`${progress}%`}} /></div>
                          <span className="text-xs text-white/40 w-8 text-right">{progress}%</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
            {/* Agent Growth Summary */}
            {growthBoard.length > 0 && (
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold flex items-center gap-2"><TrendingUp className="w-5 h-5 text-purple-400" />Top Growing Agents</h2>
                  <button onClick={() => setTab("skills")} className="text-sm text-purple-400 hover:text-purple-300 flex items-center gap-1">View All <ChevronRight className="w-4 h-4" /></button>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {growthBoard.slice(0,6).map((a: any) => (
                    <div key={a.agent_id} className="flex items-center gap-3 p-3 rounded-lg bg-white/5">
                      <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center text-xs font-bold text-purple-400">Lv{a.highest_level}</div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-medium truncate">{a.agent_id}</p>
                        <p className="text-[10px] text-white/40">{a.total_skills} skills | {a.total_xp} XP</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* AI Research Tools */}
            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2 mb-4"><Sparkles className="w-5 h-5 text-purple-400" />AI Tools</h2>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {[
                  { name: "Trend Scanner", desc: "Find trending topics across YouTube, Google, Reddit", icon: "🔍", prompt: "Research the top 10 trending topics across AI, finance, and psychology right now. Include search volume, competition level, and content angle for each." },
                  { name: "Competitor Spy", desc: "Analyze top competitor channels", icon: "🕵️", prompt: "Analyze our top 3 competitors for each channel. What topics are they covering? What's working? Where are the gaps we can exploit?" },
                  { name: "Title Generator", desc: "Generate CTR-optimized titles", icon: "✨", prompt: "Generate 10 high-CTR title options for each channel based on current trending topics. Score each title for curiosity, clarity, and SEO." },
                  { name: "Content Audit", desc: "Review all channels performance", icon: "📊", prompt: "Run a full content audit across all 3 channels. Analyze what's working, what's not, and provide specific recommendations for each channel." },
                  { name: "Newsletter Brief", desc: "Draft this week's newsletter", icon: "✉️", prompt: "Write a complete newsletter for this week. Include: top 3 insights from our latest videos, 1 exclusive tip not in the videos, a content teaser for next week, and a product recommendation with affiliate potential." },
                  { name: "Monetization Scan", desc: "Find new revenue opportunities", icon: "💎", prompt: "Scan all our channels and content for untapped monetization opportunities. Include affiliate programs, sponsorship fits, digital product ideas, and community offerings." },
                  { name: "Script Doctor", desc: "Improve a video script", icon: "🩺", prompt: "Review our latest video script. Check the hook strength, retention structure, storytelling arc, CTA effectiveness, and SEO integration. Provide a score and specific fixes." },
                  { name: "Growth Plan", desc: "Build a 90-day growth strategy", icon: "🚀", prompt: "Create a detailed 90-day growth plan for the entire empire. Include subscriber targets, content volume, collaboration opportunities, and key milestones for each channel." },
                ].map(tool => (
                  <button key={tool.name} onClick={() => { setTab("agents"); setAgentPrompt(tool.prompt); }} className="bg-white/5 border border-white/10 hover:border-white/25 rounded-xl p-4 text-left transition-all group">
                    <span className="text-lg">{tool.icon}</span>
                    <p className="text-xs font-semibold mt-2 group-hover:text-white transition-colors">{tool.name}</p>
                    <p className="text-[10px] text-white/30 mt-0.5 leading-relaxed">{tool.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <h2 className="text-lg font-semibold flex items-center gap-2 mb-4"><Youtube className="w-5 h-5 text-red-400" />Channels</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {channels.map(c => (
                  <div key={c.id} className="bg-white/5 border border-white/10 rounded-xl p-5 hover:border-white/20 transition-all">
                    <div className={`w-full h-1.5 rounded-full bg-gradient-to-r ${c.color} mb-4`} />
                    <h3 className="font-semibold mb-3">{c.name}</h3>
                    <div className="grid grid-cols-2 gap-y-2 text-sm">
                      <div><span className="text-white/40">Subs</span><p className="font-medium">{c.subs}</p></div>
                      <div><span className="text-white/40">Revenue</span><p className="font-medium text-green-400">{c.revenue}</p></div>
                      <div><span className="text-white/40">Frequency</span><p className="font-medium">{c.freq}</p></div>
                      <div><span className="text-white/40">Next video</span><p className="font-medium">{c.nextVideo}</p></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {tab === "pipeline" && (() => {
          const PROD_STAGES = ["research","scripted","voiceover","thumbnail","edited","seo","review","approved","published"];
          const stageColor: Record<string,string> = { research:"text-purple-400 bg-purple-500/20 border-purple-500/30", scripted:"text-cyan-400 bg-cyan-500/20 border-cyan-500/30", voiceover:"text-blue-400 bg-blue-500/20 border-blue-500/30", thumbnail:"text-orange-400 bg-orange-500/20 border-orange-500/30", edited:"text-yellow-400 bg-yellow-500/20 border-yellow-500/30", seo:"text-green-400 bg-green-500/20 border-green-500/30", review:"text-pink-400 bg-pink-500/20 border-pink-500/30", approved:"text-emerald-400 bg-emerald-500/20 border-emerald-500/30", published:"text-red-400 bg-red-500/20 border-red-500/30" };
          const stageIcon: Record<string,string> = { research:"🔍", scripted:"📝", voiceover:"🎙️", thumbnail:"🎨", edited:"🎬", seo:"📊", review:"👁️", approved:"✅", published:"🚀" };
          const refreshJobs = () => fetch('/api/production/jobs').then(r=>r.json()).then(d=>setProdJobs(Array.isArray(d)?d:[])).catch(()=>{});
          const [pipelineView, setPipelineView] = useState<"cards"|"table"|"kanban">("cards");

          return (
          <div className="space-y-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-bold">Content Pipeline</h2>
                <p className="text-xs text-white/40 mt-0.5">{prodJobs.length} active jobs | {prodJobs.filter(j => j.stage === "published").length} published</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex bg-white/5 rounded-lg p-0.5 border border-white/10">
                  {(["cards","table","kanban"] as const).map(v => (
                    <button key={v} onClick={() => setPipelineView(v)} className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-all ${pipelineView === v ? "bg-white/10 text-white" : "text-white/40"}`}>
                      {v === "cards" ? "Cards" : v === "table" ? "Table" : "Board"}
                    </button>
                  ))}
                </div>
                <button onClick={() => setShowNewModal(true)} className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 px-3 py-2 rounded-lg text-xs font-medium transition-colors"><Plus className="w-3.5 h-3.5" />New Video</button>
              </div>
            </div>

            {/* Stage progress bar */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-3 sm:p-4">
              <div className="flex gap-1 sm:gap-1.5 overflow-x-auto no-scrollbar">
                {PROD_STAGES.map(stage => {
                  const count = prodJobs.filter(j => j.stage === stage).length;
                  return (
                    <div key={stage} className="flex-1 min-w-[60px]">
                      <div className={`text-center p-1.5 sm:p-2 rounded-lg border transition-all ${count > 0 ? stageColor[stage] : "bg-white/[0.02] border-white/5 text-white/20"}`}>
                        <span className="text-sm sm:text-base">{stageIcon[stage]}</span>
                        <p className="text-[9px] sm:text-[10px] font-medium mt-0.5 uppercase tracking-wider truncate">{stage}</p>
                        <p className="text-xs sm:text-sm font-bold">{count}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* CARD VIEW — mobile-first */}
            {pipelineView === "cards" && (
              <div className="space-y-3">
                {prodJobs.length === 0 && (
                  <div className="text-center py-12 bg-white/5 border border-white/10 rounded-xl">
                    <Layers className="w-10 h-10 text-white/10 mx-auto mb-3" />
                    <p className="text-sm text-white/30">No production jobs yet</p>
                    <p className="text-xs text-white/15 mt-1">Click "New Video" to start your first production</p>
                  </div>
                )}
                {prodJobs.map((j: any) => {
                  const stageIdx = PROD_STAGES.indexOf(j.stage);
                  const progress = Math.round(((stageIdx + 1) / PROD_STAGES.length) * 100);
                  return (
                    <div key={j.id} className="bg-white/5 border border-white/10 rounded-xl p-4 hover:border-white/20 transition-all">
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-semibold truncate">{j.title}</p>
                          <p className="text-xs text-white/40 mt-0.5">{j.channel}</p>
                        </div>
                        <span className={`text-[10px] px-2 py-1 rounded-full border font-medium shrink-0 ${stageColor[j.stage] || "text-white/40 bg-white/10 border-white/10"}`}>
                          {stageIcon[j.stage]} {j.stage.toUpperCase()}
                        </span>
                      </div>
                      {/* Progress bar */}
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] text-white/30">Progress</span>
                          <span className="text-[10px] text-white/40 font-medium">{progress}%</span>
                        </div>
                        <div className="w-full h-2 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all" style={{width:`${progress}%`}} />
                        </div>
                        {/* Stage dots */}
                        <div className="flex justify-between mt-1.5">
                          {PROD_STAGES.map((s, i) => (
                            <div key={s} className={`w-1.5 h-1.5 rounded-full ${i <= stageIdx ? "bg-cyan-400" : "bg-white/10"}`} title={s} />
                          ))}
                        </div>
                      </div>
                      {/* Agent + actions */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {j.current_agent_id && (
                            <>
                              <img src={getAgentAvatar(j.current_agent_id)} className="w-6 h-6 rounded-full object-cover ring-1 ring-white/10" alt="" />
                              <span className="text-[11px] text-white/50">{getHumanName(j.current_agent_id) || j.current_agent_name || j.current_agent_id}</span>
                            </>
                          )}
                          {!j.current_agent_id && <span className="text-[11px] text-white/30">No agent assigned</span>}
                        </div>
                        <div className="flex items-center gap-1.5">
                          {j.stage === "review" && (
                            <button onClick={() => fetch(`/api/production/jobs/${j.id}/approve`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).then(refreshJobs).catch(()=>{})} className="text-[10px] px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-500 text-white font-medium transition-all">Approve</button>
                          )}
                          {j.stage !== "published" && j.stage !== "review" && (
                            <button onClick={() => fetch(`/api/production/jobs/${j.id}/advance`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).then(refreshJobs).catch(()=>{})} className="text-[10px] px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white/60 font-medium transition-all">Advance</button>
                          )}
                          {j.stage !== "published" && (
                            <button onClick={() => fetch(`/api/production/jobs/${j.id}/reject`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({notes:"Manual rejection"})}).then(refreshJobs).catch(()=>{})} className="text-[10px] px-2 py-1.5 rounded-lg hover:bg-red-500/10 text-white/30 hover:text-red-400 transition-all">Reject</button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* TABLE VIEW — desktop optimized */}
            {pipelineView === "table" && (
              <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                <div className="hidden sm:grid grid-cols-12 gap-4 px-6 py-3 border-b border-white/10 text-xs text-white/40 font-medium uppercase tracking-wider">
                  <div className="col-span-3">Title</div><div className="col-span-2">Channel</div><div className="col-span-2">Stage</div><div className="col-span-2">Agent</div><div className="col-span-1">Progress</div><div className="col-span-2 text-right">Actions</div>
                </div>
                {prodJobs.length === 0 && <div className="px-6 py-12 text-center text-white/30">No production jobs yet.</div>}
                {prodJobs.map((j: any) => {
                  const stageIdx = PROD_STAGES.indexOf(j.stage);
                  const progress = Math.round(((stageIdx + 1) / PROD_STAGES.length) * 100);
                  return (
                    <div key={j.id} className="grid grid-cols-1 sm:grid-cols-12 gap-2 sm:gap-4 px-4 sm:px-6 py-3 border-b border-white/5 hover:bg-white/5 transition-all items-center">
                      <div className="sm:col-span-3 text-sm font-medium truncate">{j.title}</div>
                      <div className="sm:col-span-2 text-xs text-white/50">{j.channel}</div>
                      <div className="sm:col-span-2"><span className={`text-[10px] px-2 py-1 rounded-full border ${stageColor[j.stage] || "text-white/40 bg-white/10 border-white/10"}`}>{j.stage.toUpperCase()}</span></div>
                      <div className="sm:col-span-2 text-[11px] text-white/40 truncate">{getHumanName(j.current_agent_id) || j.current_agent_name || "—"}</div>
                      <div className="sm:col-span-1"><div className="w-full h-2 bg-white/10 rounded-full overflow-hidden"><div className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 rounded-full transition-all" style={{width:`${progress}%`}} /></div></div>
                      <div className="sm:col-span-2 flex items-center gap-1.5 justify-end">
                        {j.stage === "review" && <button onClick={() => fetch(`/api/production/jobs/${j.id}/approve`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).then(refreshJobs).catch(()=>{})} className="text-[10px] px-2.5 py-1 rounded-lg bg-green-600 hover:bg-green-500 text-white font-medium">Approve</button>}
                        {j.stage !== "published" && j.stage !== "review" && <button onClick={() => fetch(`/api/production/jobs/${j.id}/advance`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).then(refreshJobs).catch(()=>{})} className="text-[10px] px-2.5 py-1 rounded-lg bg-white/10 hover:bg-white/20 text-white/60">Advance</button>}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* KANBAN BOARD VIEW */}
            {pipelineView === "kanban" && (
              <div className="overflow-x-auto -mx-3 px-3 pb-4">
                <div className="flex gap-3" style={{ minWidth: PROD_STAGES.length * 180 }}>
                  {PROD_STAGES.map(stage => {
                    const jobs = prodJobs.filter(j => j.stage === stage);
                    return (
                      <div key={stage} className="flex-1 min-w-[160px]">
                        <div className={`rounded-t-lg p-2 border-b-2 ${stageColor[stage] || "bg-white/5 border-white/10"} text-center`}>
                          <span className="text-sm">{stageIcon[stage]}</span>
                          <p className="text-[10px] font-bold uppercase tracking-wider mt-0.5">{stage}</p>
                          <p className="text-[9px] text-white/40">{jobs.length} job{jobs.length !== 1 ? 's' : ''}</p>
                        </div>
                        <div className="space-y-2 mt-2 min-h-[100px]">
                          {jobs.map((j: any) => (
                            <div key={j.id} className="bg-white/5 border border-white/10 rounded-lg p-3 hover:border-white/20 transition-all">
                              <p className="text-xs font-medium leading-tight">{j.title}</p>
                              <p className="text-[9px] text-white/30 mt-1">{j.channel}</p>
                              {j.current_agent_id && (
                                <div className="flex items-center gap-1.5 mt-2">
                                  <img src={getAgentAvatar(j.current_agent_id)} className="w-4 h-4 rounded-full object-cover" alt="" />
                                  <span className="text-[9px] text-white/40 truncate">{getHumanName(j.current_agent_id) || j.current_agent_name}</span>
                                </div>
                              )}
                              <div className="flex gap-1 mt-2">
                                {stage === "review" && <button onClick={() => fetch(`/api/production/jobs/${j.id}/approve`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).then(refreshJobs).catch(()=>{})} className="text-[9px] px-2 py-1 rounded bg-green-600/80 hover:bg-green-500 text-white">Approve</button>}
                                {stage !== "published" && stage !== "review" && <button onClick={() => fetch(`/api/production/jobs/${j.id}/advance`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"}).then(refreshJobs).catch(()=>{})} className="text-[9px] px-2 py-1 rounded bg-white/10 hover:bg-white/20 text-white/50">Advance</button>}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Static pipeline items (planning) */}
            {pipeline.length > 0 && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-white/50">Planning Pipeline</h3>
                  <div className="flex gap-1.5 flex-wrap">
                    <button onClick={() => setFilterStatus("ALL")} className={`text-[10px] px-2 py-1 rounded-full border transition-colors ${filterStatus==="ALL" ? "bg-white/15 text-white border-white/25" : "border-white/10 text-white/40"}`}>ALL</button>
                    {STATUSES.map(s => (<button key={s} onClick={() => setFilterStatus(s)} className={`text-[10px] px-2 py-1 rounded-full border transition-colors ${filterStatus===s ? SC[s] : "border-white/10 text-white/30"}`}>{s}</button>))}
                  </div>
                </div>
                <div className="space-y-2">
                  {filteredPipeline.map(item => (
                    <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-white/5 hover:border-white/15 transition-all">
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <div className={`w-2 h-2 rounded-full shrink-0 ${item.status==="LIVE" ? "bg-red-500 animate-pulse" : "bg-white/20"}`} />
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">{item.title}</p>
                          <p className="text-[10px] text-white/30">{item.channel} &middot; {item.date}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full border ${SC[item.status]}`}>{item.status}</span>
                        <button onClick={() => setEditItem(item)} className="p-1 rounded hover:bg-white/10"><Edit3 className="w-3.5 h-3.5 text-white/30" /></button>
                        <button onClick={() => handleDelete(item.id)} className="p-1 rounded hover:bg-red-500/10"><Trash2 className="w-3.5 h-3.5 text-white/30" /></button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
          );
        })()}

        {tab === "channels" && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold">Channel Management</h2>
            <div className="grid grid-cols-1 gap-6">
              {channels.map(c => (
                <div key={c.id} className="bg-white/5 border border-white/10 rounded-xl p-6 hover:border-white/20 transition-all">
                  <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${c.color} flex items-center justify-center`}><Youtube className="w-6 h-6" /></div>
                      <div><h3 className="text-lg font-semibold">{c.name}</h3><p className="text-sm text-white/40">Publishing {c.freq}</p></div>
                    </div>
                    <span className="text-green-400 text-sm font-medium flex items-center gap-1"><ArrowUpRight className="w-4 h-4" />{c.growth}</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                    {[["Subscribers",c.subs],["Total Views",c.views],["Videos",c.vids],["Avg CTR",c.ctr],["Est. Revenue",c.revenue],["Next Upload",c.nextVideo]].map(([l,v]) => (
                      <div key={l} className="bg-white/5 rounded-lg p-4"><p className="text-xs text-white/40 mb-1">{l}</p><p className="text-xl font-bold">{v}</p></div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "skills" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold">Agent Skills & Growth</h2>
            </div>
            {/* Growth Leaderboard */}
            <div className="bg-white/5 border border-white/10 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-white/70 mb-4 uppercase tracking-wider">Growth Leaderboard</h3>
              {growthBoard.length === 0 && <p className="text-sm text-white/30">Loading leaderboard...</p>}
              <div className="space-y-2">
                {growthBoard.slice(0, 15).map((a: any, i: number) => (
                  <div key={a.agent_id} className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/5 cursor-pointer transition-all" onClick={() => fetch(`/api/skills/agent/${a.agent_id}`).then(r=>r.json()).then(setSelectedAgentSkills).catch(()=>{})}>
                    <span className="text-xs text-white/30 w-5">{i+1}.</span>
                    <div className="flex-1">
                      <p className="text-sm font-medium">{a.agent_id}</p>
                      <p className="text-xs text-white/40">{a.total_skills} skills | Avg Lv {a.avg_level} | {a.total_xp} XP</p>
                    </div>
                    <span className="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30">Lv{a.highest_level} max</span>
                  </div>
                ))}
              </div>
            </div>
            {/* Production Leaderboard */}
            {prodBoard.length > 0 && (
              <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                <h3 className="text-sm font-semibold text-white/70 mb-4 uppercase tracking-wider">Production Leaderboard</h3>
                <div className="space-y-2">
                  {prodBoard.slice(0, 10).map((a: any, i: number) => (
                    <div key={a.agent_id} className="flex items-center gap-3 py-2 px-3 rounded-lg hover:bg-white/5">
                      <span className="text-xs text-white/30 w-5">{i+1}.</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium">{a.agent_id}</p>
                        <p className="text-xs text-white/40">{a.total_productions} productions | Avg {a.avg_quality}/10 | {a.avg_attempts} avg attempts</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {/* Selected Agent Skill Portfolio */}
            {selectedAgentSkills && (
              <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-white/70 uppercase tracking-wider">Skill Portfolio: {selectedAgentSkills.agent_id}</h3>
                  <button onClick={() => setSelectedAgentSkills(null)} className="p-1 rounded-lg hover:bg-white/10"><X className="w-4 h-4 text-white/40" /></button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                  <div className="bg-white/5 rounded-lg p-3"><p className="text-xs text-white/40">Total Skills</p><p className="text-lg font-bold">{selectedAgentSkills.summary?.total_skills || 0}</p></div>
                  <div className="bg-white/5 rounded-lg p-3"><p className="text-xs text-white/40">Avg Level</p><p className="text-lg font-bold">{selectedAgentSkills.summary?.avg_level || 0}</p></div>
                  <div className="bg-white/5 rounded-lg p-3"><p className="text-xs text-white/40">Total XP</p><p className="text-lg font-bold">{selectedAgentSkills.summary?.total_xp || 0}</p></div>
                  <div className="bg-white/5 rounded-lg p-3"><p className="text-xs text-white/40">1st Try Pass</p><p className="text-lg font-bold">{selectedAgentSkills.summary?.first_try_pass_rate || "0%"}</p></div>
                </div>
                <div className="space-y-2">
                  {(selectedAgentSkills.skills || []).map((s: any) => (
                    <div key={s.name} className="flex items-center gap-3 py-2 px-3 bg-white/5 rounded-lg">
                      <span className="text-lg">{s.level_icon}</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium">{s.name.replace(/-/g, ' ')}</p>
                        <p className="text-xs text-white/40">{s.description}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs font-medium">{s.level_name} (Lv{s.level})</p>
                        <p className="text-xs text-white/40">{s.xp} XP{s.xp_to_next ? ` / ${s.xp_to_next}` : ''}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {tab === "automation" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold mb-1">Automation Pipeline</h2>
              <p className="text-sm text-white/50">Trigger each stage of your video production workflow. Connect your API keys to activate.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {AUTOMATIONS.map(a => {
                const state = autoStates[a.id];
                return (
                  <div key={a.id} className="bg-white/5 border border-white/10 rounded-xl p-5 hover:border-white/20 transition-all">
                    <div className="flex items-center gap-4 mb-4">
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${a.color} flex items-center justify-center`}><a.icon className="w-6 h-6" /></div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2"><span className="text-xs text-white/40">{a.step}</span></div>
                        <p className="text-sm font-semibold">{a.name}</p>
                        <p className="text-xs text-white/50">{a.desc}</p>
                      </div>
                      {state === "done" && <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />}
                      {state === "running" && <RefreshCw className="w-5 h-5 text-blue-400 flex-shrink-0 animate-spin" />}
                      {state === "idle" && <AlertCircle className="w-5 h-5 text-white/20 flex-shrink-0" />}
                    </div>
                    <button
                      onClick={() => startAutomation(a.id)}
                      disabled={state === "running"}
                      className={`w-full py-2.5 rounded-lg text-sm font-medium transition-all ${state==="running" ? "bg-white/5 text-white/30 cursor-not-allowed" : state==="done" ? "bg-green-600/20 text-green-400 border border-green-500/30 hover:bg-green-600/30" : "bg-white/10 hover:bg-white/20 text-white border border-white/10"}`}
                    >
                      {state==="running" ? "Running..." : state==="done" ? "Completed ✓" : `Run ${a.name}`}
                    </button>
                  </div>
                );
              })}
            </div>
            {/* Topic input */}
            <div className="bg-[#0D1829] border border-cyan-500/20 rounded-xl p-4">
              <p className="text-sm text-cyan-400 font-medium mb-2">Video Topic (optional — set once, apply to any step)</p>
              <div className="flex gap-2">
                <input
                  value={pipelineTopic}
                  onChange={e => setPipelineTopic(e.target.value)}
                  placeholder="e.g. How to use Claude for content creation"
                  className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
                />
                {pipelineTopic && <button onClick={() => setPipelineTopic("")} className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/40 text-xs border border-white/10">Clear</button>}
              </div>
            </div>

            {/* Pipeline result */}
            {pipelineResult && (
              <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm text-green-400 font-medium">Pipeline Output</p>
                  <button onClick={() => setPipelineResult(null)} className="text-white/30 hover:text-white/60 text-xs">Dismiss</button>
                </div>
                <pre className="text-[10px] text-white/50 overflow-auto max-h-64 whitespace-pre-wrap">{JSON.stringify(pipelineResult.data, null, 2)}</pre>
              </div>
            )}
          </div>
        )}

        {tab === "analytics" && (
          <div className="space-y-6">
            <h2 className="text-xl font-bold">Analytics Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h3 className="text-sm font-medium text-white/60 mb-4">Projected Revenue (12 months)</h3>
                <div className="h-48 flex items-end gap-1.5">
                  {[0,0,0,0,100,300,800,1500,2500,4000,6000,9000].map((h,i) => (
                    <div key={i} className="flex-1 bg-gradient-to-t from-blue-600 to-cyan-400 rounded-t-sm opacity-70 hover:opacity-100 transition-all" style={{height: `${Math.max((h/9000)*100, 2)}%`}} />
                  ))}
                </div>
                <div className="flex justify-between mt-3 text-xs text-white/30">
                  <span>Apr</span><span>Jun</span><span>Aug</span><span>Oct</span><span>Dec</span><span>Feb</span>
                </div>
              </div>
              <div className="bg-white/5 border border-white/10 rounded-xl p-6">
                <h3 className="text-sm font-medium text-white/60 mb-4">Subscriber Growth Target</h3>
                <div className="h-48 flex items-end gap-1.5">
                  {[0,0,100,300,700,1200,2000,3500,6000,10000,18000,30000].map((h,i) => (
                    <div key={i} className="flex-1 bg-gradient-to-t from-green-600 to-emerald-400 rounded-t-sm opacity-70 hover:opacity-100 transition-all" style={{height:`${Math.max((h/30000)*100, 2)}%`}} />
                  ))}
                </div>
                <div className="flex justify-between mt-3 text-xs text-white/30">
                  <span>Apr</span><span>Jun</span><span>Aug</span><span>Oct</span><span>Dec</span><span>Feb</span>
                </div>
              </div>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-xl p-6">
              <h3 className="text-sm font-medium text-white/60 mb-4">Revenue Milestones</h3>
              <div className="space-y-3">
                {[
                  { label:"Month 3 — First affiliate conversion", target:"$50–$200", status:"upcoming" },
                  { label:"Month 6 — YouTube monetized (YPP)", target:"$300–$800/mo", status:"upcoming" },
                  { label:"Month 12 — First sponsorship", target:"$500–$2,500/video", status:"upcoming" },
                  { label:"Month 18 — Agency at scale", target:"$5,000–$15,000/mo", status:"upcoming" },
                ].map((m,i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                    <div className="flex items-center gap-3">
                      <span className="text-white/30 text-sm w-6 font-mono">#{i+1}</span>
                      <span className="text-sm font-medium">{m.label}</span>
                    </div>
                    <span className="text-sm text-green-400 font-medium">{m.target}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ===== AGENTS TAB ===== */}
        {tab === "agents" && (
          <div className="space-y-6">
            {/* Sub-nav */}
            <div className="flex items-center justify-between gap-2">
              <div className="flex gap-1.5 overflow-x-auto no-scrollbar">
                {(["chat","directory","departments","org"] as const).map(v => (
                  <button key={v} onClick={() => setAgentView(v)} className={`px-2.5 md:px-3 py-1.5 rounded-lg text-[11px] md:text-xs font-medium transition-all whitespace-nowrap ${agentView === v ? "bg-white/10 text-white" : "text-white/50 hover:text-white/70"}`}>
                    {{ chat: "Command", directory: "Tier", departments: "Dept", org: "Org" }[v]}
                  </button>
                ))}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <a href="/agents" className="flex items-center gap-1.5 text-[10px] md:text-xs text-white/30 hover:text-white/60 transition-all"><ExternalLink className="w-3 h-3" /> Full Directory</a>
                <a href="/org" className="flex items-center gap-1.5 text-[10px] md:text-xs text-white/30 hover:text-white/60 transition-all"><ExternalLink className="w-3 h-3" /> Org Chart</a>
                <span className="text-xs text-white/30 hidden sm:block ml-1">{agents.length} agents</span>
              </div>
            </div>

            {/* COMMAND CENTER — Single prompt → CEO delegates */}
            {agentView === "chat" && (
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                {/* Thread list — email inbox style */}
                <div className="lg:col-span-1 bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                  <div className="p-3 border-b border-white/10 flex items-center justify-between">
                    <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider">Inbox</h3>
                    <span className="text-[9px] text-white/20">{threads.length} threads</span>
                  </div>
                  <div className="max-h-[500px] overflow-y-auto">
                    <button onClick={() => setActiveThread(null)} className={`w-full text-left px-3 py-3 border-b border-white/5 hover:bg-white/5 transition-all ${!activeThread ? "bg-white/10" : ""}`}>
                      <div className="flex items-center gap-2">
                        <Plus className="w-3 h-3 text-blue-400" />
                        <span className="text-sm text-blue-400 font-medium">New Task</span>
                      </div>
                    </button>
                    {threads.map(t => {
                      const firstAgent = t.participants?.[0];
                      const isActive = activeThread?.id === t.id;
                      return (
                        <button key={t.id} onClick={() => {
                          fetch(`/api/threads/${t.id}`).then(r => r.json()).then(setActiveThread).catch(() => {});
                        }} className={`w-full text-left px-3 py-3 border-b border-white/5 hover:bg-white/5 transition-all ${isActive ? "bg-white/10 border-l-2 border-l-purple-500" : ""}`}>
                          <div className="flex items-start gap-2.5">
                            <div className="flex -space-x-1.5 shrink-0 mt-0.5">
                              {t.participants?.slice(0, 3).map((pid: string) => (
                                <img key={pid} src={getAgentAvatar(pid)} className="w-6 h-6 rounded-full object-cover ring-1 ring-[#0a0a0a]" alt="" />
                              ))}
                            </div>
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center justify-between">
                                <p className="text-[11px] font-semibold truncate">{t.subject?.replace('[Strategy] ','').replace('PEDRO DIRECTIVE: ','').replace('PRIORITY: ','')}</p>
                              </div>
                              <div className="flex items-center gap-1.5 mt-0.5">
                                <span className="text-[9px] text-white/25">{t.participants?.length || 0} agents</span>
                                <span className="text-[9px] text-white/15">·</span>
                                <span className="text-[9px] text-white/20">{t.updated_at ? new Date(t.updated_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : ''}</span>
                              </div>
                            </div>
                            <div className="w-2 h-2 rounded-full bg-purple-500 shrink-0 mt-1.5" />
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Main chat area */}
                <div className="lg:col-span-3 bg-white/5 border border-white/10 rounded-xl flex flex-col" style={{ minHeight: 520 }}>
                  {!activeThread ? (
                    /* New task prompt + recommended prompts + tools */
                    <div className="flex-1 overflow-y-auto p-6 space-y-6">
                      {/* Header */}
                      <div className="text-center">
                        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center mx-auto mb-3">
                          <Bot className="w-7 h-7" />
                        </div>
                        <h3 className="text-lg font-semibold">Command Your Empire</h3>
                        <p className="text-xs text-white/40 mt-1">Send a task and the CEO delegates to the right team automatically</p>
                      </div>

                      {/* Prompt input */}
                      <div className="max-w-lg mx-auto">
                        <textarea
                          value={agentPrompt}
                          onChange={e => setAgentPrompt(e.target.value)}
                          onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendToAgents(); } }}
                          placeholder="What do you need your team to do?"
                          rows={2}
                          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white placeholder-white/30 focus:outline-none focus:border-purple-500/50 resize-none"
                        />
                        <button onClick={sendToAgents} disabled={agentSending || !agentPrompt.trim()} className="mt-2 w-full flex items-center justify-center gap-2 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 disabled:opacity-50 px-4 py-2.5 rounded-lg text-sm font-medium transition-all">
                          <Send className="w-4 h-4" />{agentSending ? "Sending..." : "Send to CEO"}
                        </button>
                      </div>

                      {/* Recommended Prompts */}
                      <div>
                        <h4 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3">Recommended Prompts</h4>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {[
                            { cat: "Content", color: "blue", icon: "📝", prompts: [
                              "Create a content calendar for next week across all 3 channels",
                              "Write a script for a viral AI tools video targeting beginners",
                              "Analyze our top 5 performing videos and identify the winning formula",
                            ]},
                            { cat: "Growth", color: "green", icon: "📈", prompts: [
                              "Research trending topics in AI, finance, and psychology for this month",
                              "Develop a strategy to hit 100K subscribers on V-Real AI in 90 days",
                              "Audit our SEO across all channels and recommend improvements",
                            ]},
                            { cat: "Revenue", color: "amber", icon: "💰", prompts: [
                              "Identify the top 5 affiliate programs we should join for each channel",
                              "Create a digital product roadmap — courses, templates, community",
                              "Draft a sponsorship outreach pitch for AI tool companies",
                            ]},
                            { cat: "Operations", color: "purple", icon: "⚙️", prompts: [
                              "Review our production pipeline and find bottlenecks",
                              "Set up a QA checklist for all videos before publishing",
                              "Build a thumbnail A/B testing strategy for this quarter",
                            ]},
                            { cat: "Newsletter", color: "cyan", icon: "✉️", prompts: [
                              "Design a weekly newsletter strategy to convert YouTube viewers to email subscribers",
                              "Write this week's newsletter — top insights from our latest 3 videos",
                              "Create a 5-email welcome sequence for new newsletter subscribers",
                            ]},
                            { cat: "Web & Design", color: "pink", icon: "🎨", prompts: [
                              "Redesign the landing page to improve email signup conversion",
                              "Build a sales page for our upcoming AI productivity course",
                              "Audit the dashboard UI and suggest improvements",
                            ]},
                          ].map(group => (
                            <div key={group.cat} className="bg-white/[0.03] border border-white/5 rounded-lg p-3">
                              <p className="text-[10px] font-semibold text-white/50 uppercase tracking-wider mb-2">{group.icon} {group.cat}</p>
                              <div className="space-y-1.5">
                                {group.prompts.map((p, i) => (
                                  <button key={i} onClick={() => setAgentPrompt(p)} className="w-full text-left text-xs text-white/60 hover:text-white hover:bg-white/5 px-2.5 py-1.5 rounded-md transition-all leading-relaxed">
                                    {p}
                                  </button>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>

                    </div>
                  ) : (
                    /* Active thread — email chain style */
                    <>
                      <div className="px-5 py-3 border-b border-white/10">
                        <div className="flex items-center justify-between mb-2">
                          <button onClick={() => setActiveThread(null)} className="text-xs text-white/30 hover:text-white/60 flex items-center gap-1"><ChevronRight className="w-3 h-3 rotate-180" /> Back to Inbox</button>
                          <span className="text-[10px] text-white/20">{activeThread.messages?.length || 0} messages</span>
                        </div>
                        <h3 className="text-base font-bold">{activeThread.subject}</h3>
                        <div className="flex items-center gap-2 mt-2">
                          <span className="text-[10px] text-white/30">To:</span>
                          <div className="flex flex-wrap gap-1">
                            {activeThread.participants?.map(pid => {
                              const a = getAgentById(pid);
                              return a ? (
                                <span key={pid} className="inline-flex items-center gap-1.5 text-[10px] text-white/50 bg-white/5 px-2 py-0.5 rounded-full">
                                  <img src={getAgentAvatar(pid)} className="w-4 h-4 rounded-full object-cover" />
                                  {getHumanName(pid) || a.name}
                                </span>
                              ) : null;
                            })}
                          </div>
                        </div>
                      </div>
                      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
                        {activeThread.messages?.map((msg, idx) => {
                          const isUser = msg.sender_type === "user";
                          const agent = msg.sender_agent_id ? getAgentById(msg.sender_agent_id) : null;
                          const tier = msg.sender_agent_id ? getAgentTier(msg.sender_agent_id) : null;
                          const ts = tier ? TIER_STYLES[tier] : null;
                          return (
                            <div key={msg.id} className={`border rounded-xl overflow-hidden ${isUser ? "border-purple-500/20 bg-purple-500/[0.03]" : "border-white/10 bg-white/[0.02]"}`}>
                              {/* Email header */}
                              <div className={`px-4 py-2.5 border-b ${isUser ? "border-purple-500/10 bg-purple-500/[0.03]" : "border-white/5 bg-white/[0.02]"} flex items-center justify-between`}>
                                <div className="flex items-center gap-3">
                                  {isUser ? (
                                    <img src="/avatars/pedro.jpg" className="w-8 h-8 rounded-full object-cover ring-2 ring-purple-500/50" alt="" />
                                  ) : (
                                    <img src={getAgentAvatar(msg.sender_agent_id || "")} className={`w-8 h-8 rounded-full object-cover ring-2 ${ts?.ring || "ring-white/10"}`} alt="" />
                                  )}
                                  <div>
                                    <div className="flex items-center gap-2">
                                      <span className="text-xs font-semibold">{isUser ? "Pedro (You)" : getHumanName(msg.sender_agent_id || "") || agent?.name || msg.sender_name}</span>
                                      {agent && <span className={`text-[8px] px-1.5 py-0 rounded-full border font-medium ${ts?.badge || ""}`}>{tier}</span>}
                                      {agent && <span className="text-[9px] text-white/25">{agent.name}</span>}
                                    </div>
                                    <span className="text-[10px] text-white/20">{msg.created_at ? new Date(msg.created_at).toLocaleString() : ""}</span>
                                  </div>
                                </div>
                                <span className="text-[9px] text-white/15">#{idx + 1}</span>
                              </div>
                              {/* Email body */}
                              <div className="px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap text-white/75">
                                {msg.content}
                              </div>
                            </div>
                          );
                        })}
                        <div ref={msgEndRef} />
                      </div>
                      <div className="px-5 py-3 border-t border-white/10 bg-white/[0.02]">
                        <p className="text-[10px] text-white/20 mb-2">Reply to thread</p>
                        <div className="flex gap-2">
                          <input type="text" value={agentPrompt} onChange={e => setAgentPrompt(e.target.value)} onKeyDown={e => { if (e.key === "Enter") sendReply(); }} placeholder="Type your response..." className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2.5 text-sm text-white placeholder-white/30 focus:outline-none focus:border-purple-500/50" />
                          <button onClick={sendReply} disabled={agentSending || !agentPrompt.trim()} className="px-5 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-all flex items-center gap-2">
                            <Send className="w-3 h-3" /> Send
                          </button>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>
            )}

            {/* AGENT DIRECTORY */}
            {agentView === "directory" && (
              <div className="space-y-8">
                {(["T1","T2","T3","T4","T5","T6","T7","T8","T9"] as Tier[]).map(tier => {
                  const tierAgents = agents.filter(a => getAgentTier(a.id) === tier);
                  if (tierAgents.length === 0) return null;
                  const ts = TIER_STYLES[tier];
                  const tierLabel = TIER_LABELS[tier];
                  return (
                    <div key={tier}>
                      <div className="flex items-center gap-3 mb-3">
                        <span className={`text-xs font-bold uppercase tracking-wider ${ts.text}`}>{tier} — {tierLabel}</span>
                        <div className="flex-1 h-px bg-white/5" />
                        <span className="text-[10px] text-white/20">{tierAgents.length} agents</span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                        {tierAgents.map(a => {
                          const tierStyle = TIER_STYLES[getAgentTier(a.id)];
                          const dept = DEPT_COLORS[a.department] || DEPT_COLORS.general;
                          return (
                            <div key={a.id} className={`${tierStyle.bg} border ${tierStyle.border} rounded-xl p-4 hover:brightness-125 transition-all`}>
                              <div className="flex items-center gap-3 mb-3">
                                <div className={`w-11 h-11 rounded-full overflow-hidden ring-2 ${tierStyle.ring} shrink-0`}>
                                  <img src={getAgentAvatar(a.id)} alt={a.name} className="w-full h-full object-cover" />
                                </div>
                                <div className="min-w-0 flex-1">
                                  <p className="text-sm font-semibold truncate">{getHumanName(a.id) || a.name}</p>
                                  <p className="text-[10px] text-white/40 truncate">{a.name}</p>
                                </div>
                              </div>
                              <div className="flex flex-wrap gap-1.5 mb-2.5">
                                <span className={`text-[9px] px-2 py-0.5 rounded-full border font-medium ${tierStyle.badge}`}>{tier}</span>
                                <span className="text-[9px] px-2 py-0.5 rounded-full border border-white/10 text-white/50 flex items-center gap-1">
                                  <span className={`w-1.5 h-1.5 rounded-full ${dept.dot}`} />{dept.label}
                                </span>
                              </div>
                              <p className="text-[10px] text-white/30 truncate">{a.role}</p>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* ORG CHART */}
            {/* DEPARTMENTS VIEW */}
            {agentView === "departments" && (
              <div className="space-y-6">
                {(["executive","content","operations","analytics","monetization","admin"] as const).map(deptKey => {
                  const dept = DEPT_COLORS[deptKey];
                  const deptAgents = agents.filter(a => a.department === deptKey);
                  if (deptAgents.length === 0) return null;
                  // Sort by tier within department
                  const tierOrder: Record<Tier, number> = { "T1": 1, "T2": 2, "T3": 3, "T4": 4, "T5": 5, "T6": 6, "T7": 7, "T8": 8, "T9": 9 };
                  const sorted = [...deptAgents].sort((a, b) => tierOrder[getAgentTier(a.id)] - tierOrder[getAgentTier(b.id)]);
                  // Find the department head (highest tier)
                  const head = sorted[0];
                  const rest = sorted.slice(1);

                  return (
                    <div key={deptKey} className="bg-white/[0.02] border border-white/10 rounded-2xl overflow-hidden">
                      {/* Department header */}
                      <div className="px-5 py-3 border-b border-white/10 flex items-center justify-between" style={{ borderLeftWidth: 3, borderLeftColor: dept.dot.replace("bg-", "").includes("yellow") ? "#facc15" : dept.dot.replace("bg-", "").includes("blue") ? "#60a5fa" : dept.dot.replace("bg-", "").includes("amber") ? "#fbbf24" : dept.dot.replace("bg-", "").includes("emerald") ? "#34d399" : dept.dot.replace("bg-", "").includes("red") ? "#f87171" : "#94a3b8" }}>
                        <div className="flex items-center gap-3">
                          <span className={`w-2.5 h-2.5 rounded-full ${dept.dot}`} />
                          <h3 className="text-sm font-bold uppercase tracking-wider">{dept.label} Department</h3>
                        </div>
                        <span className="text-[10px] text-white/30">{deptAgents.length} members</span>
                      </div>

                      {/* Department head */}
                      <div className="px-5 py-3 border-b border-white/5 bg-white/[0.02]">
                        <p className="text-[9px] text-white/30 uppercase tracking-wider mb-2">Department Head</p>
                        <div className="flex items-center gap-3">
                          <div className={`w-12 h-12 rounded-full overflow-hidden ring-2 ${TIER_STYLES[getAgentTier(head.id)].ring}`}>
                            <img src={getAgentAvatar(head.id)} alt="" className="w-full h-full object-cover" />
                          </div>
                          <div>
                            <p className="text-sm font-semibold">{getHumanName(head.id) || head.name}</p>
                            <p className="text-[10px] text-white/40">{head.role}</p>
                            <div className="flex gap-1 mt-1">
                              <span className={`text-[8px] px-1.5 py-0 rounded-full border font-medium ${TIER_STYLES[getAgentTier(head.id)].badge}`}>{getAgentTier(head.id)}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Team members */}
                      {rest.length > 0 && (
                        <div className="px-5 py-3">
                          <p className="text-[9px] text-white/30 uppercase tracking-wider mb-2">Team ({rest.length})</p>
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                            {rest.map(a => {
                              const ts = TIER_STYLES[getAgentTier(a.id)];
                              return (
                                <div key={a.id} className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/5 hover:border-white/15 transition-all">
                                  <div className={`w-8 h-8 rounded-full overflow-hidden ring-2 ${ts.ring} shrink-0`}>
                                    <img src={getAgentAvatar(a.id)} alt="" className="w-full h-full object-cover" />
                                  </div>
                                  <div className="min-w-0 flex-1">
                                    <p className="text-xs font-medium truncate">{getHumanName(a.id) || a.name}</p>
                                    <p className="text-[9px] text-white/30 truncate">{a.role}</p>
                                  </div>
                                  <span className={`text-[7px] px-1.5 py-0 rounded-full border font-medium shrink-0 ${ts.badge}`}>{getAgentTier(a.id)}</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {agentView === "org" && (
              <div className="overflow-x-auto pb-8">
                <div className="min-w-[900px] space-y-10">
                  {agents.filter(a => !a.reports_to).map(root => {
                    const directReports = agents.filter(a => a.reports_to === root.id);
                    return (
                      <div key={root.id}>
                        {/* CEO at top center */}
                        <div className="flex justify-center mb-2">
                          <div style={{ width: 220 }}><BracketCard agent={root} /></div>
                        </div>
                        {/* Connector line down from CEO */}
                        {directReports.length > 0 && (
                          <div className="flex justify-center mb-2"><div className="w-px h-6 bg-white/15" /></div>
                        )}
                        {/* Horizontal rail connecting all VPs */}
                        {directReports.length > 1 && (
                          <div className="flex justify-center mb-0">
                            <div className="h-px bg-white/15" style={{ width: `${Math.min(directReports.length * 220, 900)}px` }} />
                          </div>
                        )}
                        {/* VP branches */}
                        <div className="flex justify-center gap-4 flex-wrap">
                          {directReports.map(vp => {
                            const vpReports = agents.filter(a => a.reports_to === vp.id);
                            return (
                              <div key={vp.id} className="flex flex-col items-center">
                                {/* Connector down to VP */}
                                <div className="w-px h-4 bg-white/15" />
                                <div style={{ width: 210 }}><BracketCard agent={vp} /></div>
                                {/* VP's reports */}
                                {vpReports.length > 0 && (
                                  <>
                                    <div className="w-px h-3 bg-white/15" />
                                    <div className="flex flex-col gap-1.5 items-center">
                                      {vpReports.map((rep, ri) => (
                                        <div key={rep.id} className="flex items-center gap-0">
                                          {/* Horizontal connector */}
                                          <div className="w-3 h-px bg-white/15" />
                                          <div style={{ width: 195 }}><BracketCard agent={rep} /></div>
                                        </div>
                                      ))}
                                    </div>
                                  </>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ===== NEWSLETTER TAB ===== */}
        {tab === "newsletter" && (
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2"><Mail className="w-5 h-5 text-cyan-400" /> Newsletter Command Center</h2>
                <p className="text-sm text-white/40 mt-1">Powered by Sarah Lindgren — Newsletter Strategist Agent</p>
              </div>
              <div className="flex items-center gap-2">
                <img src="/avatars/newsletter-strategist-agent.jpg" className="w-8 h-8 rounded-full ring-2 ring-cyan-500/50 object-cover" alt="" />
                <div className="text-right">
                  <p className="text-xs font-medium">Sarah Lindgren</p>
                  <p className="text-[10px] text-white/30">Newsletter Strategist</p>
                </div>
              </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: "Subscribers", value: "0", change: "Starting", icon: UserPlus, color: "cyan" },
                { label: "Open Rate", value: "—", change: "No data yet", icon: MailOpen, color: "blue" },
                { label: "Click Rate", value: "—", change: "No data yet", icon: TrendingUp, color: "purple" },
                { label: "Issues Sent", value: "0", change: "Draft first issue", icon: Send, color: "green" },
              ].map(s => (
                <div key={s.label} className="bg-white/5 border border-white/10 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <s.icon className="w-4 h-4 text-white/30" />
                    <span className="text-[10px] text-white/30">{s.change}</span>
                  </div>
                  <p className="text-xl font-bold">{s.value}</p>
                  <p className="text-xs text-white/40 mt-0.5">{s.label}</p>
                </div>
              ))}
            </div>

            {/* Main grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Write & Create */}
              <div className="lg:col-span-2 space-y-4">
                <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                  <h3 className="text-sm font-semibold mb-4 flex items-center gap-2"><PenTool className="w-4 h-4 text-cyan-400" /> Create Content</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {[
                      { title: "Write Weekly Issue", desc: "Pull insights from latest videos, add exclusive tips, tease upcoming content", icon: FileText, color: "from-cyan-600 to-blue-600", prompt: "Write this week's newsletter issue. Pull the best insights from our recent videos, add an exclusive tip, tease upcoming content, and include one curated resource recommendation. Format it ready to send with subject line options." },
                      { title: "Write Welcome Sequence", desc: "5-email automated series for new subscribers", icon: Mail, color: "from-purple-600 to-pink-600", prompt: "Design a complete 5-email automated welcome sequence for new subscribers. Each email should deliver value, build trust, and gradually introduce our products and community. Include subject lines, send timing, and full copy for each email." },
                      { title: "Write Product Launch Email", desc: "Announcement + sales email for digital product drops", icon: Megaphone, color: "from-amber-600 to-orange-600", prompt: "Write a product launch email sequence (3 emails: teaser, launch day, last chance) for our next digital product. Include subject lines, preview text, full copy, and CTAs. Make it feel exclusive to newsletter subscribers." },
                      { title: "Write Re-engagement Email", desc: "Win back inactive subscribers who stopped opening", icon: RefreshCw, color: "from-red-600 to-pink-600", prompt: "Write a 3-email re-engagement sequence for subscribers who haven't opened in 30+ days. Include a compelling reason to come back, an exclusive offer, and a final 'should we remove you?' email. Focus on delivering immediate value." },
                    ].map(item => (
                      <button key={item.title} onClick={() => { setTab("agents"); setAgentPrompt(item.prompt); }} className="flex items-start gap-3 p-4 bg-white/[0.03] border border-white/5 hover:border-white/20 rounded-xl text-left transition-all group">
                        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${item.color} flex items-center justify-center shrink-0`}>
                          <item.icon className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-sm font-medium group-hover:text-white transition-colors">{item.title}</p>
                          <p className="text-[10px] text-white/30 mt-0.5 leading-relaxed">{item.desc}</p>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Strategy & Growth */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                  <h3 className="text-sm font-semibold mb-4 flex items-center gap-2"><TrendingUp className="w-4 h-4 text-green-400" /> Growth & Strategy</h3>
                  <div className="space-y-2">
                    {[
                      { title: "30-Day Growth Plan", desc: "Grow list by 1,000 subscribers with lead magnets, CTAs, and landing pages", prompt: "Create a detailed 30-day plan to grow our email list by 1,000 subscribers. Include lead magnet ideas for each channel, video CTA scripts, landing page strategy, and cross-promotion tactics. Break it into weekly milestones." },
                      { title: "Lead Magnet Ideas", desc: "Create irresistible freebies for each channel to drive signups", prompt: "Design 3 lead magnets for each of our 3 channels (V-Real AI, Cash Flow Code, Mind Shift). Each should solve a specific problem, be quick to create, and have high perceived value. Include titles, formats, and promotion strategy." },
                      { title: "Monetization Strategy", desc: "Plan newsletter revenue streams — sponsors, products, affiliates", prompt: "Create a newsletter monetization roadmap. Include: when to add sponsors (subscriber threshold), how to price newsletter ad placements, which affiliate products to feature, and how to use the newsletter to drive digital product sales. Include revenue projections." },
                      { title: "Content Calendar", desc: "Plan 4 weeks of newsletter content with themes and CTAs", prompt: "Build a 4-week newsletter content calendar. Each week should have: a theme tied to our video content, 1 exclusive insight, 1 curated resource, 1 product/affiliate mention, and a specific CTA. Alternate between educational, inspirational, and promotional tones." },
                      { title: "A/B Testing Plan", desc: "Subject lines, send times, formats — systematic testing roadmap", prompt: "Design a 30-day A/B testing plan for our newsletter. Test subject line styles, send day/time, content format (long vs short, text vs visual), CTA placement, and personalization. Include hypothesis, test design, and success metrics for each test." },
                      { title: "Segmentation Strategy", desc: "Split list by interest, engagement, and customer status", prompt: "Design an email list segmentation strategy. Define segments by: channel interest (AI/Finance/Psychology), engagement level (active/lukewarm/cold), customer status (free/paid), and content preference. For each segment, recommend different content approaches and frequencies." },
                    ].map(item => (
                      <button key={item.title} onClick={() => { setTab("agents"); setAgentPrompt(item.prompt); }} className="w-full flex items-center justify-between px-4 py-3 bg-white/[0.02] border border-white/5 hover:border-white/15 rounded-lg text-left transition-all group">
                        <div>
                          <p className="text-xs font-medium group-hover:text-white transition-colors">{item.title}</p>
                          <p className="text-[10px] text-white/25 mt-0.5">{item.desc}</p>
                        </div>
                        <ChevronRight className="w-3 h-3 text-white/15 group-hover:text-white/40 shrink-0" />
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right sidebar */}
              <div className="space-y-4">
                {/* Quick Send */}
                <div className="bg-gradient-to-b from-cyan-500/10 to-blue-500/5 border border-cyan-500/20 rounded-xl p-5">
                  <h3 className="text-sm font-semibold mb-3 flex items-center gap-2"><Sparkles className="w-4 h-4 text-cyan-400" /> Quick Draft</h3>
                  <p className="text-[10px] text-white/40 mb-3">Describe what you want and the Newsletter Strategist will draft it</p>
                  <textarea
                    value={agentPrompt}
                    onChange={e => setAgentPrompt(e.target.value)}
                    placeholder="e.g. Write a newsletter about our latest AI tools video with a special discount code..."
                    rows={4}
                    className="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-cyan-500/50 resize-none mb-2"
                  />
                  <button onClick={() => { setTab("agents"); sendToAgents(); }} disabled={!agentPrompt.trim()} className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 px-3 py-2 rounded-lg text-xs font-medium transition-all">
                    <Send className="w-3 h-3" /> Send to Newsletter Team
                  </button>
                </div>

                {/* Email Templates */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                  <h3 className="text-sm font-semibold mb-3">Email Templates</h3>
                  <div className="space-y-2">
                    {[
                      { name: "Weekly Digest", type: "Recurring", color: "bg-blue-500" },
                      { name: "Video Launch", type: "Triggered", color: "bg-purple-500" },
                      { name: "Product Promo", type: "Campaign", color: "bg-amber-500" },
                      { name: "Welcome Series", type: "Automation", color: "bg-green-500" },
                      { name: "Re-engagement", type: "Automation", color: "bg-red-500" },
                    ].map(t => (
                      <div key={t.name} className="flex items-center justify-between px-3 py-2 bg-white/[0.03] rounded-lg">
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${t.color}`} />
                          <span className="text-xs">{t.name}</span>
                        </div>
                        <span className="text-[9px] text-white/25 px-1.5 py-0.5 border border-white/10 rounded">{t.type}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Automation Status */}
                <div className="bg-white/5 border border-white/10 rounded-xl p-5">
                  <h3 className="text-sm font-semibold mb-3">Automations</h3>
                  <div className="space-y-3">
                    {[
                      { name: "Welcome Sequence", status: "Not set up", statusColor: "text-white/25" },
                      { name: "Weekly Digest", status: "Not set up", statusColor: "text-white/25" },
                      { name: "Video Notification", status: "Not set up", statusColor: "text-white/25" },
                      { name: "Re-engagement Flow", status: "Not set up", statusColor: "text-white/25" },
                    ].map(a => (
                      <div key={a.name} className="flex items-center justify-between">
                        <span className="text-xs text-white/60">{a.name}</span>
                        <span className={`text-[10px] ${a.statusColor}`}>{a.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ===== ACTIVITY TAB ===== */}
        {tab === "activity" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2"><Activity className="w-5 h-5 text-purple-400" /> Workforce Activity</h2>
                <p className="text-sm text-white/40 mt-1">Real-time view of what every agent is doing — Goal: 1B subscribers</p>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                <span className="text-xs text-green-400 font-medium">Autopilot ON</span>
              </div>
            </div>

            {/* Stats */}
            {activityData && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-4">
                  <Play className="w-4 h-4 text-green-400 mb-2" />
                  <p className="text-2xl font-bold">{activityData.running_count}</p>
                  <p className="text-xs text-white/40">Running Now</p>
                </div>
                <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
                  <CheckCircle className="w-4 h-4 text-blue-400 mb-2" />
                  <p className="text-2xl font-bold">{activityData.completed_today}</p>
                  <p className="text-xs text-white/40">Completed Today</p>
                </div>
                <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
                  <AlertTriangle className="w-4 h-4 text-amber-400 mb-2" />
                  <p className="text-2xl font-bold">{activityData.pending_escalations}</p>
                  <p className="text-xs text-white/40">Needs Review</p>
                </div>
                <div className="bg-purple-500/5 border border-purple-500/20 rounded-xl p-4">
                  <Users className="w-4 h-4 text-purple-400 mb-2" />
                  <p className="text-2xl font-bold">{activityData.total_agents}</p>
                  <p className="text-xs text-white/40">Active Agents</p>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Agent Status Board */}
              <div className="lg:col-span-2">
                <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                  <div className="px-5 py-3 border-b border-white/10 flex items-center justify-between">
                    <h3 className="text-sm font-semibold">Agent Status Board</h3>
                    <span className="text-[10px] text-white/30">{activityData?.agent_statuses?.length || 0} agents</span>
                  </div>
                  <div className="max-h-[500px] overflow-y-auto divide-y divide-white/5">
                    {activityData?.agent_statuses?.map(a => {
                      const tier = getAgentTier(a.id);
                      const ts = TIER_STYLES[tier];
                      const dept = DEPT_COLORS[a.department] || DEPT_COLORS.general;
                      return (
                        <div key={a.id} className="flex items-center gap-3 px-5 py-2.5 hover:bg-white/[0.02]">
                          <div className={`w-9 h-9 rounded-full overflow-hidden ring-2 ${ts.ring} shrink-0`}>
                            <img src={getAgentAvatar(a.id)} alt="" className="w-full h-full object-cover" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold truncate">{getHumanName(a.id) || a.name}</span>
                              <span className={`text-[7px] px-1.5 py-0 rounded-full border font-medium ${ts.badge}`}>{tier}</span>
                              <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${a.status === "working" ? "bg-green-400 animate-pulse" : "bg-white/20"}`} />
                            </div>
                            <div className="flex items-center gap-1.5">
                              <span className="text-[10px] text-white/40 truncate">{a.role}</span>
                              <span className="text-[10px] text-white/15">·</span>
                              <span className={`text-[9px] flex items-center gap-0.5`}><span className={`w-1 h-1 rounded-full ${dept.dot}`} /><span className="text-white/25">{dept.label}</span></span>
                            </div>
                            <p className="text-[10px] text-white/30 truncate mt-0.5">{a.current_task}</p>
                          </div>
                          <span className={`text-[9px] px-2 py-0.5 rounded-full font-medium ${a.status === "working" ? "bg-green-500/20 text-green-400" : "bg-white/5 text-white/25"}`}>
                            {a.status === "working" ? "Working" : "Done"}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              {/* Right column: Escalations + Recent Activity */}
              <div className="space-y-4">
                {/* Escalation Inbox */}
                <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl overflow-hidden">
                  <div className="px-5 py-3 border-b border-amber-500/10 flex items-center justify-between">
                    <h3 className="text-sm font-semibold flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-400" /> Escalations</h3>
                    <span className="text-[10px] text-amber-400">{activityData?.escalations?.length || 0} pending</span>
                  </div>
                  <div className="p-3 space-y-2 max-h-48 overflow-y-auto">
                    {(!activityData?.escalations || activityData.escalations.length === 0) ? (
                      <p className="text-xs text-white/20 text-center py-4">No escalations — all clear</p>
                    ) : activityData.escalations.map(e => (
                      <div key={e.id} className="bg-white/5 rounded-lg p-3">
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-xs text-white/60">{e.reason}</p>
                            <p className="text-[10px] text-white/20 mt-1">{e.agent_id}</p>
                          </div>
                          <button onClick={() => resolveEscalation(e.id)} className="text-[10px] text-green-400 hover:text-green-300 px-2 py-1 border border-green-500/20 rounded shrink-0">
                            Resolve
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recent Activity Feed */}
                <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                  <div className="px-5 py-3 border-b border-white/10">
                    <h3 className="text-sm font-semibold">Recent Activity</h3>
                  </div>
                  <div className="p-3 space-y-2 max-h-64 overflow-y-auto">
                    {activityData?.recent_runs?.map(r => (
                      <div key={r.id} className="flex items-start gap-2 py-1.5">
                        <span className={`mt-0.5 ${r.status === "complete" ? "text-green-400" : r.status === "failed" ? "text-red-400" : r.status === "escalated" ? "text-amber-400" : "text-blue-400"}`}>
                          {r.status === "complete" ? <CheckCircle className="w-3 h-3" /> : r.status === "failed" ? <XCircle className="w-3 h-3" /> : r.status === "escalated" ? <AlertTriangle className="w-3 h-3" /> : <CircleDot className="w-3 h-3" />}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-[11px] text-white/60 truncate">{r.task_name}</p>
                          {r.summary && <p className="text-[10px] text-white/25 truncate mt-0.5">{r.summary}</p>}
                        </div>
                      </div>
                    ))}
                    {(!activityData?.recent_runs || activityData.recent_runs.length === 0) && (
                      <p className="text-xs text-white/20 text-center py-4">No activity yet — trigger a task to start</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Scheduled Tasks Table */}
            <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
              <div className="px-5 py-3 border-b border-white/10 flex items-center justify-between">
                <h3 className="text-sm font-semibold">Scheduled Tasks ({scheduledTasks.length})</h3>
                <span className="text-[10px] text-white/30">{scheduledTasks.filter(t => t.enabled).length} active</span>
              </div>
              <div className="max-h-[400px] overflow-y-auto">
                <div className="hidden sm:grid grid-cols-12 gap-2 px-5 py-2 border-b border-white/5 text-[10px] text-white/30 uppercase tracking-wider font-medium">
                  <div className="col-span-3">Task</div><div className="col-span-2">Agent</div><div className="col-span-2">Schedule</div><div className="col-span-2">Last Run</div><div className="col-span-1">Status</div><div className="col-span-2 text-right">Action</div>
                </div>
                {scheduledTasks.map(t => (
                  <div key={t.id} className="grid grid-cols-1 sm:grid-cols-12 gap-2 px-5 py-2.5 border-b border-white/5 hover:bg-white/[0.02] items-center">
                    <div className="sm:col-span-3 text-xs font-medium truncate">{t.name}</div>
                    <div className="sm:col-span-2 text-[11px] text-white/40 truncate">{t.agent_name}</div>
                    <div className="sm:col-span-2 text-[10px] text-white/30 font-mono">{t.cron_expression}</div>
                    <div className="sm:col-span-2 text-[10px] text-white/25">{t.last_run ? new Date(t.last_run).toLocaleString() : "Never"}</div>
                    <div className="sm:col-span-1">
                      <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${t.enabled ? "bg-green-500/20 text-green-400" : "bg-white/5 text-white/25"}`}>
                        {t.enabled ? "On" : "Off"}
                      </span>
                    </div>
                    <div className="sm:col-span-2 flex justify-end gap-1">
                      <button onClick={() => triggerTask(t.id)} className="text-[10px] text-blue-400 hover:text-blue-300 px-2 py-0.5 border border-blue-500/20 rounded">Run Now</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ===== FEED TAB ===== */}
        {tab === "feed" && (
          <div className="flex gap-4 h-[calc(100vh-120px)] md:h-[calc(100vh-120px)]" style={{ height: "calc(100vh - 120px - env(safe-area-inset-bottom, 0px))" }}>
            {/* Channel sidebar */}
            <div className="hidden md:flex w-48 shrink-0 bg-white/5 border border-white/10 rounded-xl overflow-hidden flex-col">
              <div className="p-3 border-b border-white/10">
                <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider">Channels</h3>
              </div>
              <div className="flex-1 overflow-y-auto p-1">
                <button onClick={() => switchFeedChannel("all")} className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all flex items-center justify-between ${feedChannel === "all" ? "bg-white/10 text-white" : "text-white/50 hover:text-white/70 hover:bg-white/5"}`}>
                  <span>All Messages</span>
                  {feedUnread.total > 0 && <span className="bg-red-500 text-[9px] px-1.5 py-0.5 rounded-full font-bold">{feedUnread.total}</span>}
                </button>
                {Object.entries(FEED_CHANNELS).map(([key, ch]) => (
                  <button key={key} onClick={() => switchFeedChannel(key)} className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-all flex items-center justify-between ${feedChannel === key ? "bg-white/10 text-white" : "text-white/50 hover:text-white/70 hover:bg-white/5"}`}>
                    <span>{ch.emoji} {ch.name}</span>
                    {(feedUnread.channels[key] || 0) > 0 && <span className="bg-red-500 text-[9px] px-1.5 py-0.5 rounded-full font-bold">{feedUnread.channels[key]}</span>}
                  </button>
                ))}
              </div>
            </div>

            {/* Message stream */}
            <div className="flex-1 bg-white/5 border border-white/10 rounded-xl flex flex-col overflow-hidden">
              {/* Header */}
              <div className="px-3 md:px-5 py-3 border-b border-white/10 flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-base shrink-0">{feedChannel === "all" ? "📡" : FEED_CHANNELS[feedChannel]?.emoji || "💬"}</span>
                  <h3 className="text-sm font-semibold truncate">{feedChannel === "all" ? "All Channels" : FEED_CHANNELS[feedChannel]?.name || feedChannel}</h3>
                  <span className="text-[10px] text-white/20 hidden md:inline">— live feed from your agents</span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {/* Mobile channel picker */}
                  <select
                    value={feedChannel}
                    onChange={e => setFeedChannel(e.target.value)}
                    className="md:hidden bg-white/5 border border-white/10 rounded-lg px-2 py-1 text-[10px] text-white/60 focus:outline-none"
                  >
                    <option value="all" className="bg-[#141414]">All</option>
                    {Object.entries(FEED_CHANNELS).map(([key, val]) => (
                      <option key={key} value={key} className="bg-[#141414]">{val.emoji} {val.name}</option>
                    ))}
                  </select>
                  <button onClick={markAllRead} className="text-[10px] text-white/30 hover:text-white/60 px-2 py-1 border border-white/10 rounded whitespace-nowrap">Mark read</button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
                {feedMessages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-white/20">
                    <MessageSquare className="w-12 h-12 mb-3 opacity-20" />
                    <p className="text-sm">No messages yet</p>
                    <p className="text-[10px] mt-1">Agent updates will appear here as they work</p>
                  </div>
                ) : (
                  feedMessages.map(msg => {
                    const severityColors: Record<string, string> = {
                      info: "border-white/5",
                      warning: "border-amber-500/20 bg-amber-500/[0.02]",
                      urgent: "border-red-500/20 bg-red-500/[0.02]",
                      celebration: "border-green-500/20 bg-green-500/[0.02]",
                    };
                    const typeIcons: Record<string, string> = {
                      update: "📋", alert: "🚨", win: "🏆", request: "❓", report: "📊", milestone: "🎯",
                    };
                    return (
                      <div key={msg.id} className={`border rounded-lg p-3 ${severityColors[msg.severity] || severityColors.info} ${!msg.read ? "ring-1 ring-white/10" : ""}`}>
                        <div className="flex items-start gap-3">
                          {(() => {
                            const feedTier = msg.agent_id !== "pedro" ? getAgentTier(msg.agent_id) : null;
                            const feedTs = feedTier ? TIER_STYLES[feedTier] : null;
                            return (
                              <div className={`w-9 h-9 rounded-full overflow-hidden ring-2 ${feedTs?.ring || "ring-purple-500/60"} shrink-0`}>
                                {msg.agent_id === "pedro" ? (
                                  <img src="/avatars/pedro.jpg" className="w-full h-full object-cover" alt="" />
                                ) : (
                                  <img src={getAgentAvatar(msg.agent_id)} className="w-full h-full object-cover" alt="" />
                                )}
                              </div>
                            );
                          })()}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1 flex-wrap">
                              <span className="text-xs font-semibold">{msg.agent_id === "pedro" ? "Pedro (You)" : getHumanName(msg.agent_id) || msg.agent_name}</span>
                              {msg.agent_id !== "pedro" && (() => {
                                const ft = getAgentTier(msg.agent_id);
                                const fts = TIER_STYLES[ft];
                                return <span className={`text-[7px] px-1.5 py-0 rounded-full border font-medium ${fts.badge}`}>{ft}</span>;
                              })()}
                              <span className="text-[9px] text-white/25">{msg.agent_id !== "pedro" ? msg.agent_name : "Empire Operator"}</span>
                              <span className="text-[8px] px-1.5 py-0 rounded border border-white/10 text-white/20">{FEED_CHANNELS[msg.channel]?.emoji} {FEED_CHANNELS[msg.channel]?.name || msg.channel}</span>
                              <span className="text-[10px] text-white/15 ml-auto">{new Date(msg.created_at).toLocaleString()}</span>
                            </div>
                            <div className="text-xs text-white/60 leading-relaxed whitespace-pre-wrap">
                              <span className="mr-1">{typeIcons[msg.message_type] || "📋"}</span>
                              {msg.content}
                            </div>
                            {msg.thread_id && (
                              <button onClick={() => { setTab("agents"); fetch(`/api/threads/${msg.thread_id}`).then(r => r.json()).then(setActiveThread).catch(() => {}); }} className="text-[10px] text-purple-400 hover:text-purple-300 mt-1.5 flex items-center gap-1">
                                <ChevronRight className="w-3 h-3" /> View full thread
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Message input — Pedro can post to the feed */}
              <div className="px-5 py-3 border-t border-white/10">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={feedInput}
                    onChange={e => setFeedInput(e.target.value)}
                    onKeyDown={e => { if (e.key === "Enter") sendFeedMessage(); }}
                    placeholder="Post a message to your team..."
                    className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-xs text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50"
                  />
                  <button onClick={sendFeedMessage} disabled={!feedInput.trim()} className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg text-xs font-medium transition-all">
                    <Send className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ===== SOCIAL TAB ===== */}
        {tab === "social" && (() => {
          const platformEmojis: Record<string, string> = { youtube: "📺", instagram: "📸", facebook: "📘", tiktok: "📱", snapchat: "👻", twitter: "𝕏", linkedin: "💼", threads: "🧵" };
          const platformNames: Record<string, string> = { youtube: "YouTube", instagram: "Instagram", facebook: "Facebook", tiktok: "TikTok", snapchat: "Snapchat", twitter: "X/Twitter", linkedin: "LinkedIn", threads: "Threads" };
          const platforms = Object.keys(platformEmojis);
          const filtered = socialFilter === "all" ? socialAccounts : socialAccounts.filter(a => a.platform === socialFilter);
          const byPlatform: Record<string, SocialAccountInfo[]> = {};
          filtered.forEach(a => { if (!byPlatform[a.platform]) byPlatform[a.platform] = []; byPlatform[a.platform].push(a); });

          return (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold flex items-center gap-2"><Globe className="w-5 h-5 text-blue-400" /> Social Media Hub</h2>
                  <p className="text-sm text-white/40 mt-1">{socialAccounts.length} accounts across {platforms.length} platforms — 31 cross-followers each</p>
                </div>
              </div>

              {/* Platform stats */}
              <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2">
                {platforms.map(p => {
                  const count = socialAccounts.filter(a => a.platform === p).length;
                  const active = socialAccounts.filter(a => a.platform === p && a.status === "active").length;
                  return (
                    <button key={p} onClick={() => setSocialFilter(socialFilter === p ? "all" : p)} className={`p-3 rounded-xl border text-center transition-all ${socialFilter === p ? "bg-white/10 border-white/20" : "bg-white/[0.02] border-white/5 hover:border-white/15"}`}>
                      <span className="text-lg">{platformEmojis[p]}</span>
                      <p className="text-xs font-semibold mt-1">{platformNames[p]}</p>
                      <p className="text-[10px] text-white/30">{count} accounts</p>
                      <p className="text-[10px] text-green-400">{active} active</p>
                    </button>
                  );
                })}
              </div>

              {/* Accounts by platform */}
              {(socialFilter === "all" ? platforms : [socialFilter]).map(platform => {
                const accts = byPlatform[platform] || [];
                if (accts.length === 0) return null;
                return (
                  <div key={platform} className="bg-white/[0.02] border border-white/10 rounded-xl overflow-hidden">
                    <div className="px-5 py-3 border-b border-white/10 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-base">{platformEmojis[platform]}</span>
                        <h3 className="text-sm font-bold">{platformNames[platform]}</h3>
                        <span className="text-[10px] text-white/30">({accts.length} accounts)</span>
                      </div>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${accts.some(a => a.status === "active") ? "bg-green-500/20 text-green-400" : "bg-amber-500/20 text-amber-400"}`}>
                        {accts.filter(a => a.status === "active").length > 0 ? `${accts.filter(a => a.status === "active").length} active` : "pending creation"}
                      </span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-2 p-3">
                      {accts.map(a => (
                        <div key={a.id} className="flex items-center gap-2.5 px-3 py-2 rounded-lg bg-white/[0.03] border border-white/5 hover:border-white/15 transition-all">
                          <div className="w-8 h-8 rounded-full overflow-hidden ring-2 ring-white/10 shrink-0">
                            <img src={getAgentAvatar(a.managed_by)} alt="" className="w-full h-full object-cover" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-medium truncate">@{a.account_name}</p>
                            <p className="text-[9px] text-white/30 truncate">{a.display_name} &middot; {a.channel_brand?.split("—")[0]?.trim()}</p>
                          </div>
                          <span className={`text-[8px] px-1.5 py-0.5 rounded-full shrink-0 ${a.status === "active" ? "bg-green-500/20 text-green-400" : a.status === "pending_creation" ? "bg-amber-500/20 text-amber-400" : "bg-white/5 text-white/25"}`}>
                            {a.status === "pending_creation" ? "pending" : a.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })()}

        {/* ===== VAULT TAB ===== */}
        {tab === "vault" && (() => {
          const categories = ["workstation", "social", "api", "tool", "hosting"];
          const catLabels: Record<string, { label: string; emoji: string }> = {
            workstation: { label: "Workstations", emoji: "🖥️" },
            social: { label: "Social Media", emoji: "📱" },
            api: { label: "API Keys", emoji: "🔑" },
            tool: { label: "Tools", emoji: "🔧" },
            hosting: { label: "Hosting", emoji: "☁️" },
          };
          const byCat: Record<string, VaultEntry[]> = {};
          vaultEntries.forEach(e => { if (!byCat[e.category]) byCat[e.category] = []; byCat[e.category].push(e); });

          return (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold flex items-center gap-2"><KeyRound className="w-5 h-5 text-amber-400" /> Credential Vault</h2>
                  <p className="text-sm text-white/40 mt-1">{vaultEntries.length} credentials tracked — all logins and API keys in one place</p>
                </div>
              </div>

              {/* Summary cards */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                {categories.map(cat => {
                  const entries = byCat[cat] || [];
                  const info = catLabels[cat] || { label: cat, emoji: "📄" };
                  return (
                    <div key={cat} className="bg-white/5 border border-white/10 rounded-xl p-4">
                      <span className="text-lg">{info.emoji}</span>
                      <p className="text-xl font-bold mt-1">{entries.length}</p>
                      <p className="text-xs text-white/40">{info.label}</p>
                    </div>
                  );
                })}
              </div>

              {/* Entries by category */}
              {categories.map(cat => {
                const entries = byCat[cat] || [];
                if (entries.length === 0) return null;
                const info = catLabels[cat] || { label: cat, emoji: "📄" };
                return (
                  <div key={cat} className="bg-white/[0.02] border border-white/10 rounded-xl overflow-hidden">
                    <div className="px-5 py-3 border-b border-white/10 flex items-center justify-between">
                      <h3 className="text-sm font-bold flex items-center gap-2">
                        <span>{info.emoji}</span> {info.label}
                      </h3>
                      <span className="text-[10px] text-white/30">{entries.length} entries</span>
                    </div>
                    <div className="max-h-[400px] overflow-y-auto">
                      <div className="hidden sm:grid grid-cols-12 gap-2 px-5 py-2 border-b border-white/5 text-[10px] text-white/30 uppercase tracking-wider font-medium">
                        <div className="col-span-3">Service</div><div className="col-span-3">Account</div><div className="col-span-4">Notes</div><div className="col-span-1">Status</div><div className="col-span-1">Agent</div>
                      </div>
                      {entries.slice(0, cat === "social" ? 20 : 50).map(e => (
                        <div key={e.id} className="grid grid-cols-1 sm:grid-cols-12 gap-2 px-5 py-2 border-b border-white/5 hover:bg-white/[0.02] items-center text-xs">
                          <div className="sm:col-span-3 font-medium truncate">{e.service}</div>
                          <div className="sm:col-span-3 text-white/50 truncate font-mono text-[10px]">{e.account_name}</div>
                          <div className="sm:col-span-4 text-white/30 truncate text-[10px]">{e.notes}</div>
                          <div className="sm:col-span-1">
                            <span className={`text-[8px] px-1.5 py-0.5 rounded-full ${e.status === "active" ? "bg-green-500/20 text-green-400" : "bg-white/5 text-white/25"}`}>{e.status}</span>
                          </div>
                          <div className="sm:col-span-1">
                            {e.managed_by && <img src={getAgentAvatar(e.managed_by)} className="w-5 h-5 rounded-full object-cover" alt="" />}
                          </div>
                        </div>
                      ))}
                      {cat === "social" && entries.length > 20 && (
                        <div className="px-5 py-3 text-center text-[10px] text-white/20">Showing 20 of {entries.length} — all entries tracked in the database</div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })()}

        {/* ===== INBOX TAB ===== */}
        {tab === "inbox" && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold flex items-center gap-2"><Inbox className="w-5 h-5 text-blue-400" /> Inbox</h2>
                <p className="text-sm text-white/40 mt-1">Escalations, approvals, and important updates from your team</p>
              </div>
              <div className="flex items-center gap-2">
                <a href="/inbox" className="flex items-center gap-2 text-xs bg-white/5 hover:bg-white/10 border border-white/10 px-3 py-2 rounded-lg font-medium transition-all"><ExternalLink className="w-3 h-3" /> Full Inbox</a>
                <a href="/compose" className="flex items-center gap-2 text-xs bg-purple-600 hover:bg-purple-500 px-3 py-2 rounded-lg font-medium transition-all"><Plus className="w-3 h-3" /> New Thread</a>
              </div>
            </div>

            {/* Summary stats */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4">
                <AlertTriangle className="w-4 h-4 text-amber-400 mb-2" />
                <p className="text-2xl font-bold">{activityData?.pending_escalations || 0}</p>
                <p className="text-xs text-white/40">Needs Your Decision</p>
              </div>
              <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4">
                <MessageSquare className="w-4 h-4 text-blue-400 mb-2" />
                <p className="text-2xl font-bold">{threads.length}</p>
                <p className="text-xs text-white/40">Active Threads</p>
              </div>
              <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-4">
                <CheckCircle className="w-4 h-4 text-green-400 mb-2" />
                <p className="text-2xl font-bold">{activityData?.completed_today || 0}</p>
                <p className="text-xs text-white/40">Completed Today</p>
              </div>
              <div className="bg-purple-500/5 border border-purple-500/20 rounded-xl p-4">
                <Activity className="w-4 h-4 text-purple-400 mb-2" />
                <p className="text-2xl font-bold">{feedUnread.total}</p>
                <p className="text-xs text-white/40">Unread Messages</p>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Left: Escalations + Recent completed */}
              <div className="lg:col-span-1 space-y-4">
                {/* Escalations needing action */}
                <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl overflow-hidden">
                  <div className="px-5 py-3 border-b border-amber-500/10 flex items-center justify-between">
                    <h3 className="text-sm font-semibold flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-400" /> Action Required</h3>
                    <span className="text-[10px] text-amber-400">{activityData?.escalations?.length || 0}</span>
                  </div>
                  <div className="p-3 space-y-2 max-h-72 overflow-y-auto">
                    {(!activityData?.escalations || activityData.escalations.length === 0) ? (
                      <div className="text-center py-6">
                        <CheckCircle className="w-8 h-8 text-green-400/30 mx-auto mb-2" />
                        <p className="text-xs text-white/30">All clear — nothing needs your approval</p>
                      </div>
                    ) : activityData.escalations.map(e => {
                      const eAgent = getAgentById(e.agent_id);
                      const eTier = getAgentTier(e.agent_id);
                      const eTs = TIER_STYLES[eTier];
                      return (
                        <div key={e.id} className="bg-white/5 rounded-lg p-3">
                          <div className="flex items-start gap-2.5">
                            <div className={`w-8 h-8 rounded-full overflow-hidden ring-2 ${eTs.ring} shrink-0`}>
                              <img src={getAgentAvatar(e.agent_id)} className="w-full h-full object-cover" alt="" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-1.5">
                                <span className="text-xs font-semibold">{getHumanName(e.agent_id) || eAgent?.name || e.agent_id}</span>
                                <span className={`text-[7px] px-1.5 py-0 rounded-full border font-medium ${eTs.badge}`}>{eTier}</span>
                              </div>
                              <p className="text-[10px] text-white/50 mt-1 leading-relaxed">{e.reason}</p>
                              <div className="flex items-center gap-2 mt-2">
                                <button onClick={() => resolveEscalation(e.id)} className="text-[10px] text-green-400 hover:text-green-300 px-2 py-1 border border-green-500/20 rounded hover:bg-green-500/10 transition-all">Approve</button>
                                <button onClick={() => { setTab("agents"); fetch(`/api/threads/${e.thread_id}`).then(r => r.json()).then(setActiveThread).catch(() => {}); }} className="text-[10px] text-blue-400 hover:text-blue-300 px-2 py-1 border border-blue-500/20 rounded hover:bg-blue-500/10 transition-all">View Thread</button>
                                <span className={`text-[8px] px-1.5 py-0.5 rounded-full ml-auto ${e.severity === "high" ? "bg-red-500/20 text-red-400" : e.severity === "medium" ? "bg-amber-500/20 text-amber-400" : "bg-white/5 text-white/25"}`}>{e.severity}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Recent completed tasks */}
                <div className="bg-white/5 border border-white/10 rounded-xl overflow-hidden">
                  <div className="px-5 py-3 border-b border-white/10">
                    <h3 className="text-sm font-semibold flex items-center gap-2"><CheckCircle className="w-4 h-4 text-green-400" /> Recently Completed</h3>
                  </div>
                  <div className="p-3 space-y-1.5 max-h-64 overflow-y-auto">
                    {activityData?.recent_runs?.filter(r => r.status === "complete").slice(0, 10).map(r => (
                      <div key={r.id} className="flex items-start gap-2 py-1.5 px-2 rounded-lg hover:bg-white/[0.03]">
                        <CheckCircle className="w-3 h-3 text-green-400 mt-0.5 shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-[11px] text-white/60 truncate">{r.task_name}</p>
                          {r.summary && <p className="text-[10px] text-white/25 truncate">{r.summary}</p>}
                        </div>
                      </div>
                    ))}
                    {(!activityData?.recent_runs || activityData.recent_runs.filter(r => r.status === "complete").length === 0) && (
                      <p className="text-xs text-white/20 text-center py-4">No completed tasks yet</p>
                    )}
                  </div>
                </div>
              </div>

              {/* Right: Thread list */}
              <div className="lg:col-span-2 bg-white/[0.02] border border-white/10 rounded-xl overflow-hidden flex flex-col" style={{ maxHeight: 600 }}>
                <div className="px-5 py-3 border-b border-white/10 flex items-center justify-between">
                  <h3 className="text-sm font-semibold">Conversations ({threads.length})</h3>
                  <span className="text-[10px] text-white/30">Click to open in Agents tab</span>
                </div>
                <div className="flex-1 overflow-y-auto divide-y divide-white/5">
                  {threads.map(t => {
                    const firstAgent = t.participants?.[0];
                    const tier = firstAgent ? getAgentTier(firstAgent) : null;
                    const ts = tier ? TIER_STYLES[tier] : null;
                    return (
                      <button key={t.id} onClick={() => { setTab("agents"); fetch(`/api/threads/${t.id}`).then(r => r.json()).then(setActiveThread).catch(() => {}); }} className="w-full text-left flex items-center gap-4 px-5 py-3.5 hover:bg-white/[0.03] transition-all">
                        <div className="flex -space-x-2 shrink-0">
                          {t.participants?.slice(0, 4).map((pid: string) => (
                            <img key={pid} src={getAgentAvatar(pid)} className={`w-8 h-8 rounded-full object-cover ring-2 ring-[#0a0a0a] ${TIER_STYLES[getAgentTier(pid)]?.ring || ""}`} alt="" />
                          ))}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-sm font-medium truncate">{t.subject}</p>
                            {firstAgent && ts && <span className={`text-[7px] px-1.5 py-0 rounded-full border font-medium ${ts.badge}`}>{tier}</span>}
                          </div>
                          <p className="text-[10px] text-white/30 mt-0.5">
                            {t.participants?.slice(0, 3).map((pid: string) => getHumanName(pid) || pid).join(", ")}
                            {(t.participants?.length || 0) > 3 ? ` +${t.participants.length - 3} more` : ""}
                          </p>
                        </div>
                        <div className="text-right shrink-0">
                          <p className="text-[10px] text-white/20">{t.updated_at ? new Date(t.updated_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}) : ""}</p>
                          <span className="text-[9px] text-white/15">{t.participants?.length} agents</span>
                        </div>
                      </button>
                    );
                  })}
                  {threads.length === 0 && <p className="text-center text-xs text-white/20 py-8">No threads yet — go to Agents tab to start a conversation</p>}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ===== TOOLS TAB ===== */}
        {tab === "tools" && (() => {
          const toolsCategories = ["voice", "video", "image", "text", "analytics", "publishing", "automation", "email"];
          const toolsCatLabels: Record<string, { label: string; emoji: string }> = {
            voice: { label: "Voice Generation", emoji: "🎙️" },
            video: { label: "Video Creation", emoji: "🎬" },
            image: { label: "Image & Thumbnails", emoji: "🎨" },
            text: { label: "AI Text & Research", emoji: "🧠" },
            analytics: { label: "Analytics & SEO", emoji: "📊" },
            publishing: { label: "Publishing APIs", emoji: "📺" },
            automation: { label: "Automation", emoji: "⚡" },
            email: { label: "Email & Newsletter", emoji: "✉️" },
          };

          return (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold flex items-center gap-2"><Wrench className="w-5 h-5 text-amber-400" /> AI Tools & Services</h2>
                <span className="text-xs text-white/30">{toolsList.length} tools registered</span>
              </div>

              {/* Tools by category */}
              {toolsCategories.map(cat => {
                const catTools = toolsList.filter(t => t.category === cat);
                if (catTools.length === 0) return null;
                const info = toolsCatLabels[cat];
                return (
                  <div key={cat}>
                    <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <span>{info.emoji}</span> {info.label} ({catTools.length})
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                      {catTools.map(t => (
                        <a key={t.id} href={t.website} target="_blank" rel="noopener noreferrer" className="bg-white/[0.03] border border-white/10 hover:border-white/20 rounded-xl p-4 transition-all group">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="text-lg">{t.icon}</span>
                            <div className="flex-1">
                              <p className="text-sm font-semibold group-hover:text-white transition-colors">{t.name}</p>
                              <span className={`text-[8px] px-1.5 py-0.5 rounded-full ${t.status === "active" ? "bg-green-500/20 text-green-400" : "bg-amber-500/20 text-amber-400"}`}>{t.status}</span>
                            </div>
                            {t.managed_by && (
                              <img src={getAgentAvatar(t.managed_by)} className={`w-6 h-6 rounded-full object-cover ring-1 ${TIER_STYLES[getAgentTier(t.managed_by)]?.ring || ""}`} alt="" title={getHumanName(t.managed_by)} />
                            )}
                          </div>
                          <p className="text-[10px] text-white/40 leading-relaxed">{t.description}</p>
                          {t.api_key_env && <p className="text-[9px] text-white/15 mt-2 font-mono">{t.api_key_env}</p>}
                        </a>
                      ))}
                    </div>
                  </div>
                );
              })}

              {/* Make.com Scenarios */}
              <div>
                <h3 className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <span>⚡</span> Make.com Scenarios ({Object.keys(scenariosList).length})
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                  {Object.entries(scenariosList).map(([key, s]: [string, any]) => (
                    <div key={key} className="bg-white/[0.03] border border-white/10 rounded-xl p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">{s.icon}</span>
                        <p className="text-sm font-semibold">{s.name}</p>
                      </div>
                      <p className="text-[10px] text-white/40 mb-2">{s.description}</p>
                      <div className="flex flex-wrap gap-1">
                        {s.tools?.map((tool: string) => (
                          <span key={tool} className="text-[8px] px-1.5 py-0.5 rounded bg-white/5 text-white/30">{tool}</span>
                        ))}
                      </div>
                      <p className="text-[9px] text-white/15 mt-2">Trigger: {s.trigger}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })()}
      </div>

      <Modal open={!!editItem} onClose={() => setEditItem(null)} title="Edit Content">
        {editItem && (
          <div className="space-y-4">
            <div><label className="block text-sm text-white/60 mb-1.5">Title</label><input type="text" value={editItem.title} onChange={e => setEditItem({...editItem, title:e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-white/30" /></div>
            <div className="grid grid-cols-2 gap-4">
              <div><label className="block text-sm text-white/60 mb-1.5">Channel</label><select value={editItem.channel} onChange={e => setEditItem({...editItem, channel:e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none">{channels.map(c => <option key={c.id} value={c.name} className="bg-[#141414]">{c.name}</option>)}</select></div>
              <div><label className="block text-sm text-white/60 mb-1.5">Status</label><select value={editItem.status} onChange={e => setEditItem({...editItem, status:e.target.value as Status})} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none">{STATUSES.map(s => <option key={s} value={s} className="bg-[#141414]">{s}</option>)}</select></div>
            </div>
            <div><label className="block text-sm text-white/60 mb-1.5">Target Date</label><input type="text" value={editItem.date} onChange={e => setEditItem({...editItem, date:e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none" placeholder="e.g. Apr 15" /></div>
            <div className="flex gap-3 pt-2">
              <button onClick={handleSaveEdit} className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 px-4 py-2.5 rounded-lg text-sm font-medium"><Save className="w-4 h-4" />Save</button>
              <button onClick={() => setEditItem(null)} className="px-4 py-2.5 rounded-lg text-sm border border-white/10 hover:bg-white/5">Cancel</button>
            </div>
          </div>
        )}
      </Modal>

      <Modal open={showNewModal} onClose={() => setShowNewModal(false)} title="Start New Production">
        <div className="space-y-4">
          <div><label className="block text-sm text-white/60 mb-1.5">Video Title / Topic</label><input type="text" value={newItem.title||""} onChange={e => setNewItem({...newItem, title:e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500/50" placeholder="e.g. 5 AI Tools That Will Replace Your Job in 2026" /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="block text-sm text-white/60 mb-1.5">Channel</label><select value={newItem.channel||""} onChange={e => setNewItem({...newItem, channel:e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none">{channels.map(c => <option key={c.id} value={c.name} className="bg-[#141414]">{c.name}</option>)}</select></div>
            <div><label className="block text-sm text-white/60 mb-1.5">Target Date</label><input type="text" value={newItem.date||""} onChange={e => setNewItem({...newItem, date:e.target.value})} className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2.5 text-sm focus:outline-none" placeholder="e.g. Apr 20" /></div>
          </div>
          <div className="bg-blue-500/5 border border-blue-500/20 rounded-lg p-3">
            <p className="text-xs text-blue-400 font-medium mb-1">What happens next?</p>
            <p className="text-[10px] text-white/40 leading-relaxed">Your agents will automatically: Research the topic → Write a script → Generate voiceover brief → Create thumbnail brief → Plan the edit → Optimize SEO → Quality review → Submit for your approval.</p>
          </div>
          <div className="flex gap-3 pt-2">
            <button onClick={() => {
              if (!newItem.title) return;
              fetch('/api/production/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: newItem.title, channel: newItem.channel || channels[0]?.name || 'V-Real AI', target_date: newItem.date || undefined }) })
                .then(r => r.json())
                .then(() => {
                  fetch('/api/production/jobs').then(r=>r.json()).then(d=>setProdJobs(Array.isArray(d)?d:[])).catch(()=>{});
                  handleAddNew();
                })
                .catch(() => { handleAddNew(); });
            }} className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 px-4 py-2.5 rounded-lg text-sm font-medium transition-all"><Zap className="w-4 h-4" />Start Production</button>
            <button onClick={() => setShowNewModal(false)} className="px-4 py-2.5 rounded-lg text-sm border border-white/10 hover:bg-white/5">Cancel</button>
          </div>
        </div>
      </Modal>

      <Modal open={!!skillModal} onClose={() => setSkillModal(null)} title={skillModal?.name||""}>
        {skillModal && (
          <div className="space-y-4">
            <p className="text-sm text-white/60">{skillModal.desc}</p>
            <div className="bg-black/40 rounded-lg p-4 font-mono text-xs text-green-400 space-y-1">
              <p># {skillModal.name}</p>
              <p className="text-white/40">## Purpose</p>
              <p className="text-white/60">{skillModal.desc}</p>
              <p className="text-white/40 mt-2">## Location</p>
              <p className="text-white/60">github.com/pvillarreal23/youtube-agency/{skillModal.file}</p>
            </div>
            <a href={`https://github.com/pvillarreal23/youtube-agency/blob/main/${skillModal.file}`} target="_blank" rel="noopener noreferrer" className="flex items-center justify-center gap-2 w-full bg-blue-600 hover:bg-blue-500 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors">
              <ExternalLink className="w-4 h-4" />Open Full File on GitHub
            </a>
          </div>
        )}
      </Modal>

      {/* ===== TOPIC INPUT MODAL ===== */}
      <Modal open={!!pipelineTopicModal} onClose={() => setPipelineTopicModal(null)} title="What's your video topic?">
        <div className="space-y-4">
          <p className="text-sm text-white/50">Enter a topic and the agent will get to work.</p>
          <input
            autoFocus
            value={pipelineTopic}
            onChange={e => setPipelineTopic(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter" && pipelineTopic.trim() && pipelineTopicModal) triggerAutomation(pipelineTopicModal, pipelineTopic.trim()); }}
            placeholder="e.g. How to use Claude for content creation"
            className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-sm text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50"
          />
          <button
            disabled={!pipelineTopic.trim()}
            onClick={() => { if (pipelineTopic.trim() && pipelineTopicModal) triggerAutomation(pipelineTopicModal, pipelineTopic.trim()); }}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-sm font-semibold disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            Run Agent
          </button>
        </div>
      </Modal>

      </main>

      {/* ===== MOBILE BOTTOM NAV ===== */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#0d0d0d]/95 backdrop-blur-xl border-t border-white/[0.08] safe-bottom">
        <div className="flex items-center justify-around h-14 px-1">
          {mobileBottomTabs.map(item => {
            const isActive = tab === item.id;
            const badgeCount = item.id === "inbox" ? (activityData?.pending_escalations || 0) : item.id === "feed" ? (feedUnread.total || 0) : 0;
            return (
              <button
                key={item.id}
                onClick={() => setTab(item.id)}
                className={`flex flex-col items-center justify-center gap-0.5 flex-1 py-1.5 rounded-lg transition-all ${
                  isActive ? "text-white" : "text-white/35"
                }`}
              >
                <div className="relative">
                  <item.icon className={`w-5 h-5 ${isActive ? "text-white" : "text-white/35"}`} />
                  {badgeCount > 0 && (
                    <span className="absolute -top-1.5 -right-2.5 min-w-[14px] h-[14px] flex items-center justify-center bg-red-500 rounded-full text-[7px] font-bold px-0.5">{badgeCount}</span>
                  )}
                </div>
                <span className={`text-[9px] font-medium ${isActive ? "text-white" : "text-white/35"}`}>{item.label}</span>
                {isActive && <div className="w-4 h-0.5 rounded-full bg-white mt-0.5" />}
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
