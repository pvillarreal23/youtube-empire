"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, AgentSummary } from "@/lib/api";
import { getInitials, departmentLabel } from "@/lib/utils";
import { getHumanName, getAgentTier, TIER_STYLES, DEPT_COLORS } from "@/lib/constants";

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.getAgents().then(setAgents);
  }, []);

  const filtered = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.role.toLowerCase().includes(search.toLowerCase()) ||
      a.department.toLowerCase().includes(search.toLowerCase()) ||
      (getHumanName(a.id) || "").toLowerCase().includes(search.toLowerCase())
  );

  const grouped = filtered.reduce<Record<string, AgentSummary[]>>((acc, a) => {
    const dept = a.department;
    if (!acc[dept]) acc[dept] = [];
    acc[dept].push(a);
    return acc;
  }, {});

  const deptOrder = ["executive", "content", "operations", "analytics", "monetization", "admin", "general"];

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Agents ({agents.length})</h2>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search agents..."
          className="px-4 py-2 bg-white/[0.03] border border-white/10 rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50 w-64"
        />
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        {deptOrder.map((dept) => {
          const deptAgents = grouped[dept];
          if (!deptAgents) return null;
          const deptColor = DEPT_COLORS[dept];
          return (
            <div key={dept} className="mb-8">
              <h3 className="flex items-center gap-2 text-xs font-semibold text-white/30 uppercase tracking-wider mb-3">
                {deptColor && <span className={`w-2 h-2 rounded-full ${deptColor.dot}`} />}
                {departmentLabel(dept)} ({deptAgents.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {deptAgents.map((agent) => {
                  const tier = getAgentTier(agent.id);
                  const tierStyle = TIER_STYLES[tier];
                  const humanName = getHumanName(agent.id);
                  return (
                    <Link
                      key={agent.id}
                      href={`/agents/${agent.id}`}
                      className={`flex items-center gap-3 p-4 rounded-lg bg-white/[0.02] border border-white/5 hover:border-purple-500/30 transition-colors`}
                    >
                      <div
                        className="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
                        style={{ backgroundColor: agent.avatar_color }}
                      >
                        {getInitials(agent.name)}
                      </div>
                      <div className="min-w-0">
                        <div className="text-sm font-medium text-white truncate">
                          {humanName || agent.name}
                        </div>
                        <div className="text-xs text-white/30 truncate">{agent.role}</div>
                        <span className={`inline-block mt-1 text-[9px] px-1.5 py-0.5 rounded border ${tierStyle.badge}`}>
                          {tier}
                        </span>
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
