import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { User, ConfigItem } from "@/types";
import { toast } from "sonner";

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
        mutationFn: async (data: any) => {
            return api.post("/admin/users", data);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["users"] });
            toast.success("User created successfully");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to create user");
        }
    });
}

export function useUpdateUser() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: { username: string; update: any }) => {
            return api.put(`/admin/users/${data.username}`, data.update);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["users"] });
            toast.success("User updated successfully");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to update user");
        }
    });
}

export function useUpdateUserPassword() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: { username: string; new_password: string }) => {
            return api.put(`/admin/users/${data.username}/password`, {
                new_password: data.new_password
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["users"] });
            toast.success("密码修改成功");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "修改密码失败");
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
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to delete user");
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
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "更新配置失败");
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
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "创建配置失败");
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
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "删除配置失败");
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
    records: any[];
}

export function useTableData(
    tableName: string, 
    params: { 
        page?: number; 
        page_size?: number; 
        search?: string;
        sort_by?: string;
        sort_order?: "asc" | "desc";
        field_search?: Record<string, string>;
    }
) {
    return useQuery({
        queryKey: ["tableData", tableName, params],
        queryFn: async () => {
            const apiParams: any = {
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
        mutationFn: async (data: { tableName: string; data: any }) => {
            return api.post(`/admin/tables/${data.tableName}`, { data: data.data });
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["tableData", variables.tableName] });
            queryClient.invalidateQueries({ queryKey: ["tables"] });
            toast.success("Record created successfully");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to create record");
        }
    });
}

export function useUpdateTableRecord() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (data: { tableName: string; recordId: number; data: any }) => {
            return api.put(`/admin/tables/${data.tableName}/${data.recordId}`, { data: data.data });
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["tableData", variables.tableName] });
            toast.success("Record updated successfully");
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to update record");
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
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to delete record");
        }
    });
}

// --- Cache Management ---
interface CacheStatistics {
    db_size_mb: number;
    max_size_mb: number;
    size_usage_percent: number;
    emails_cache: any;
    details_cache: any;
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
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to clear cache");
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
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to cleanup cache");
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
    data?: any[];
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
        onError: (error: any) => {
            const errorMsg = error.response?.data?.error_message || error.response?.data?.detail || "SQL执行失败";
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
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "创建SQL收藏失败");
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
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "删除SQL收藏失败");
        }
    });
}
