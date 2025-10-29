/**
 * OutlookManager 前端类型定义
 */

// ============================================================================
// 认证相关类型
// ============================================================================

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  admin_id: string;
  username: string;
  message: string;
}

export interface Admin {
  id: string;
  username: string;
  email: string | null;
  is_active: boolean;
  last_login: string | null;
  created_at: string;
}

// ============================================================================
// 账户相关类型
// ============================================================================

export type AccountStatus = "active" | "inactive" | "suspended" | "error";
export type RefreshStatus = "pending" | "success" | "failed" | "in_progress";

export interface Account {
  id: string;
  email: string;
  client_id: string;
  tags: string[];
  status: AccountStatus;
  refresh_status: RefreshStatus;
  last_refresh_time: string | null;
  next_refresh_time: string | null;
  refresh_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface AccountCreateRequest {
  email: string;
  refresh_token: string;
  client_id: string;
  tags?: string[];
}

export interface AccountUpdateRequest {
  tags?: string[];
  status?: AccountStatus;
  refresh_token?: string;
  client_id?: string;
}

export interface AccountListResponse {
  items: Account[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ============================================================================
// 邮件相关类型
// ============================================================================

export type EmailFolder = "INBOX" | "SENT" | "DRAFTS" | "TRASH" | "JUNK";
export type EmailStatus = "unread" | "read" | "archived" | "deleted";

export interface EmailAddress {
  address: string;
  name?: string | null;
}

export interface Email {
  id: string;
  account_id: string;
  message_id: string;
  subject: string;
  sender: EmailAddress;
  recipients: EmailAddress[];
  folder: EmailFolder;
  sent_at: string;
  body_preview: string;
  status: EmailStatus;
  is_flagged: boolean;
  has_attachments: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmailDetail extends Email {
  full_body: string | null;
}

export interface EmailListParams {
  folder?: EmailFolder;
  search_query?: string;
  is_read?: boolean;
  has_attachments?: boolean;
  start_date?: string;
  end_date?: string;
}

// ============================================================================
// 统计相关类型
// ============================================================================

export interface SystemStats {
  total_accounts: number;
  active_accounts: number;
  total_emails: number;
  unread_emails: number;
}

// ============================================================================
// API响应类型
// ============================================================================

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

