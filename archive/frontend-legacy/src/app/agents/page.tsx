"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, AgentSummary } from "@/lib/api";
import { getInitials, departmentLabel } from "@/lib/utils";

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
      a.department.toLowerCase().includes(search.toLowerCase())
  );

  const grouped = filtered.reduce<Record<string, AgentSummary[]>>((acc, a) => {
    const dept = a.department;
    if (!acc[dept]) acc[dept] = [];
    acc[dept].push(a);
    return acc;
  }, {});

  const deptOrder = ["executive", "content", "operations", "analytics", "monetization", "admin"];

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-[#334155] flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Agents ({agents.length})</h2>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search agents..."
          className="px-4 py-2 bg-[#1e293b] border border-[#334155] rounded-lg text-sm text-white placeholder-[#64748b] focus:outline-none focus:border-[#8b5cf6] w-64"
        />
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        {deptOrder.map((dept) => {
          const deptAgents = grouped[dept];
          if (!deptAgents) return null;
          return (
            <div key={dept} className="mb-8">
              <h3 className="text-xs font-semibold text-[#64748b] uppercase tracking-wider mb-3">
                {departmentLabel(dept)} ({deptAgents.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                {deptAgents.map((agent) => (
                  <Link
                    key={agent.id}
                    href={`/agents/${agent.id}`}
                    className="flex items-center gap-3 p-4 rounded-lg bg-[#1e293b] border border-[#334155] hover:border-[#8b5cf6]/50 transition-colors"
                  >
                    <div
                      className="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
                      style={{ backgroundColor: agent.avatar_color }}
                    >
                      {getInitials(agent.name)}
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-medium text-white truncate">{agent.name}</div>
                      <div className="text-xs text-[#64748b] truncate">{agent.role}</div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
