/**
 * API 客户端
 * 
 * 提供与后端API通信的统一接口
 */

import type {
  LoginRequest,
  LoginResponse,
  Admin,
  Account,
  AccountCreateRequest,
  AccountUpdateRequest,
  AccountListResponse,
  Email,
  EmailDetail,
  EmailListParams,
  SystemStats,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
    // 从 localStorage 恢复 token
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("access_token");
    }
  }

  /**
   * 设置认证 Token
   */
  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem("access_token", token);
      } else {
        localStorage.removeItem("access_token");
      }
    }
  }

  /**
   * 获取当前 Token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * 通用请求方法
   */
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);

      // 处理 204 No Content
      if (response.status === 204) {
        return {} as T;
      }

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.message || "请求失败");
      }

      return data;
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("网络请求失败");
    }
  }

  // ============================================================================
  // 认证相关
  // ============================================================================

  /**
   * 登录
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    this.setToken(response.access_token);
    return response;
  }

  /**
   * 登出
   */
  logout() {
    this.setToken(null);
  }

  /**
   * 验证 Token
   */
  async verifyToken(): Promise<boolean> {
    try {
      await this.request("/api/v1/auth/verify-token", {
        method: "POST",
      });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 修改密码
   */
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await this.request("/api/v1/auth/change-password", {
      method: "POST",
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
      }),
    });
  }

  // ============================================================================
  // 管理员相关
  // ============================================================================

  /**
   * 获取管理员资料
   */
  async getAdminProfile(): Promise<Admin> {
    return this.request<Admin>("/api/v1/admin/profile");
  }

  /**
   * 更新管理员资料
   */
  async updateAdminProfile(data: Partial<Admin>): Promise<Admin> {
    return this.request<Admin>("/api/v1/admin/profile", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * 获取系统统计
   */
  async getSystemStats(): Promise<SystemStats> {
    return this.request<SystemStats>("/api/v1/admin/stats");
  }

  // ============================================================================
  // 账户管理
  // ============================================================================

  /**
   * 获取账户列表
   */
  async getAccounts(params?: {
    page?: number;
    page_size?: number;
    email_search?: string;
    tag_search?: string;
  }): Promise<AccountListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.page_size) searchParams.set("page_size", params.page_size.toString());
    if (params?.email_search) searchParams.set("email_search", params.email_search);
    if (params?.tag_search) searchParams.set("tag_search", params.tag_search);

    const query = searchParams.toString();
    return this.request<AccountListResponse>(
      `/api/v1/accounts${query ? `?${query}` : ""}`
    );
  }

  /**
   * 获取账户详情
   */
  async getAccount(id: string): Promise<Account> {
    return this.request<Account>(`/api/v1/accounts/${id}`);
  }

  /**
   * 创建账户
   */
  async createAccount(data: AccountCreateRequest): Promise<Account> {
    return this.request<Account>("/api/v1/accounts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  /**
   * 更新账户
   */
  async updateAccount(id: string, data: AccountUpdateRequest): Promise<Account> {
    return this.request<Account>(`/api/v1/accounts/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  /**
   * 删除账户
   */
  async deleteAccount(id: string): Promise<void> {
    await this.request(`/api/v1/accounts/${id}`, {
      method: "DELETE",
    });
  }

  /**
   * 刷新账户 Token
   */
  async refreshAccountToken(id: string): Promise<void> {
    await this.request(`/api/v1/accounts/${id}/refresh-token`, {
      method: "POST",
    });
  }

  // ============================================================================
  // 邮件管理
  // ============================================================================

  /**
   * 获取邮件列表
   */
  async getEmails(
    accountId: string,
    params?: EmailListParams & { skip?: number; limit?: number }
  ): Promise<{ items: Email[]; total: number }> {
    const searchParams = new URLSearchParams();
    if (params?.folder) searchParams.set("folder", params.folder);
    if (params?.search_query) searchParams.set("search_query", params.search_query);
    if (params?.skip !== undefined) searchParams.set("skip", params.skip.toString());
    if (params?.limit !== undefined) searchParams.set("limit", params.limit.toString());

    const query = searchParams.toString();
    return this.request<{ items: Email[]; total: number }>(
      `/api/v1/emails/${accountId}${query ? `?${query}` : ""}`
    );
  }

  /**
   * 获取邮件详情
   */
  async getEmailDetail(accountId: string, messageId: string): Promise<EmailDetail> {
    return this.request<EmailDetail>(`/api/v1/emails/${accountId}/${messageId}`);
  }

  /**
   * 搜索邮件
   */
  async searchEmails(accountId: string, params: EmailListParams): Promise<Email[]> {
    return this.request<Email[]>(`/api/v1/emails/${accountId}/search`, {
      method: "POST",
      body: JSON.stringify(params),
    });
  }

  // ============================================================================
  // 健康检查
  // ============================================================================

  /**
   * 健康检查
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.request<{ status: string }>("/health");
  }
}

// 导出单例实例
export const apiClient = new ApiClient();

// 导出类型以便其他地方使用
export type { ApiClient };

