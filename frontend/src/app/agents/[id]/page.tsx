"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, AgentDetail, AgentSummary, SandboxTask } from "@/lib/api";
import { getInitials, departmentLabel, timeAgo } from "@/lib/utils";

const STATUS_COLORS: Record<string, string> = {
  pending: "#f59e0b",
  running: "#3b82f6",
  completed: "#10b981",
  failed: "#ef4444",
};

export default function AgentProfilePage() {
  const params = useParams();
  const agentId = params.id as string;
  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [allAgents, setAllAgents] = useState<Record<string, AgentSummary>>({});
  const [sandboxTask, setSandboxTask] = useState("");
  const [sandboxTasks, setSandboxTasks] = useState<SandboxTask[]>([]);
  const [dispatching, setDispatching] = useState(false);
  const [dispatchError, setDispatchError] = useState<string | null>(null);
  const [expandedTask, setExpandedTask] = useState<string | null>(null);
  const [showSetup, setShowSetup] = useState(false);

  useEffect(() => {
    if (!agentId) return;
    Promise.all([
      api.getAgent(agentId),
      api.getAgents(),
      api.getAgentSandboxTasks(agentId).catch(() => [] as SandboxTask[]),
    ]).then(([a, all, tasks]) => {
      setAgent(a);
      const map: Record<string, AgentSummary> = {};
      all.forEach((ag) => (map[ag.id] = ag));
      setAllAgents(map);
      setSandboxTasks(tasks);
    });
  }, [agentId]);

  // Auto-poll active tasks every 5 seconds
  const pollActiveTasks = useCallback(async () => {
    const active = sandboxTasks.filter(
      (t) => t.status === "pending" || t.status === "running"
    );
    if (active.length === 0) return;
    const updates = await Promise.all(
      active.map((t) => api.getSandboxTask(t.id).catch(() => t))
    );
    setSandboxTasks((prev: SandboxTask[]) => {
      const updated = new Map(updates.map((u) => [u.id, u]));
      return prev.map((t: SandboxTask) => updated.get(t.id) || t);
    });
  }, [sandboxTasks]);

  useEffect(() => {
    const hasActive = sandboxTasks.some(
      (t) => t.status === "pending" || t.status === "running"
    );
    if (!hasActive) return;
    const interval = setInterval(pollActiveTasks, 5000);
    return () => clearInterval(interval);
  }, [sandboxTasks, pollActiveTasks]);

  const handleDispatch = async () => {
    if (!sandboxTask.trim() || dispatching) return;
    setDispatching(true);
    setDispatchError(null);
    try {
      const task = await api.dispatchToSandbox({ agent_id: agentId, task: sandboxTask });
      setSandboxTasks((prev: SandboxTask[]) => [task, ...prev]);
      setSandboxTask("");
    } catch {
      setDispatchError("Failed to dispatch — check that your API key is set in .env and the backend is running.");
    } finally {
      setDispatching(false);
    }
  };

  if (!agent) return <div className="flex items-center justify-center h-full text-[#64748b]">Loading...</div>;

  const manager = agent.reports_to ? allAgents[agent.reports_to] : null;

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <div
            className="w-16 h-16 rounded-full flex items-center justify-center text-white text-xl font-bold"
            style={{ backgroundColor: agent.avatar_color }}
          >
            {getInitials(agent.name)}
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">{agent.name}</h1>
            <p className="text-[#94a3b8]">{agent.role}</p>
            <span
              className="inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium"
              style={{ backgroundColor: agent.avatar_color + "20", color: agent.avatar_color }}
            >
              {departmentLabel(agent.department)}
            </span>
          </div>
        </div>

        {/* Org relationships */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Reports to */}
          <div className="p-4 rounded-lg bg-[#1e293b] border border-[#334155]">
            <h3 className="text-xs font-semibold text-[#64748b] uppercase mb-2">Reports To</h3>
            {manager ? (
              <Link href={`/agents/${manager.id}`} className="flex items-center gap-2 hover:opacity-80">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[8px] font-bold"
                  style={{ backgroundColor: manager.avatar_color }}
                >
                  {getInitials(manager.name)}
                </div>
                <span className="text-sm text-white">{manager.name}</span>
              </Link>
            ) : (
              <span className="text-sm text-[#64748b]">Top of hierarchy</span>
            )}
          </div>

          {/* Direct reports */}
          <div className="p-4 rounded-lg bg-[#1e293b] border border-[#334155]">
            <h3 className="text-xs font-semibold text-[#64748b] uppercase mb-2">Direct Reports</h3>
            {agent.direct_reports.length > 0 ? (
              <div className="space-y-1.5">
                {agent.direct_reports.map((rid) => {
                  const r = allAgents[rid];
                  return r ? (
                    <Link key={rid} href={`/agents/${rid}`} className="flex items-center gap-2 hover:opacity-80">
                      <div
                        className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[7px] font-bold"
                        style={{ backgroundColor: r.avatar_color }}
                      >
                        {getInitials(r.name)}
                      </div>
                      <span className="text-xs text-[#94a3b8]">{r.name}</span>
                    </Link>
                  ) : null;
                })}
              </div>
            ) : (
              <span className="text-sm text-[#64748b]">None</span>
            )}
          </div>

          {/* Collaborates with */}
          <div className="p-4 rounded-lg bg-[#1e293b] border border-[#334155]">
            <h3 className="text-xs font-semibold text-[#64748b] uppercase mb-2">Collaborates With</h3>
            {agent.collaborates_with.length > 0 ? (
              <div className="space-y-1.5">
                {agent.collaborates_with.map((cid) => {
                  const c = allAgents[cid];
                  return c ? (
                    <Link key={cid} href={`/agents/${cid}`} className="flex items-center gap-2 hover:opacity-80">
                      <div
                        className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[7px] font-bold"
                        style={{ backgroundColor: c.avatar_color }}
                      >
                        {getInitials(c.name)}
                      </div>
                      <span className="text-xs text-[#94a3b8]">{c.name}</span>
                    </Link>
                  ) : null;
                })}
              </div>
            ) : (
              <span className="text-sm text-[#64748b]">None</span>
            )}
          </div>
        </div>

        {/* System prompt */}
        <div className="p-4 rounded-lg bg-[#1e293b] border border-[#334155]">
          <h3 className="text-xs font-semibold text-[#64748b] uppercase mb-3">Agent Prompt</h3>
          <pre className="text-sm text-[#94a3b8] whitespace-pre-wrap font-sans leading-relaxed">
            {agent.system_prompt}
          </pre>
        </div>

        {/* Sandbox dispatch */}
        <div className="p-4 rounded-lg bg-[#1e293b] border border-[#334155]">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-[#64748b] uppercase">
              Sandbox Task
            </h3>
            <button
              onClick={() => setShowSetup(!showSetup)}
              className="text-[10px] text-[#8b5cf6] hover:text-[#a78bfa] transition-colors"
            >
              {showSetup ? "Hide setup guide" : "Setup guide"}
            </button>
          </div>

          {/* Collapsible setup guide */}
          {showSetup && (
            <div className="mb-4 p-3 rounded-lg bg-[#0f172a] border border-[#1e293b] text-xs text-[#94a3b8] space-y-2">
              <p className="font-semibold text-white">One-time setup</p>
              <ol className="list-decimal list-inside space-y-1">
                <li>Go to <span className="text-[#8b5cf6]">console.anthropic.com</span></li>
                <li>Navigate to <span className="text-white">Settings &rarr; API Keys &rarr; Create Key</span></li>
                <li>Copy the key (starts with <code className="text-[#10b981]">sk-ant-...</code>)</li>
                <li>Add it to your <code className="text-[#10b981]">.env</code> file:
                  <code className="block mt-1 p-1.5 rounded bg-[#1e293b] text-[#f59e0b]">ANTHROPIC_API_KEY=sk-ant-...</code>
                </li>
                <li>Restart the backend server</li>
              </ol>
              <p className="pt-1 border-t border-[#1e293b]">
                <span className="font-semibold text-white">What this does:</span> Dispatches {agent.name} to
                {" "}Anthropic&apos;s cloud sandbox where it runs autonomously with bash, file access, and web
                search. Great for research, trend analysis, report writing, and content generation.
              </p>
            </div>
          )}

          <p className="text-xs text-[#64748b] mb-3">
            Dispatch {agent.name} to an autonomous cloud sandbox for long-running tasks like
            research, analysis, or content generation.
          </p>
          <textarea
            value={sandboxTask}
            onChange={(e) => { setSandboxTask(e.target.value); setDispatchError(null); }}
            placeholder={`e.g. "Research the top 10 trending AI topics this week and write a summary report..."`}
            className="w-full p-3 rounded-lg bg-[#0f172a] border border-[#334155] text-sm text-white placeholder-[#475569] resize-none focus:outline-none focus:border-[#8b5cf6]"
            rows={3}
          />
          <button
            onClick={handleDispatch}
            disabled={!sandboxTask.trim() || dispatching}
            className="mt-2 px-4 py-2 bg-[#10b981] hover:bg-[#059669] disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
          >
            {dispatching ? "Dispatching..." : "Dispatch to Sandbox"}
          </button>

          {/* Error display */}
          {dispatchError && (
            <p className="mt-2 text-xs text-[#ef4444]">{dispatchError}</p>
          )}

          {/* Previous sandbox tasks */}
          {sandboxTasks.length > 0 && (
            <div className="mt-4 space-y-2">
              <h4 className="text-xs font-semibold text-[#64748b] uppercase">
                Previous Tasks
              </h4>
              {sandboxTasks.map((t) => (
                <div
                  key={t.id}
                  className="p-3 rounded bg-[#0f172a] border border-[#1e293b] cursor-pointer hover:border-[#334155] transition-colors"
                  onClick={() => setExpandedTask(expandedTask === t.id ? null : t.id)}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-[#94a3b8] truncate flex-1">
                      {t.task.slice(0, 80)}{t.task.length > 80 ? "..." : ""}
                    </span>
                    <div className="flex items-center gap-2 ml-2 shrink-0">
                      <span className="text-[10px] text-[#64748b]">{timeAgo(t.created_at)}</span>
                      <span
                        className="text-[10px] font-medium px-1.5 py-0.5 rounded"
                        style={{
                          color: STATUS_COLORS[t.status] || "#64748b",
                          backgroundColor: (STATUS_COLORS[t.status] || "#64748b") + "20",
                        }}
                      >
                        {t.status}
                      </span>
                    </div>
                  </div>
                  {expandedTask === t.id && t.result && (
                    <pre className="mt-2 text-xs text-[#94a3b8] whitespace-pre-wrap font-sans leading-relaxed border-t border-[#1e293b] pt-2">
                      {t.result}
                    </pre>
                  )}
                  {expandedTask === t.id && t.status === "failed" && t.result && (
                    <p className="mt-2 text-xs text-[#ef4444] border-t border-[#1e293b] pt-2">
                      Error: {t.result}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick action */}
        <Link
          href={`/compose?to=${agent.id}`}
          className="inline-block px-5 py-2.5 bg-[#8b5cf6] hover:bg-[#7c3aed] text-white text-sm font-medium rounded-lg transition-colors"
        >
          Send Message to {agent.name}
        </Link>
      </div>
    </div>
  );
}
