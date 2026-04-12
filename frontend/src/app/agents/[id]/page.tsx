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

        {/* Available Tools */}
        {agent.tools && agent.tools.length > 0 && (
          <div className="p-4 rounded-lg bg-[#1e293b] border border-[#334155]">
            <h3 className="text-xs font-semibold text-[#64748b] uppercase mb-3">Available Tools</h3>
            <div className="flex flex-wrap gap-2">
              {agent.tools.map((toolId) => (
                <span
                  key={toolId}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium bg-[#8b5cf620] text-[#a78bfa] border border-[#8b5cf630]"
                >
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {toolId.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </div>
        )}

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
