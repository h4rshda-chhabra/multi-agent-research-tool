export interface User {
  id: string;
  name: string;
  email: string;
  plan: "free" | "pro";
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user_id: string;
  name: string;
  email: string;
  plan: string;
}

export type ReportStatus = "pending" | "running" | "complete" | "failed";

export type AgentName = "planner" | "search" | "validator" | "extractor" | "synthesizer";

export type AgentStatus = "idle" | "running" | "complete" | "error";

export interface AgentStep {
  name: AgentName;
  label: string;
  status: AgentStatus;
  message?: string;
}

export interface Source {
  id: string;
  url: string;
  title: string;
  domain: string;
  snippet: string | null;
  published_date: string | null;
  relevance_score: number;
  credibility_score: number;
  recency_score: number;
  technical_depth_score: number;
  total_score: number;
}

export interface AgentRun {
  id: string;
  agent_name: string;
  status: string;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface Report {
  id: string;
  user_id: string;
  topic: string;
  status: ReportStatus;
  markdown_content: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  sources: Source[];
  agent_runs: AgentRun[];
  is_saved: boolean;
}

export interface ReportListItem {
  id: string;
  topic: string;
  status: ReportStatus;
  created_at: string;
  is_saved: boolean;
}

export interface SSEEvent {
  type: "agent_start" | "agent_complete" | "agent_error" | "complete" | "error" | "ping";
  agent?: AgentName;
  message: string;
  report_id: string;
  data?: Record<string, unknown>;
}
