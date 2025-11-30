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
  created_at: string;
}
