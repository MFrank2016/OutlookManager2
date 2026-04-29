import { keepPreviousData, useQuery, useMutation, useQueryClient, UseQueryOptions } from "@tanstack/react-query";
import api, { ApiError, extractApiErrorMessage } from "@/lib/api";
import { Account } from "@/types";
import { toast } from "sonner";

interface AccountListResponse {
  total_accounts: number;
  page: number;
  page_size: number;
  total_pages: number;
  accounts: Account[];
}

interface AccountsParams {
  page?: number;
  page_size?: number;
  email_search?: string;
  tag_search?: string;
  include_tags?: string;
  exclude_tags?: string;
  refresh_status?: string;
}

export function useAccounts(
  params: AccountsParams = {},
  options?: Omit<UseQueryOptions<AccountListResponse>, 'queryKey' | 'queryFn'>
) {
  // 使用稳定的 queryKey，避免对象引用变化导致的重复请求
  const queryKey = [
    "accounts",
    params.page || 1,
    params.page_size || 10,
    params.email_search || "",
    params.tag_search || "",
    params.include_tags || "",
    params.exclude_tags || "",
    params.refresh_status || ""
  ];
  
  return useQuery({
    queryKey,
    queryFn: async () => {
      const queryParams = {
        page: params.page || 1,
        page_size: params.page_size || 10,
        email_search: params.email_search || undefined,
        tag_search: params.tag_search || undefined,
        include_tags: params.include_tags || undefined,
        exclude_tags: params.exclude_tags || undefined,
        refresh_status: params.refresh_status === "all" ? undefined : params.refresh_status,
      };

      const { data } = await api.get<AccountListResponse>("/accounts", {
        params: queryParams
      });

      return data;
    },
    placeholderData: keepPreviousData,
    ...options,
  });
}

export function useAddAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { email: string; refresh_token: string; client_id: string; tags: string[] }) => {
      return api.post("/accounts", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      toast.success("账户已添加");
    },
    onError: (error: ApiError) => {
        toast.error(extractApiErrorMessage(error, "添加账户失败"));
    }
  });
}

export function useDeleteAccount() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (email_id: string) => {
      return api.delete(`/accounts/${email_id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      toast.success("账户已删除");
    },
  });
}

export function useUpdateTags() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: { email_id: string; tags: string[] }) => {
      return api.put(`/accounts/${data.email_id}/tags`, { tags: data.tags });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      toast.success("标签已更新");
    },
  });
}

export function useRefreshToken() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (email_id: string) => {
      return api.post(`/accounts/${email_id}/refresh-token`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      toast.success("Token 已刷新");
    },
  });
}

export function useBatchDeleteAccounts() {
    const queryClient = useQueryClient();
    return useMutation({
      mutationFn: async (email_ids: string[]) => {
        return api.post("/accounts/batch-delete", { email_ids });
      },
      onSuccess: (data) => {
        queryClient.invalidateQueries({ queryKey: ["accounts"] });
        toast.success(`批量删除完成：成功 ${data.data.success_count}，失败 ${data.data.failed_count}`);
      },
    });
  }
