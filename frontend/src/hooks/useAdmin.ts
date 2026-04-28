import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api, { ApiError, extractApiErrorMessage } from "@/lib/api";
import { User, ConfigItem, VerificationRule, VerificationRuleTestResult } from "@/types";
import { toast } from "sonner";

type TableCellValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | Record<string, unknown>
  | unknown[];

export type TableRecord = Record<string, TableCellValue>;

interface CreateUserPayload {
    username: string;
    password: string;
    email?: string | null;
    role: User["role"];
    bound_accounts?: string[];
    permissions?: string[];
    is_active: boolean;
}

export interface UpdateUserPayload {
    email?: string | null;
    role?: User["role"];
    bound_accounts?: string[] | null;
    permissions?: string[] | null;
    is_active?: boolean;
}

interface UpdateUserInput {
    username: string;
    update: UpdateUserPayload;
}

interface UpdateUserPasswordInput {
    username: string;
    new_password: string;
}

interface TableDataParams {
    page?: number;
    page_size?: number;
    search?: string;
    sort_by?: string;
    sort_order?: "asc" | "desc";
    field_search?: Record<string, string>;
}

interface TableRecordMutationInput {
    tableName: string;
    data: TableRecord;
}

interface TableRecordUpdateInput extends TableRecordMutationInput {
    recordId: number;
}

const getMutationErrorMessage = (error: ApiError, fallback: string): string =>
    extractApiErrorMessage(error, fallback);

// ... existing User and Config code ...

// --- User Management ---
interface UserListResponse {
    total_users: number;
    page: number;
    page_size: number;
    total_pages: number;
    users: User[];
}

export function useUsers(params: { page?: number; page_size?: number; search?: string } = {}) {
    return useQuery({
        queryKey: ["users", params],
        queryFn: async () => {
            const { data } = await api.get<UserListResponse>("/admin/users", { 
                params: {
                    page: params.page || 1,
                    page_size: params.page_size || 50,
                    search: params.search || undefined
                } 
            });
            return data;
        }
    });
}

export function useCreateUser() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: CreateUserPayload) => {
            return api.post("/admin/users", data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["users"] });
            toast.success("User created successfully");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "Failed to create user"));
        }
    });
}

export function useUpdateUser() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: UpdateUserInput) => {
            return api.put(`/admin/users/${data.username}`, data.update);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["users"] });
            toast.success("User updated successfully");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "Failed to update user"));
        }
    });
}

export function useUpdateUserPassword() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: UpdateUserPasswordInput) => {
            return api.put(`/admin/users/${data.username}/password`, {
                new_password: data.new_password
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["users"] });
            toast.success("密码修改成功");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "修改密码失败"));
        }
    });
}

export function useDeleteUser() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (username: string) => {
            return api.delete(`/admin/users/${username}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["users"] });
            toast.success("User deleted successfully");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "Failed to delete user"));
        }
    });
}

// --- Config Management ---
interface ConfigListResponse {
    configs: ConfigItem[];
}

export function useConfigs() {
    return useQuery({
        queryKey: ["configs"],
        queryFn: async () => {
            const { data } = await api.get<ConfigListResponse>("/admin/config");
            return data;
        }
    });
}

export function useUpdateConfig() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: { key: string; value: string; description?: string }) => {
            return api.put(`/admin/config/${data.key}`, { value: data.value, description: data.description });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["configs"] });
            toast.success("配置更新成功");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "更新配置失败"));
        }
    });
}

export function useCreateConfig() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: { key: string; value: string; description?: string }) => {
            return api.post("/admin/config", { key: data.key, value: data.value, description: data.description });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["configs"] });
            toast.success("配置创建成功");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "创建配置失败"));
        }
    });
}

export function useDeleteConfig() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (key: string) => {
            return api.delete(`/admin/config/${key}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["configs"] });
            toast.success("配置删除成功");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "删除配置失败"));
        }
    });
}

// --- Table Management ---
interface TableInfo {
    name: string;
    record_count: number;
}

interface TableListResponse {
    tables: TableInfo[];
}

export function useTables() {
    return useQuery({
        queryKey: ["tables"],
        queryFn: async () => {
            const { data } = await api.get<TableListResponse>("/admin/tables");
            return data;
        }
    });
}

interface TableDataResponse {
    table_name: string;
    page: number;
    page_size: number;
    total_records: number;
    total_pages: number;
    records: TableRecord[];
}

export function useTableData(
    tableName: string, 
    params: TableDataParams
) {
    return useQuery({
        queryKey: ["tableData", tableName, params],
        queryFn: async () => {
            const apiParams: Record<string, string | number> = {
                page: params.page || 1,
                page_size: params.page_size || 20,
            };
            if (params.search) apiParams.search = params.search;
            if (params.sort_by) apiParams.sort_by = params.sort_by;
            if (params.sort_order) apiParams.sort_order = params.sort_order;
            if (params.field_search) apiParams.field_search = JSON.stringify(params.field_search);
            
            const { data } = await api.get<TableDataResponse>(`/admin/tables/${tableName}`, { params: apiParams });
            return data;
        },
        enabled: !!tableName
    });
}

export function useCreateTableRecord() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: TableRecordMutationInput) => {
            return api.post(`/admin/tables/${data.tableName}`, { data: data.data });
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["tableData", variables.tableName] });
            queryClient.invalidateQueries({ queryKey: ["tables"] });
            toast.success("Record created successfully");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "Failed to create record"));
        }
    });
}

export function useUpdateTableRecord() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: TableRecordUpdateInput) => {
            return api.put(`/admin/tables/${data.tableName}/${data.recordId}`, { data: data.data });
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["tableData", variables.tableName] });
            toast.success("Record updated successfully");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "Failed to update record"));
        }
    });
}

export function useDeleteTableRecord() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: { tableName: string; recordId: number }) => {
            return api.delete(`/admin/tables/${data.tableName}/${data.recordId}`);
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["tableData", variables.tableName] });
            // Also update table list count implicitly or explicitly
            queryClient.invalidateQueries({ queryKey: ["tables"] });
            toast.success("Record deleted successfully");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "Failed to delete record"));
        }
    });
}

// --- Cache Management ---
interface CacheStatistics {
    db_size_mb: number;
    max_size_mb: number;
    size_usage_percent: number;
    emails_cache: Record<string, unknown>;
    details_cache: Record<string, unknown>;
    hit_rate?: number;
}

export function useCacheStats() {
    return useQuery({
        queryKey: ["cacheStats"],
        queryFn: async () => {
            const { data } = await api.get<CacheStatistics>("/admin/cache/statistics");
            return data;
        }
    });
}

export function useClearAllCache() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async () => {
            return api.delete("/admin/cache");
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["cacheStats"] });
            toast.success("All cache cleared successfully");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "Failed to clear cache"));
        }
    });
}

export function useTriggerLruCleanup() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async () => {
            return api.post("/admin/cache/cleanup");
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["cacheStats"] });
            toast.success("LRU cleanup completed");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "Failed to cleanup cache"));
        }
    });
}

// --- SQL Query Management ---
interface SqlExecuteRequest {
    sql: string;
    max_rows?: number;
}

interface SqlExecuteResponse {
    success: boolean;
    data?: TableRecord[];
    row_count?: number;
    execution_time_ms: number;
    error_message?: string;
}

interface SqlQueryHistoryItem {
    id: number;
    sql_query: string;
    result_count?: number;
    execution_time_ms?: number;
    status: string;
    error_message?: string;
    created_at: string;
    created_by?: string;
}

interface SqlQueryHistoryResponse {
    total: number;
    page: number;
    page_size: number;
    total_pages: number;
    history: SqlQueryHistoryItem[];
}

interface SqlQueryFavoriteItem {
    id: number;
    name: string;
    sql_query: string;
    description?: string;
    created_at: string;
    created_by?: string;
    updated_at: string;
}

interface SqlQueryFavoriteListResponse {
    favorites: SqlQueryFavoriteItem[];
}

export function useExecuteSql() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (request: SqlExecuteRequest) => {
            const { data } = await api.post<SqlExecuteResponse>("/admin/sql/execute", request);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["sqlHistory"] });
            toast.success("SQL执行成功");
        },
        onError: (error: ApiError) => {
            const errorMsg = getMutationErrorMessage(error, "SQL执行失败");
            toast.error(errorMsg);
        }
    });
}

export function useSqlHistory(params: { page?: number; page_size?: number } = {}) {
    return useQuery({
        queryKey: ["sqlHistory", params],
        queryFn: async () => {
            const { data } = await api.get<SqlQueryHistoryResponse>("/admin/sql/history", {
                params: {
                    page: params.page || 1,
                    page_size: params.page_size || 50
                }
            });
            return data;
        }
    });
}

export function useSqlFavorites() {
    return useQuery({
        queryKey: ["sqlFavorites"],
        queryFn: async () => {
            const { data } = await api.get<SqlQueryFavoriteListResponse>("/admin/sql/favorites");
            return data;
        }
    });
}

export function useCreateSqlFavorite() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: { name: string; sql_query: string; description?: string }) => {
            return api.post("/admin/sql/favorites", data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["sqlFavorites"] });
            toast.success("SQL收藏创建成功");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "创建SQL收藏失败"));
        }
    });
}

export function useDeleteSqlFavorite() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (favoriteId: number) => {
            return api.delete(`/admin/sql/favorites/${favoriteId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["sqlFavorites"] });
            toast.success("SQL收藏删除成功");
        },
        onError: (error: ApiError) => {
            toast.error(getMutationErrorMessage(error, "删除SQL收藏失败"));
        }
    });
}

interface VerificationRuleListResponse {
    total: number;
    rules: VerificationRule[];
}

interface VerificationRulePayload {
    name: string;
    scope_type: "targeted" | "global";
    match_mode: "and" | "or";
    priority: number;
    enabled: boolean;
    sender_pattern?: string;
    subject_pattern?: string;
    body_pattern?: string;
    extract_pattern: string;
    is_regex: boolean;
    description?: string;
}

export function useVerificationRules() {
    return useQuery({
        queryKey: ["verificationRules"],
        queryFn: async () => {
            const { data } = await api.get<VerificationRuleListResponse>("/admin/verification-rules");
            return data;
        }
    });
}

export function useCreateVerificationRule() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (payload: VerificationRulePayload) => {
            const { data } = await api.post<VerificationRule>("/admin/verification-rules", payload);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["verificationRules"] });
            toast.success("验证码规则创建成功");
        },
        onError: (error: ApiError) => {
            toast.error(extractApiErrorMessage(error, "验证码规则创建失败"));
        }
    });
}

export function useUpdateVerificationRule() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: { ruleId: number; payload: VerificationRulePayload }) => {
            const response = await api.put<VerificationRule>(`/admin/verification-rules/${data.ruleId}`, data.payload);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["verificationRules"] });
            toast.success("验证码规则更新成功");
        },
        onError: (error: ApiError) => {
            toast.error(extractApiErrorMessage(error, "验证码规则更新失败"));
        }
    });
}

export function useDeleteVerificationRule() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (ruleId: number) => {
            const { data } = await api.delete<{ message: string }>(`/admin/verification-rules/${ruleId}`);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["verificationRules"] });
            toast.success("验证码规则删除成功");
        },
        onError: (error: ApiError) => {
            toast.error(extractApiErrorMessage(error, "验证码规则删除失败"));
        }
    });
}

export function useTestVerificationRule() {
    return useMutation({
        mutationFn: async (payload: { email_account: string; message_id: string; rule_id?: number }) => {
            await api.get(`/emails/${payload.email_account}/${payload.message_id}`);
            const { data } = await api.post<VerificationRuleTestResult>("/admin/verification-rules/test", payload);
            return data;
        },
        onError: (error: ApiError) => {
            toast.error(extractApiErrorMessage(error, "验证码规则测试失败"));
        }
    });
}
