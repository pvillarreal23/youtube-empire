"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, AgentSummary } from "@/lib/api";
import { getInitials, departmentLabel } from "@/lib/utils";
import { getHumanName } from "@/lib/constants";
import { Check } from "lucide-react";

export default function ComposePage() {
  const router = useRouter();
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [subject, setSubject] = useState("");
  const [content, setContent] = useState("");
  const [sending, setSending] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.getAgents().then(setAgents);
  }, []);

  const filteredAgents = agents.filter(
    (a) =>
      a.name.toLowerCase().includes(search.toLowerCase()) ||
      a.role.toLowerCase().includes(search.toLowerCase()) ||
      a.department.toLowerCase().includes(search.toLowerCase()) ||
      (getHumanName(a.id) || "").toLowerCase().includes(search.toLowerCase())
  );

  const groupedAgents = filteredAgents.reduce<Record<string, AgentSummary[]>>((acc, a) => {
    const dept = a.department;
    if (!acc[dept]) acc[dept] = [];
    acc[dept].push(a);
    return acc;
  }, {});

  const toggleAgent = (id: string) => {
    setSelectedAgents((prev) =>
      prev.includes(id) ? prev.filter((a) => a !== id) : [...prev, id]
    );
  };

  const handleSend = async () => {
    if (!subject.trim() || !content.trim() || selectedAgents.length === 0) return;
    setSending(true);
    try {
      const thread = await api.createThread({
        subject,
        recipient_agent_ids: selectedAgents,
        content,
      });
      router.push(`/thread?id=${thread.id}`);
    } catch (e) {
      console.error(e);
      setSending(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-white/5">
        <h2 className="text-xl font-semibold text-white">Compose Message</h2>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Selected agents */}
          <div>
            <label className="block text-sm font-medium text-white/50 mb-2">To:</label>
            {selectedAgents.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {selectedAgents.map((id) => {
                  const agent = agents.find((a) => a.id === id);
                  return (
                    <span
                      key={id}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs text-white"
                      style={{ backgroundColor: agent?.avatar_color || "#6366f1" }}
                    >
                      {getHumanName(id) || agent?.name || id}
                      <button onClick={() => toggleAgent(id)} className="hover:opacity-70">x</button>
                    </span>
                  );
                })}
              </div>
            )}
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search agents..."
              className="w-full px-4 py-2.5 bg-white/[0.03] border border-white/10 rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50"
            />
            <div className="mt-3 max-h-48 overflow-y-auto rounded-lg border border-white/10 bg-white/[0.03]">
              {Object.entries(groupedAgents).map(([dept, deptAgents]) => (
                <div key={dept}>
                  <div className="px-3 py-1.5 text-[10px] font-semibold text-white/30 uppercase tracking-wider bg-black/40 sticky top-0">
                    {departmentLabel(dept)}
                  </div>
                  {deptAgents.map((agent) => (
                    <button
                      key={agent.id}
                      onClick={() => toggleAgent(agent.id)}
                      className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-white/5 transition-colors ${
                        selectedAgents.includes(agent.id) ? "bg-white/5" : ""
                      }`}
                    >
                      <div
                        className="w-7 h-7 rounded-full flex items-center justify-center text-white text-[10px] font-bold shrink-0"
                        style={{ backgroundColor: agent.avatar_color }}
                      >
                        {getInitials(agent.name)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-white truncate">
                          {getHumanName(agent.id) || agent.name}
                          {getHumanName(agent.id) && <span className="text-white/20 ml-1.5">({agent.name})</span>}
                        </div>
                        <div className="text-[10px] text-white/30 truncate">{agent.role}</div>
                      </div>
                      {selectedAgents.includes(agent.id) && (
                        <Check className="w-4 h-4 text-purple-400" />
                      )}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          </div>

          {/* Subject */}
          <div>
            <label className="block text-sm font-medium text-white/50 mb-2">Subject:</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g., Q2 Content Strategy Review"
              className="w-full px-4 py-2.5 bg-white/[0.03] border border-white/10 rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50"
            />
          </div>

          {/* Message body */}
          <div>
            <label className="block text-sm font-medium text-white/50 mb-2">Message:</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Write your message to the team..."
              rows={8}
              className="w-full px-4 py-3 bg-white/[0.03] border border-white/10 rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50 resize-none"
            />
          </div>

          <div className="flex justify-end">
            <button
              onClick={handleSend}
              disabled={sending || !subject.trim() || !content.trim() || selectedAgents.length === 0}
              className="px-6 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
            >
              {sending ? "Sending..." : "Send Message"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
