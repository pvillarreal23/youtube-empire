"use client";

import { useEffect, useState, useRef, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api, ThreadDetail, AgentSummary } from "@/lib/api";
import { getInitials, timeAgo } from "@/lib/utils";
import ToolCallBlock from "@/components/ToolCallBlock";

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

  if (!threadId) return <div className="flex items-center justify-center h-full text-[#64748b]">No thread selected</div>;
  if (!thread) return <div className="flex items-center justify-center h-full text-[#64748b]">Loading...</div>;

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-[#334155]">
        <h2 className="text-lg font-semibold text-white">{thread.subject}</h2>
        <div className="flex items-center gap-2 mt-1">
          {thread.participants.map((pid) => {
            const agent = agents[pid];
            return (
              <span key={pid} className="inline-flex items-center gap-1 text-xs text-[#94a3b8]">
                <span
                  className="w-4 h-4 rounded-full inline-flex items-center justify-center text-[6px] text-white font-bold"
                  style={{ backgroundColor: agent?.avatar_color || "#6366f1" }}
                >
                  {getInitials(agent?.name || pid)}
                </span>
                {agent?.name || pid}
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
                  <span className="text-xs font-semibold text-[#94a3b8]">
                    {isUser ? "You" : agent?.name || msg.sender_agent_id}
                  </span>
                  {agent && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded" style={{ backgroundColor: agent.avatar_color + "20", color: agent.avatar_color }}>
                      {agent.role}
                    </span>
                  )}
                  <span className="text-[10px] text-[#64748b]">{timeAgo(msg.created_at)}</span>
                </div>
                <div
                  className={`rounded-lg px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                    isUser
                      ? "bg-[#8b5cf6] text-white"
                      : "bg-[#1e293b] text-[#e2e8f0] border border-[#334155]"
                  }`}
                >
                  {msg.content}
                  {msg.tool_calls && msg.tool_calls.length > 0 && (
                    <div className="mt-3 space-y-1">
                      {msg.tool_calls.map((tc) => (
                        <ToolCallBlock key={tc.id} toolCall={tc} />
                      ))}
                    </div>
                  )}
                </div>
              </div>
              {isUser && (
                <div className="w-9 h-9 rounded-full bg-[#8b5cf6] flex items-center justify-center text-white text-xs font-bold shrink-0">
                  U
                </div>
              )}
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      <div className="px-6 py-4 border-t border-[#334155]">
        <div className="flex gap-3">
          <input
            type="text"
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder="Type a reply..."
            className="flex-1 px-4 py-2.5 bg-[#1e293b] border border-[#334155] rounded-lg text-sm text-white placeholder-[#64748b] focus:outline-none focus:border-[#8b5cf6]"
          />
          <button
            onClick={handleSend}
            disabled={sending || !reply.trim()}
            className="px-5 py-2.5 bg-[#8b5cf6] hover:bg-[#7c3aed] disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
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
    <Suspense fallback={<div className="flex items-center justify-center h-full text-[#64748b]">Loading...</div>}>
      <ThreadContent />
    </Suspense>
  );
}
