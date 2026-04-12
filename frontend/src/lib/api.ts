const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AgentSummary {
  id: string;
  name: string;
  role: string;
  reports_to: string | null;
  direct_reports: string[];
  collaborates_with: string[];
  avatar_color: string;
  department: string;
}

export interface AgentDetail extends AgentSummary {
  system_prompt: string;
  file_path: string;
}

export interface ThreadMessage {
  id: string;
  thread_id: string;
  sender_type: "user" | "agent";
  sender_agent_id: string | null;
  sender_name?: string;
  content: string;
  created_at: string;
  status: string;
}

export interface ThreadSummary {
  id: string;
  subject: string;
  created_at: string;
  updated_at: string;
  status: string;
  participants: string[];
}

export interface ThreadDetail extends ThreadSummary {
  messages: ThreadMessage[];
}

export interface OrgNode {
  id: string;
  name: string;
  role: string;
  department: string;
  color: string;
}

export interface OrgTree {
  nodes: OrgNode[];
  edges: { source: string; target: string }[];
}

export interface SandboxTask {
  id: string;
  agent_id: string;
  managed_agent_id: string | null;
  environment_id: string | null;
  session_id: string | null;
  task: string;
  status: "pending" | "running" | "completed" | "failed";
  result: string | null;
  created_at: string;
  updated_at: string;
}

export interface SandboxTaskEvents {
  session_id: string;
  status: string;
  events: { type: string; text?: string }[];
}

async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getAgents: () => fetchApi<AgentSummary[]>("/api/agents"),
  getAgent: (id: string) => fetchApi<AgentDetail>(`/api/agents/${id}`),
  getOrgTree: () => fetchApi<OrgTree>("/api/agents/org/tree"),
  getThreads: () => fetchApi<ThreadSummary[]>("/api/threads"),
  getThread: (id: string) => fetchApi<ThreadDetail>(`/api/threads/${id}`),
  createThread: (data: { subject: string; recipient_agent_ids: string[]; content: string }) =>
    fetchApi<ThreadSummary>("/api/threads", { method: "POST", body: JSON.stringify(data) }),
  sendMessage: (threadId: string, data: { content: string; recipient_agent_ids?: string[] }) =>
    fetchApi<{ status: string; message_id: string }>(`/api/threads/${threadId}/messages`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Sandbox (Managed Agents)
  dispatchToSandbox: (data: { agent_id: string; task: string }) =>
    fetchApi<SandboxTask>("/api/sandbox/dispatch", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  getSandboxTasks: () => fetchApi<SandboxTask[]>("/api/sandbox/tasks"),
  getSandboxTask: (taskId: string) => fetchApi<SandboxTask>(`/api/sandbox/tasks/${taskId}`),
  getSandboxTaskEvents: (taskId: string) =>
    fetchApi<SandboxTaskEvents>(`/api/sandbox/tasks/${taskId}/events`),
  getAgentSandboxTasks: (agentId: string) =>
    fetchApi<SandboxTask[]>(`/api/sandbox/tasks/agent/${agentId}`),
};
