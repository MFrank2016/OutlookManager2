import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
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
  refresh_status?: string;
}

export function useAccounts(params: AccountsParams = {}) {
  return useQuery({
    queryKey: ["accounts", params],
    queryFn: async () => {
      const { data } = await api.get<AccountListResponse>("/accounts", {
        params: {
            page: params.page || 1,
            page_size: params.page_size || 10,
            email_search: params.email_search || undefined,
            tag_search: params.tag_search || undefined,
            refresh_status: params.refresh_status === "all" ? undefined : params.refresh_status,
        }
      });
      return data;
    },
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
      toast.success("Account added successfully");
    },
    onError: (error: any) => {
        toast.error(error.response?.data?.detail || "Failed to add account");
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
      toast.success("Account deleted successfully");
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
      toast.success("Tags updated successfully");
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
      toast.success("Token refreshed successfully");
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
        toast.success(`Batch delete completed: ${data.data.success_count} success, ${data.data.failed_count} failed`);
      },
    });
  }

