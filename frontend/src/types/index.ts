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

export interface Account {
  email_id: string;
  client_id: string;
  status: "active" | "invalid" | "error";
  tags: string[];
  last_refresh_time?: string;
  next_refresh_time?: string;
  refresh_status: "success" | "failed" | "pending";
  refresh_error?: string;
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

export interface VerificationRule {
  id: number;
  name: string;
  scope_type: "targeted" | "global";
  match_mode: "and" | "or";
  priority: number;
  enabled: boolean;
  sender_pattern?: string | null;
  subject_pattern?: string | null;
  body_pattern?: string | null;
  extract_pattern: string;
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
  matched_sender?: string | null;
  matched_subject?: string | null;
  matched_body_excerpt?: string | null;
}
