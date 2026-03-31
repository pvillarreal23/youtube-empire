"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, AgentDetail, AgentSummary } from "@/lib/api";
import { getInitials, departmentLabel } from "@/lib/utils";

export default function AgentProfilePage() {
  const params = useParams();
  const agentId = params.id as string;
  const [agent, setAgent] = useState<AgentDetail | null>(null);
  const [allAgents, setAllAgents] = useState<Record<string, AgentSummary>>({});

  useEffect(() => {
    if (!agentId) return;
    Promise.all([api.getAgent(agentId), api.getAgents()]).then(([a, all]) => {
      setAgent(a);
      const map: Record<string, AgentSummary> = {};
      all.forEach((ag) => (map[ag.id] = ag));
      setAllAgents(map);
    });
  }, [agentId]);

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
