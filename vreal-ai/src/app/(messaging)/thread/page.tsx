"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api, ThreadDetail, AgentSummary } from "@/lib/api";
import { getInitials, timeAgo } from "@/lib/utils";
import { getHumanName } from "@/lib/constants";

function ThreadContent() {
  const searchParams = useSearchParams();
  const threadId = searchParams.get("id");
  const [thread, setThread] = useState<ThreadDetail | null>(null);
  const [agents, setAgents] = useState<Record<string, AgentSummary>>({});
  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const fetchThread = async () => {
    if (!threadId) return;
    try {
      const [t, a] = await Promise.all([api.getThread(threadId), api.getAgents()]);
      setThread(t);
      const agentMap: Record<string, AgentSummary> = {};
      a.forEach((ag) => (agentMap[ag.id] = ag));
      setAgents(agentMap);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchThread();
    const interval = setInterval(fetchThread, 3000);
    return () => clearInterval(interval);
  }, [threadId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thread?.messages.length]);

  const handleSend = async () => {
    if (!reply.trim() || !threadId) return;
    setSending(true);
    try {
      await api.sendMessage(threadId, { content: reply });
      setReply("");
      await fetchThread();
    } catch (e) {
      console.error(e);
    } finally {
      setSending(false);
    }
  };

  if (!threadId) return <div className="flex items-center justify-center h-full text-white/30">No thread selected</div>;
  if (!thread) return <div className="flex items-center justify-center h-full text-white/30">Loading...</div>;

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-white/5">
        <h2 className="text-lg font-semibold text-white">{thread.subject}</h2>
        <div className="flex items-center gap-2 mt-1 flex-wrap">
          {thread.participants.map((pid) => {
            const agent = agents[pid];
            return (
              <span key={pid} className="inline-flex items-center gap-1 text-xs text-white/40">
                <span
                  className="w-4 h-4 rounded-full inline-flex items-center justify-center text-[6px] text-white font-bold"
                  style={{ backgroundColor: agent?.avatar_color || "#6366f1" }}
                >
                  {getInitials(agent?.name || pid)}
                </span>
                {getHumanName(pid) || agent?.name || pid}
              </span>
            );
          })}
        </div>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {thread.messages.map((msg) => {
          const isUser = msg.sender_type === "user";
          const agent = msg.sender_agent_id ? agents[msg.sender_agent_id] : null;

          return (
            <div key={msg.id} className={`flex gap-3 ${isUser ? "justify-end" : ""}`}>
              {!isUser && (
                <div
                  className="w-9 h-9 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
                  style={{ backgroundColor: agent?.avatar_color || "#6366f1" }}
                >
                  {getInitials(agent?.name || "?")}
                </div>
              )}
              <div className={`max-w-[70%] ${isUser ? "order-first" : ""}`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-white/50">
                    {isUser ? "Pedro" : getHumanName(msg.sender_agent_id || "") || agent?.name || msg.sender_agent_id}
                  </span>
                  {agent && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: agent.avatar_color + "20", color: agent.avatar_color }}>
                      {agent.role}
                    </span>
                  )}
                  <span className="text-[10px] text-white/20">{timeAgo(msg.created_at)}</span>
                </div>
                <div
                  className={`rounded-lg px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                    isUser
                      ? "bg-purple-600 text-white"
                      : "bg-white/[0.03] text-white/80 border border-white/5"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
              {isUser && (
                <img src="/avatars/pedro.jpg" className="w-9 h-9 rounded-full object-cover shrink-0 ring-2 ring-purple-500/50" alt="Pedro" />
              )}
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      <div className="px-6 py-4 border-t border-white/5">
        <div className="flex gap-3">
          <input
            type="text"
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="Type a reply..."
            className="flex-1 px-4 py-2.5 bg-white/[0.03] border border-white/10 rounded-lg text-sm text-white placeholder-white/20 focus:outline-none focus:border-purple-500/50"
          />
          <button
            onClick={handleSend}
            disabled={sending || !reply.trim()}
            className="px-5 py-2.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
          >
            {sending ? "..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ThreadPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-full text-white/30">Loading...</div>}>
      <ThreadContent />
    </Suspense>
  );
}
