"use client";

import { useEffect, useState } from "react";
import { api, TaskItem, AgentSummary } from "@/lib/api";
import { timeAgo } from "@/lib/utils";

const priorityColors: Record<string, { color: string; bg: string }> = {
  P0: { color: "#ef4444", bg: "#ef444420" },
  P1: { color: "#f59e0b", bg: "#f59e0b20" },
  P2: { color: "#3b82f6", bg: "#3b82f620" },
  P3: { color: "#6b7280", bg: "#6b728020" },
};

const statusColumns = ["queued", "in_progress", "in_review", "blocked", "complete"];

const statusLabels: Record<string, string> = {
  queued: "Queued",
  in_progress: "In Progress",
  in_review: "In Review",
  blocked: "Blocked",
  complete: "Complete",
};

const statusHeaderColors: Record<string, string> = {
  queued: "#64748b",
  in_progress: "#3b82f6",
  in_review: "#f59e0b",
  blocked: "#ef4444",
  complete: "#10b981",
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [agents, setAgents] = useState<Record<string, AgentSummary>>({});
  const [view, setView] = useState<"board" | "list">("board");

  const fetchData = async () => {
    try {
      const [taskList, agentList] = await Promise.all([api.getTasks(), api.getAgents()]);
      setTasks(taskList);
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
  }, []);

  const tasksByStatus = statusColumns.reduce((acc, status) => {
    acc[status] = tasks.filter((t) => t.status === status);
    return acc;
  }, {} as Record<string, TaskItem[]>);

  return (
    <div className="h-full flex flex-col">
      <header className="px-6 py-4 border-b border-[#334155] flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">Tasks</h2>
          <p className="text-xs text-[#64748b] mt-1">
            {tasks.length} task{tasks.length !== 1 ? "s" : ""} created by agents
          </p>
        </div>
        <div className="flex gap-1 bg-[#1e293b] rounded-lg p-0.5 border border-[#334155]">
          <button
            onClick={() => setView("board")}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              view === "board" ? "bg-[#8b5cf6] text-white" : "text-[#94a3b8] hover:text-white"
            }`}
          >
            Board
          </button>
          <button
            onClick={() => setView("list")}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              view === "list" ? "bg-[#8b5cf6] text-white" : "text-[#94a3b8] hover:text-white"
            }`}
          >
            List
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-auto p-4">
        {tasks.length === 0 ? (
          <div className="flex items-center justify-center h-64 text-[#64748b] text-sm">
            No tasks yet. Agents will create tasks here when they use the create_task tool.
          </div>
        ) : view === "board" ? (
          <div className="flex gap-3 h-full min-w-max">
            {statusColumns.map((status) => (
              <div key={status} className="w-64 flex flex-col shrink-0">
                <div className="flex items-center gap-2 px-3 py-2 mb-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: statusHeaderColors[status] }} />
                  <span className="text-xs font-semibold text-[#94a3b8] uppercase tracking-wider">
                    {statusLabels[status]}
                  </span>
                  <span className="text-[10px] text-[#64748b] bg-[#1e293b] px-1.5 py-0.5 rounded-full">
                    {tasksByStatus[status]?.length || 0}
                  </span>
                </div>
                <div className="space-y-2 flex-1 overflow-y-auto">
                  {(tasksByStatus[status] || []).map((task) => {
                    const pc = priorityColors[task.priority] || priorityColors.P2;
                    const assignee = task.assigned_to ? agents[task.assigned_to] : null;
                    const creator = task.created_by_agent ? agents[task.created_by_agent] : null;

                    return (
                      <div
                        key={task.id}
                        className="bg-[#1e293b] border border-[#334155] rounded-lg p-3 hover:border-[#475569] transition-colors"
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <h3 className="text-sm font-medium text-[#e2e8f0] leading-tight">{task.title}</h3>
                          <span
                            className="text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0"
                            style={{ backgroundColor: pc.bg, color: pc.color }}
                          >
                            {task.priority}
                          </span>
                        </div>
                        {task.description && (
                          <p className="text-[11px] text-[#64748b] mb-2 line-clamp-2">{task.description}</p>
                        )}
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-1">
                            {assignee && (
                              <span className="text-[10px] text-[#94a3b8] flex items-center gap-1">
                                <span
                                  className="w-4 h-4 rounded-full inline-flex items-center justify-center text-[6px] text-white font-bold"
                                  style={{ backgroundColor: assignee.avatar_color }}
                                >
                                  {assignee.name.split(" ").map((w) => w[0]).join("").slice(0, 2)}
                                </span>
                                {assignee.name.split(" ").slice(0, 2).join(" ")}
                              </span>
                            )}
                          </div>
                          {task.due_date && (
                            <span className="text-[10px] text-[#64748b]">{task.due_date}</span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="divide-y divide-[#334155] border border-[#334155] rounded-lg overflow-hidden">
            <div className="grid grid-cols-[1fr_120px_100px_120px_100px] gap-2 px-4 py-2 bg-[#1e293b] text-[10px] font-semibold text-[#64748b] uppercase tracking-wider">
              <span>Title</span>
              <span>Assignee</span>
              <span>Priority</span>
              <span>Status</span>
              <span>Due</span>
            </div>
            {tasks.map((task) => {
              const pc = priorityColors[task.priority] || priorityColors.P2;
              const assignee = task.assigned_to ? agents[task.assigned_to] : null;

              return (
                <div key={task.id} className="grid grid-cols-[1fr_120px_100px_120px_100px] gap-2 px-4 py-2.5 items-center hover:bg-[#ffffff05]">
                  <span className="text-sm text-[#e2e8f0] truncate">{task.title}</span>
                  <span className="text-xs text-[#94a3b8] truncate">{assignee?.name || task.assigned_to || "—"}</span>
                  <span
                    className="text-[10px] font-bold px-1.5 py-0.5 rounded w-fit"
                    style={{ backgroundColor: pc.bg, color: pc.color }}
                  >
                    {task.priority}
                  </span>
                  <span
                    className="text-[10px] px-1.5 py-0.5 rounded w-fit"
                    style={{ backgroundColor: statusHeaderColors[task.status] + "20", color: statusHeaderColors[task.status] }}
                  >
                    {statusLabels[task.status] || task.status}
                  </span>
                  <span className="text-xs text-[#64748b]">{task.due_date || "—"}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
