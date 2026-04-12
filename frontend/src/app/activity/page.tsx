"use client";

import { useEffect, useState } from "react";
import { api, ToolCallRecord, AgentSummary } from "@/lib/api";
import { getInitials, timeAgo } from "@/lib/utils";

const statusColors: Record<string, { color: string; bg: string }> = {
  completed: { color: "#10b981", bg: "#10b98120" },
  executing: { color: "#f59e0b", bg: "#f59e0b20" },
  pending: { color: "#6366f1", bg: "#6366f120" },
  failed: { color: "#ef4444", bg: "#ef444420" },
};

export default function ActivityPage() {
  const [toolCalls, setToolCalls] = useState<ToolCallRecord[]>([]);
  const [agents, setAgents] = useState<Record<string, AgentSummary>>({});
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [filterAgent, setFilterAgent] = useState<string>("");
  const [filterStatus, setFilterStatus] = useState<string>("");

  const fetchData = async () => {
    try {
      const [calls, agentList] = await Promise.all([
        api.getToolCalls({ agent_id: filterAgent || undefined, status: filterStatus || undefined, limit: 100 }),
        api.getAgents(),
      ]);
      setToolCalls(calls);
      const agentMap: Record<string, AgentSummary> = {};
      agentList.forEach((a) => (agentMap[a.id] = a));
      setAgents(agentMap);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [filterAgent, filterStatus]);

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-[#334155]">
        <h2 className="text-lg font-semibold text-white">Activity</h2>
        <p className="text-xs text-[#64748b] mt-1">Tool calls and agent actions across the system</p>
      </header>

      <div className="px-6 py-3 border-b border-[#334155] flex gap-3">
        <select
          value={filterAgent}
          onChange={(e) => setFilterAgent(e.target.value)}
          className="px-3 py-1.5 bg-[#1e293b] border border-[#334155] rounded text-xs text-[#94a3b8] focus:outline-none focus:border-[#8b5cf6]"
        >
          <option value="">All Agents</option>
          {Object.values(agents).map((a) => (
            <option key={a.id} value={a.id}>{a.name}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-1.5 bg-[#1e293b] border border-[#334155] rounded text-xs text-[#94a3b8] focus:outline-none focus:border-[#8b5cf6]"
        >
          <option value="">All Statuses</option>
          <option value="completed">Completed</option>
          <option value="executing">Executing</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
        </select>
      </div>

      <div className="flex-1 overflow-y-auto">
        {toolCalls.length === 0 ? (
          <div className="flex items-center justify-center h-64 text-[#64748b] text-sm">
            No tool calls yet. Agents will show activity here when they use tools.
          </div>
        ) : (
          <div className="divide-y divide-[#334155]">
            {toolCalls.map((tc) => {
              const agent = agents[tc.agent_id];
              const sc = statusColors[tc.status] || statusColors.pending;
              const isExpanded = expandedId === tc.id;

              return (
                <div key={tc.id}>
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : tc.id)}
                    className="w-full px-6 py-3 flex items-center gap-4 hover:bg-[#ffffff05] transition-colors text-left"
                  >
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0"
                      style={{ backgroundColor: agent?.avatar_color || "#6366f1" }}
                    >
                      {getInitials(agent?.name || tc.agent_id)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-[#e2e8f0] truncate">
                          {agent?.name || tc.agent_id}
                        </span>
                        <span className="text-xs text-[#64748b]">used</span>
                        <span className="text-sm font-medium text-[#8b5cf6]">{tc.tool_name}</span>
                      </div>
                    </div>
                    <span
                      className="px-2 py-0.5 rounded text-[10px] font-medium shrink-0"
                      style={{ backgroundColor: sc.bg, color: sc.color }}
                    >
                      {tc.status}
                    </span>
                    <span className="text-[10px] text-[#64748b] shrink-0 w-16 text-right">
                      {timeAgo(tc.created_at)}
                    </span>
                    <svg
                      className={`w-3 h-3 text-[#64748b] transition-transform shrink-0 ${isExpanded ? "rotate-180" : ""}`}
                      fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {isExpanded && (
                    <div className="px-6 pb-3 pl-18 space-y-2" style={{ paddingLeft: "4.5rem" }}>
                      <div>
                        <div className="text-[10px] font-semibold text-[#64748b] uppercase tracking-wider mb-1">Input</div>
                        <pre className="text-[11px] text-[#94a3b8] bg-[#0f172a] rounded px-3 py-2 overflow-x-auto whitespace-pre-wrap border border-[#1e293b]">
                          {JSON.stringify(tc.input_data, null, 2)}
                        </pre>
                      </div>
                      {tc.output_data && (
                        <div>
                          <div className="text-[10px] font-semibold text-[#64748b] uppercase tracking-wider mb-1">Output</div>
                          <pre className="text-[11px] text-[#94a3b8] bg-[#0f172a] rounded px-3 py-2 overflow-x-auto whitespace-pre-wrap border border-[#1e293b]">
                            {JSON.stringify(tc.output_data, null, 2)}
                          </pre>
                        </div>
                      )}
                      {tc.error_message && (
                        <div>
                          <div className="text-[10px] font-semibold text-[#ef4444] uppercase tracking-wider mb-1">Error</div>
                          <pre className="text-[11px] text-[#fca5a5] bg-[#0f172a] rounded px-3 py-2 overflow-x-auto whitespace-pre-wrap border border-[#1e293b]">
                            {tc.error_message}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
