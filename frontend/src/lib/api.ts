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

export interface ModelInfo {
  active_preset: string;
  model: string;
  label: string;
  max_tokens: number;
  router_model: string;
  extended_thinking: boolean;
  thinking_budget: number | null;
  context_window: number;
  available_presets: string[];
}

export interface WorkflowInfo {
  id: string;
  name: string;
  description: string;
  agents_used: string[];
  channel_specific: boolean;
}

export interface ChannelInfo {
  id: string;
  name: string;
  description: string;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  channel: string | null;
  status: "running" | "completed" | "failed";
  session_id: string | null;
  output: string;
  created_at: string;
  completed_at: string | null;
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
  getModelInfo: () => fetchApi<ModelInfo>("/api/model"),
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

  // Automation
  getWorkflows: () => fetchApi<WorkflowInfo[]>("/api/automation/workflows"),
  getChannels: () => fetchApi<ChannelInfo[]>("/api/automation/channels"),
  runWorkflow: (workflowId: string, channel?: string) =>
    fetchApi<{ id: string; workflow_id: string; channel: string | null; status: string }>(
      `/api/automation/run/${workflowId}`,
      { method: "POST", body: JSON.stringify({ channel: channel || null }) },
    ),
  getAutomationHistory: () => fetchApi<WorkflowRun[]>("/api/automation/history"),
  getRunDetail: (runId: string) => fetchApi<WorkflowRun>(`/api/automation/history/${runId}`),
  streamUrl: (runId: string) => `${API_URL}/api/automation/stream/${runId}`,
};
