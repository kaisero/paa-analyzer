export interface Session {
  id: string;
  filename: string;
  file_size: number;
  created_at: string;
  parse_status: string;
  parse_error: string | null;
  parse_duration_ms: number | null;
  platform: string;
  total_log_entries: number;
  total_log_sources: number;
  total_state_files: number;
}

export interface LogSource {
  source: string;
  total_entries: number;
  levels: Record<string, number>;
  time_range: { from: string | null; to: string | null };
  module: string;
  component: string;
}

export interface LogEntry {
  timestamp: string;
  level: string;
  source: string;
  message: string;
  beautified?: string;
  [key: string]: unknown;
}

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface DataResponse<T> {
  data: T;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

// State Viewer types

export interface StateKeyInfo {
  key: string;
  module: string;
  component: string;
  name: string;
  pacli_command?: string;
}

export interface StateEntry {
  _meta: {
    type: string;
    module: string;
    component: string;
    source_file: string;
    name: string;
  };
  data: Record<string, unknown>;
  raw_text?: string;
}

export type StateBatchResponse = Record<string, StateEntry>;

export interface ForwardingRule {
  priority: number;
  name: string;
  enabled: boolean;
  source_apps: string;
  destinations: string;
  connection_type: string;
  connect_through: string;
  hits: number;
  traffic_log_hits: number;
}

export interface ForwardingProfile {
  rules: ForwardingRule[];
  flags: string[];
}
