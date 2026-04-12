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
  tools: string[];
}

export interface AgentDetail extends AgentSummary {
  system_prompt: string;
  file_path: string;
}

export interface ToolCallInfo {
  id: string;
  tool_name: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown> | null;
  status: "pending" | "executing" | "completed" | "failed";
  error_message: string | null;
  created_at: string | null;
  completed_at: string | null;
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
  message_type: string;
  tool_calls?: ToolCallInfo[] | null;
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

export interface ToolSummary {
  id: string;
  name: string;
  description: string;
  category: string;
  input_schema: Record<string, unknown>;
  requires_approval: boolean;
  enabled: boolean;
}

export interface ToolCallRecord {
  id: string;
  message_id: string | null;
  thread_id: string | null;
  agent_id: string;
  tool_id: string;
  tool_name: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown> | null;
  status: string;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface TaskItem {
  id: string;
  title: string;
  description: string | null;
  assigned_to: string | null;
  due_date: string | null;
  priority: string;
  status: string;
  project: string | null;
  created_by_agent: string | null;
  created_at: string;
  updated_at: string;
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
  // Agents
  getAgents: () => fetchApi<AgentSummary[]>("/api/agents"),
  getAgent: (id: string) => fetchApi<AgentDetail>(`/api/agents/${id}`),
  getOrgTree: () => fetchApi<OrgTree>("/api/agents/org/tree"),

  // Threads
  getThreads: () => fetchApi<ThreadSummary[]>("/api/threads"),
  getThread: (id: string) => fetchApi<ThreadDetail>(`/api/threads/${id}`),
  createThread: (data: { subject: string; recipient_agent_ids: string[]; content: string }) =>
    fetchApi<ThreadSummary>("/api/threads", { method: "POST", body: JSON.stringify(data) }),
  sendMessage: (threadId: string, data: { content: string; recipient_agent_ids?: string[] }) =>
    fetchApi<{ status: string; message_id: string }>(`/api/threads/${threadId}/messages`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Tools
  getTools: () => fetchApi<ToolSummary[]>("/api/tools"),
  getTool: (id: string) => fetchApi<ToolSummary>(`/api/tools/${id}`),
  getToolCalls: (params?: { agent_id?: string; thread_id?: string; status?: string; limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.agent_id) searchParams.set("agent_id", params.agent_id);
    if (params?.thread_id) searchParams.set("thread_id", params.thread_id);
    if (params?.status) searchParams.set("status", params.status);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const qs = searchParams.toString();
    return fetchApi<ToolCallRecord[]>(`/api/tools/calls${qs ? `?${qs}` : ""}`);
  },

  // Tasks
  getTasks: (params?: { status?: string; assigned_to?: string; priority?: string }) => {
    const searchParams = new URLSearchParams();
    if (params?.status) searchParams.set("status", params.status);
    if (params?.assigned_to) searchParams.set("assigned_to", params.assigned_to);
    if (params?.priority) searchParams.set("priority", params.priority);
    const qs = searchParams.toString();
    return fetchApi<TaskItem[]>(`/api/tasks${qs ? `?${qs}` : ""}`);
  },
  getTask: (id: string) => fetchApi<TaskItem>(`/api/tasks/${id}`),
  updateTask: (id: string, data: Partial<TaskItem>) =>
    fetchApi<TaskItem>(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
};
