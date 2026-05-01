export interface User {
  id: number;
  username: string;
  email?: string;
  role: "admin" | "user";
  bound_accounts?: string[];
  permissions?: string[];
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export type StrategyMode = "auto" | "graph_preferred" | "graph_only" | "imap_only";
export type ProviderOverride = "auto" | "graph" | "imap";

export interface Account {
  email_id: string;
  client_id: string;
  status: "active" | "invalid" | "error";
  tags: string[];
  last_refresh_time?: string;
  next_refresh_time?: string;
  refresh_status: "success" | "failed" | "pending";
  refresh_error?: string;
  strategy_mode?: StrategyMode;
  lifecycle_state?: string;
  last_provider_used?: string;
  capability_snapshot_json?: string;
  provider_health_json?: string;
}

export interface CapabilitySnapshot {
  graph_available?: boolean | null;
  graph_read_available?: boolean | null;
  graph_write_available?: boolean | null;
  graph_send_available?: boolean | null;
  imap_available?: boolean | null;
  recommended_provider?: string | null;
  last_probe_at?: string | null;
  last_probe_source?: string | null;
  graph_probe_status?: string | null;
  graph_probe_error?: string | null;
}

export interface ProviderError {
  code?: string | null;
  message?: string | null;
  at?: string | null;
}

export interface AccountHealth {
  email: string;
  strategy_mode: StrategyMode;
  lifecycle_state: string;
  capability: CapabilitySnapshot;
  last_provider_used?: string | null;
  last_error?: ProviderError | null;
}

export interface DeliveryStrategy {
  email: string;
  strategy_mode: StrategyMode;
  recommended_provider?: string | null;
  resolved_provider?: string | null;
  provider_order: string[];
  last_provider_used?: string | null;
  override_active: boolean;
  override_provider?: string | null;
  skip_cache: boolean;
  capability: CapabilitySnapshot;
}

export interface AccountProbeResult {
  token_ok: boolean;
  capability: CapabilitySnapshot;
  lifecycle_state: string;
  warnings: string[];
}

export interface V2MessageQuery {
  folder?: string;
  page?: number;
  page_size?: number;
  sender_search?: string;
  subject_search?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
  start_time?: string;
  end_time?: string;
  override_provider?: ProviderOverride | null;
  strategy_mode?: StrategyMode | null;
  skip_cache?: boolean;
}

export interface Email {
  message_id: string;
  folder: string;
  subject: string;
  from_email: string;
  date: string;
  is_read: boolean;
  has_attachments: boolean;
  sender_initial: string;
  verification_code?: string;
  body_preview?: string;
  // 以下字段为可选，如果列表接口返回了完整内容，可直接使用，无需再次请求详情
  to_email?: string;
  body_plain?: string;
  body_html?: string;
}

export interface EmailDetail {
  message_id: string;
  subject: string;
  from_email: string;
  to_email: string;
  date: string;
  body_plain?: string;
  body_html?: string;
  verification_code?: string;
}

export interface ConfigItem {
  id: number;
  key: string;
  value: string;
  description?: string;
  updated_at: string;
}

export interface ShareToken {
  id: number;
  token: string;
  email_account_id: string;
  start_time: string;
  end_time?: string;
  expiry_time?: string;
  is_active: boolean;
  subject_keyword?: string;
  sender_keyword?: string;
  max_emails?: number;
  created_at: string;
}

export interface VerificationRuleMatcher {
  id?: number;
  rule_id?: number;
  source_type: "sender" | "subject" | "body";
  keyword: string;
  sort_order: number;
  created_at?: string;
  updated_at?: string;
}

export interface VerificationRuleExtractor {
  id?: number;
  rule_id?: number;
  source_type: "subject" | "body";
  extract_pattern: string;
  sort_order: number;
  created_at?: string;
  updated_at?: string;
}

export interface VerificationRule {
  id: number;
  name: string;
  scope_type: "targeted" | "global";
  match_mode: "and" | "or";
  priority: number;
  enabled: boolean;
  matchers: VerificationRuleMatcher[];
  extractors: VerificationRuleExtractor[];
  is_regex: boolean;
  description?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface VerificationRuleTestResult {
  code?: string | null;
  matched_rule?: VerificationRule | null;
  matched_via?: "rule" | "fallback" | null;
  source: string;
  page_source: string;
  rule_evaluations: Array<Record<string, unknown>>;
  matched_matchers?: VerificationRuleMatcher[];
  extractor_attempts?: Array<Record<string, unknown>>;
  resolved_code_source?: "subject" | "body" | null;
  matched_sender?: string | null;
  matched_subject?: string | null;
  matched_body_excerpt?: string | null;
}
