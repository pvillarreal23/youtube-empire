"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import { api, type WorkflowInfo, type ChannelInfo, type WorkflowRun } from "@/lib/api";
import { timeAgo } from "@/lib/utils";

const WORKFLOW_ICONS: Record<string, string> = {
  "content-pipeline": "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z",
  "analytics-report": "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z",
  "community-engagement": "M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z",
  "strategy-review": "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z",
  "revenue-newsletter": "M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z",
};

const WORKFLOW_COLORS: Record<string, string> = {
  "content-pipeline": "bg-blue-500/20 text-blue-400 border-blue-500/30",
  "analytics-report": "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  "community-engagement": "bg-amber-500/20 text-amber-400 border-amber-500/30",
  "strategy-review": "bg-purple-500/20 text-purple-400 border-purple-500/30",
  "revenue-newsletter": "bg-red-500/20 text-red-400 border-red-500/30",
};

const STATUS_STYLES: Record<string, string> = {
  running: "bg-blue-500/20 text-blue-400",
  completed: "bg-emerald-500/20 text-emerald-400",
  failed: "bg-red-500/20 text-red-400",
};

export default function AutomationPage() {
  const [workflows, setWorkflows] = useState<WorkflowInfo[]>([]);
  const [channels, setChannels] = useState<ChannelInfo[]>([]);
  const [history, setHistory] = useState<WorkflowRun[]>([]);
  const [selectedChannel, setSelectedChannel] = useState("ai-tech");
  const [activeRun, setActiveRun] = useState<{ id: string; name: string } | null>(null);
  const [streamOutput, setStreamOutput] = useState("");
  const [launching, setLaunching] = useState<string | null>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.getWorkflows().then(setWorkflows).catch(() => {});
    api.getChannels().then(setChannels).catch(() => {});
    api.getAutomationHistory().then(setHistory).catch(() => {});
  }, []);

  // Poll for history updates while a run is active
  useEffect(() => {
    if (!activeRun) return;
    const interval = setInterval(() => {
      api.getAutomationHistory().then(setHistory).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, [activeRun]);

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [streamOutput]);

  const handleRun = useCallback(async (workflowId: string, workflowName: string, channelSpecific: boolean) => {
    setLaunching(workflowId);
    setStreamOutput("");
    try {
      const channel = channelSpecific ? selectedChannel : undefined;
      const result = await api.runWorkflow(workflowId, channel);

      setActiveRun({ id: result.id, name: workflowName });
      setLaunching(null);

      // Poll for output since SSE may not be ready immediately
      const pollOutput = async () => {
        for (let i = 0; i < 120; i++) {
          await new Promise((r) => setTimeout(r, 3000));
          try {
            const run = await api.getRunDetail(result.id);
            if (run.output) {
              setStreamOutput(run.output);
            }
            if (run.status === "completed" || run.status === "failed") {
              setActiveRun(null);
              api.getAutomationHistory().then(setHistory).catch(() => {});
              return;
            }
          } catch {
            // continue polling
          }
        }
      };
      pollOutput();
    } catch (e) {
      setLaunching(null);
      setStreamOutput(`Error: ${e instanceof Error ? e.message : "Failed to start workflow"}`);
    }
  }, [selectedChannel]);

  return (
    <div className="h-full flex flex-col bg-[#0f172a]">
      {/* Header */}
      <div className="p-4 lg:p-6 border-b border-[#334155]">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Automation</h1>
            <p className="text-sm text-[#64748b] mt-1">
              One-click workflows powered by Claude Managed Agents
            </p>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-xs text-[#94a3b8]">Channel:</label>
            <select
              value={selectedChannel}
              onChange={(e) => setSelectedChannel(e.target.value)}
              className="bg-[#1e293b] border border-[#334155] rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-[#8b5cf6]"
            >
              {channels.map((ch) => (
                <option key={ch.id} value={ch.id}>
                  {ch.name}
                </option>
              ))}
              {channels.length === 0 && (
                <>
                  <option value="ai-tech">AI &amp; Tech</option>
                  <option value="finance">Finance</option>
                  <option value="psychology">Psychology</option>
                </>
              )}
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4 lg:p-6 space-y-6">
        {/* Workflow cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {workflows.map((wf) => {
            const colors = WORKFLOW_COLORS[wf.id] || "bg-slate-500/20 text-slate-400 border-slate-500/30";
            const icon = WORKFLOW_ICONS[wf.id] || "M13 10V3L4 14h7v7l9-11h-7z";
            const isRunning = launching === wf.id || (activeRun !== null);

            return (
              <div
                key={wf.id}
                className={`rounded-xl border p-5 ${colors} transition-all hover:scale-[1.02]`}
              >
                <div className="flex items-start gap-3 mb-3">
                  <svg className="w-6 h-6 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
                  </svg>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white text-sm">{wf.name}</h3>
                    <p className="text-xs opacity-80 mt-1 line-clamp-2">{wf.description}</p>
                  </div>
                </div>
                <div className="flex items-center justify-between mt-4">
                  <div className="flex flex-wrap gap-1">
                    {wf.agents_used.map((a) => (
                      <span key={a} className="text-[10px] bg-black/20 rounded px-1.5 py-0.5">
                        {a}
                      </span>
                    ))}
                  </div>
                  <button
                    onClick={() => handleRun(wf.id, wf.name, wf.channel_specific)}
                    disabled={isRunning}
                    className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
                      isRunning
                        ? "bg-white/10 text-white/50 cursor-not-allowed"
                        : "bg-white/20 text-white hover:bg-white/30"
                    }`}
                  >
                    {launching === wf.id ? "Starting..." : isRunning ? "Running..." : "Run"}
                  </button>
                </div>
              </div>
            );
          })}

          {/* Fallback cards when backend is offline */}
          {workflows.length === 0 && (
            <>
              {[
                { name: "Weekly Content Pipeline", desc: "Research, scripts, hooks, SEO", id: "content-pipeline" },
                { name: "Analytics Report", desc: "Performance analysis & recommendations", id: "analytics-report" },
                { name: "Community Engagement", desc: "Social posts, replies, engagement", id: "community-engagement" },
                { name: "Strategy Review", desc: "Content calendar & strategic priorities", id: "strategy-review" },
                { name: "Revenue & Newsletter", desc: "Newsletter, sponsorships, affiliates", id: "revenue-newsletter" },
              ].map((wf) => {
                const colors = WORKFLOW_COLORS[wf.id] || "bg-slate-500/20 text-slate-400 border-slate-500/30";
                const icon = WORKFLOW_ICONS[wf.id] || "M13 10V3L4 14h7v7l9-11h-7z";
                return (
                  <div key={wf.id} className={`rounded-xl border p-5 ${colors} opacity-60`}>
                    <div className="flex items-start gap-3 mb-3">
                      <svg className="w-6 h-6 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
                      </svg>
                      <div>
                        <h3 className="font-semibold text-white text-sm">{wf.name}</h3>
                        <p className="text-xs opacity-80 mt-1">{wf.desc}</p>
                      </div>
                    </div>
                    <div className="flex justify-end mt-4">
                      <span className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-white/10 text-white/40">
                        Start backend to run
                      </span>
                    </div>
                  </div>
                );
              })}
            </>
          )}
        </div>

        {/* Live output panel */}
        {(activeRun || streamOutput) && (
          <div className="rounded-xl border border-[#334155] bg-[#1e293b] overflow-hidden">
            <div className="px-4 py-3 border-b border-[#334155] flex items-center justify-between">
              <div className="flex items-center gap-2">
                {activeRun && (
                  <span className="inline-block w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
                )}
                <span className="text-sm font-medium text-white">
                  {activeRun ? `Running: ${activeRun.name}` : "Last Output"}
                </span>
              </div>
              {!activeRun && streamOutput && (
                <button
                  onClick={() => setStreamOutput("")}
                  className="text-xs text-[#64748b] hover:text-white transition-colors"
                >
                  Clear
                </button>
              )}
            </div>
            <div
              ref={outputRef}
              className="p-4 max-h-96 overflow-auto font-mono text-xs text-[#94a3b8] whitespace-pre-wrap leading-relaxed"
            >
              {streamOutput || (activeRun ? "Waiting for agent output..." : "")}
            </div>
          </div>
        )}

        {/* History */}
        <div>
          <h2 className="text-sm font-semibold text-white mb-3">Recent Runs</h2>
          {history.length === 0 ? (
            <div className="text-center py-8 text-[#64748b] text-sm">
              No workflow runs yet. Click &quot;Run&quot; on any workflow above to get started.
            </div>
          ) : (
            <div className="space-y-2">
              {history.map((run) => (
                <Link
                  key={run.id}
                  href={`/automation/${run.id}`}
                  className="flex items-center justify-between p-3 rounded-lg border border-[#334155] bg-[#1e293b] hover:border-[#8b5cf6] transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${STATUS_STYLES[run.status] || ""}`}>
                      {run.status}
                    </span>
                    <span className="text-sm text-white truncate">
                      {run.workflow_id.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </span>
                    {run.channel && (
                      <span className="text-[10px] text-[#64748b] bg-[#334155] rounded px-1.5 py-0.5">
                        {run.channel}
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-[#64748b] shrink-0 ml-2">
                    {timeAgo(run.created_at)}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
