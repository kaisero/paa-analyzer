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

// HIP (Host Information Profile) types

export interface HipGateway {
  gateway: string | null;
  last_report: string | null;
  status: string | null;
  status_kind: 'success' | 'failed' | 'not-needed' | 'unknown' | null;
  age_days: number | null;
}

export interface OpswatError {
  code: number;
  code_meaning: string | null;
  method: number;
  method_name: string | null;
  signature: number | null;
  category_id: number;
  category: string | null;
  product: string | null;
  source: string;
  raw_message: string;
}

export interface MissingPatch {
  title: string | null;
  description: string | null;
  product: string | null;
  vendor: string | null;
  info_url: string | null;
  kb_article_id: string | null;
  security_bulletin_id: string | null;
  severity: string | null;
  category: string | null;
  is_installed: string | null;
  deadline_info: string | null;
  reboot_required: boolean;
}

export interface HipDrive {
  name: string | null;
  enc_state: string | null;
}

export interface HipProduct {
  name: string | null;
  version: string | null;
  vendor: string | null;
  def_version: string | null;
  def_date: string | null;
  signature: number | null;
  attributes: Record<string, unknown>;
  drives?: HipDrive[];
  errors: OpswatError[];
  status: 'ok' | 'warn' | 'unknown' | 'not-detected';
  status_reason: string | null;
}

export interface HipCategory {
  name: string | null;
  products: HipProduct[];
  missing_patches: MissingPatch[];
  patches_source: string | null;
  status: 'ok' | 'warn' | 'unknown' | 'not-detected';
  status_reason: string | null;
}

export interface HipInterface {
  name: string | null;
  description: string | null;
  mac: string | null;
  ipv4: (string | null)[];
  ipv6: (string | null)[];
}

export interface HipHostInfo {
  os: string | null;
  os_vendor: string | null;
  client_version: string | null;
  host_name: string | null;
  domain: string | null;
  host_id: string | null;
  host_id_kind: 'mac-address' | 'machine-guid' | 'unknown';
  interfaces: HipInterface[];
}

export interface HipReport {
  version: string | null;
  host_info: HipHostInfo | null;
  categories: HipCategory[];
  custom_checks: { kind: 'plist' | 'registry' | 'unknown'; entries: unknown[] } | null;
}

export interface HipPolicy {
  collection_hip_data: boolean | null;
  max_wait_time: number | null;
  default_categories: string[] | null;
  exclusion_categories: string[] | null;
  custom_check: unknown;
  certs: unknown;
  raw: Record<string, unknown>;
}

export interface HipDispatch {
  sent: boolean;
  succeeded: boolean;
  status_code: number | null;
}

export interface HipCounts {
  warn: number;
  unknown: number;
  errors: number;
  missing_patches: number;
}

export interface HipCycle {
  index: number;
  started_at: string | null;
  generate_time: string | null;
  duration_s: number | null;
  partial: boolean;
  policy: HipPolicy | null;
  report: HipReport | null;
  opswat_errors: OpswatError[];
  category_timings: Record<string, number>;
  dispatch: HipDispatch;
  counts: HipCounts;
}

export interface HipData {
  platform: 'macos' | 'windows' | 'unknown';
  collection: string | null;
  next_check: string | null;
  gateways: HipGateway[];
  cycles: HipCycle[];
}

export interface HipRaw {
  raw_xml: string | null;
  raw_patches_xml: string | null;
}
