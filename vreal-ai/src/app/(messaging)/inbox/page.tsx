"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ThreadSummary, AgentSummary } from "@/lib/api";
import { timeAgo, getInitials } from "@/lib/utils";
import { getHumanName } from "@/lib/constants";
import { Mail } from "lucide-react";

export default function InboxPage() {
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [agents, setAgents] = useState<Record<string, AgentSummary>>({});
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [t, a] = await Promise.all([api.getThreads(), api.getAgents()]);
      setThreads(t);
      const agentMap: Record<string, AgentSummary> = {};
      a.forEach((ag) => (agentMap[ag.id] = ag));
      setAgents(agentMap);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <h2 className="text-xl font-semibold text-white">Inbox</h2>
        <Link
          href="/compose"
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm font-medium rounded-lg transition-colors"
        >
          + New Message
        </Link>
      </header>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-64 text-white/30">Loading...</div>
        ) : threads.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-white/30">
            <Mail className="w-16 h-16 mb-4 opacity-30" />
            <p className="text-lg">No messages yet</p>
            <p className="text-sm mt-1">Send your first message to an agent</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {threads.map((thread) => (
              <Link
                key={thread.id}
                href={`/thread?id=${thread.id}`}
                className="flex items-center gap-4 px-6 py-4 hover:bg-white/[0.02] transition-colors cursor-pointer"
              >
                <div className="flex -space-x-2">
                  {thread.participants.slice(0, 3).map((pid) => {
                    const agent = agents[pid];
                    return (
                      <div
                        key={pid}
                        className="w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold border-2 border-[#0a0a0a]"
                        style={{ backgroundColor: agent?.avatar_color || "#6366f1" }}
                        title={agent?.name}
                      >
                        {getInitials(agent?.name || pid)}
                      </div>
                    );
                  })}
                  {thread.participants.length > 3 && (
                    <div className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center text-white/50 text-xs font-bold border-2 border-[#0a0a0a]">
                      +{thread.participants.length - 3}
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-white truncate">{thread.subject}</h3>
                    <span className="text-xs text-white/30 ml-2 shrink-0">{timeAgo(thread.updated_at)}</span>
                  </div>
                  <p className="text-xs text-white/40 mt-0.5 truncate">
                    {thread.participants.map((p) => getHumanName(p) || agents[p]?.name || p).join(", ")}
                  </p>
                </div>
                <div
                  className={`px-2 py-0.5 rounded text-xs font-medium ${
                    thread.status === "active"
                      ? "bg-emerald-500/10 text-emerald-400"
                      : "bg-white/5 text-white/30"
                  }`}
                >
                  {thread.status}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
