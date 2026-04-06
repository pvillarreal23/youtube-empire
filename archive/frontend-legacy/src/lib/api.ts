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
};
