"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, AgentDetail, AgentSummary } from "@/lib/api";
import { getInitials, departmentLabel } from "@/lib/utils";
import { getHumanName, getAgentTier, TIER_STYLES, DEPT_COLORS } from "@/lib/constants";

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

  if (!agent) return <div className="flex items-center justify-center h-full text-white/30">Loading...</div>;

  const manager = agent.reports_to ? allAgents[agent.reports_to] : null;
  const tier = getAgentTier(agent.id);
  const tierStyle = TIER_STYLES[tier];
  const humanName = getHumanName(agent.id);
  const deptColor = DEPT_COLORS[agent.department];

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
            <h1 className="text-2xl font-bold text-white">{humanName || agent.name}</h1>
            {humanName && <p className="text-sm text-white/30">{agent.name}</p>}
            <p className="text-white/50">{agent.role}</p>
            <div className="flex items-center gap-2 mt-1">
              <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium border ${tierStyle.badge}`}>
                {tier}
              </span>
              <span className="flex items-center gap-1.5 text-xs text-white/30">
                {deptColor && <span className={`w-2 h-2 rounded-full ${deptColor.dot}`} />}
                {departmentLabel(agent.department)}
              </span>
            </div>
          </div>
        </div>

        {/* Org relationships */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Reports to */}
          <div className="p-4 rounded-lg bg-white/[0.02] border border-white/5">
            <h3 className="text-xs font-semibold text-white/30 uppercase mb-2">Reports To</h3>
            {manager ? (
              <Link href={`/agents/${manager.id}`} className="flex items-center gap-2 hover:opacity-80">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center text-white text-[8px] font-bold"
                  style={{ backgroundColor: manager.avatar_color }}
                >
                  {getInitials(manager.name)}
                </div>
                <span className="text-sm text-white">{getHumanName(manager.id) || manager.name}</span>
              </Link>
            ) : (
              <span className="text-sm text-white/20">Top of hierarchy</span>
            )}
          </div>

          {/* Direct reports */}
          <div className="p-4 rounded-lg bg-white/[0.02] border border-white/5">
            <h3 className="text-xs font-semibold text-white/30 uppercase mb-2">Direct Reports</h3>
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
                      <span className="text-xs text-white/50">{getHumanName(rid) || r.name}</span>
                    </Link>
                  ) : null;
                })}
              </div>
            ) : (
              <span className="text-sm text-white/20">None</span>
            )}
          </div>

          {/* Collaborates with */}
          <div className="p-4 rounded-lg bg-white/[0.02] border border-white/5">
            <h3 className="text-xs font-semibold text-white/30 uppercase mb-2">Collaborates With</h3>
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
                      <span className="text-xs text-white/50">{getHumanName(cid) || c.name}</span>
                    </Link>
                  ) : null;
                })}
              </div>
            ) : (
              <span className="text-sm text-white/20">None</span>
            )}
          </div>
        </div>

        {/* System prompt */}
        <div className="p-4 rounded-lg bg-white/[0.02] border border-white/5">
          <h3 className="text-xs font-semibold text-white/30 uppercase mb-3">Agent Prompt</h3>
          <pre className="text-sm text-white/50 whitespace-pre-wrap font-sans leading-relaxed max-h-96 overflow-y-auto">
            {agent.system_prompt}
          </pre>
        </div>

        {/* Quick action */}
        <Link
          href={`/compose?to=${agent.id}`}
          className="inline-block px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          Send Message to {humanName || agent.name}
        </Link>
      </div>
    </div>
  );
}
