import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Email } from "@/types";
import { toast } from "sonner";

interface EmailListResponse {
    total_emails: number;
    page: number;
    page_size: number;
    total_pages: number;
    emails: Email[];
}

interface EmailsParams {
    account: string;
    page?: number;
    page_size?: number;
    folder?: string;
    search?: string;
    searchType?: "subject" | "sender";
    sortBy?: string;
    sortOrder?: "asc" | "desc";
    forceRefresh?: boolean; // 强制刷新，不走缓存
}

// 请求去重 Map，防止同一时间多次请求同一资源
const pendingRequests = new Map<string, Promise<EmailListResponse | null>>();

export function useEmails(params: EmailsParams) {
    // 使用稳定的 queryKey，避免对象引用变化导致的重复请求
    // forceRefresh 不应该在 queryKey 中，因为它只是控制是否添加 refresh 参数
    const queryKey = [
        "emails",
        params.account,
        params.page || 1,
        params.page_size || 20,
        params.folder || "all",
        params.search || "",
        params.searchType || "subject",
        params.sortBy || "date",
        params.sortOrder || "desc"
    ];
    
    return useQuery({
        queryKey,
        queryFn: async () => {
            const requestKey = queryKey.join('-');
            
            console.log('[useEmails] queryFn 被调用', {
                timestamp: new Date().toISOString(),
                account: params.account,
                queryKey,
                requestKey,
                isPending: pendingRequests.has(requestKey),
                params: {
                    page: params.page || 1,
                    page_size: params.page_size || 20,
                    folder: params.folder || "all",
                    search: params.search,
                    searchType: params.searchType,
                    sortBy: params.sortBy,
                    sortOrder: params.sortOrder,
                    forceRefresh: params.forceRefresh
                },
                stackTrace: new Error().stack
            });
            
            // 如果已有相同的请求正在进行，等待它完成
            if (pendingRequests.has(requestKey)) {
                console.log('[useEmails] 检测到重复请求，等待之前的请求完成', {
                    timestamp: new Date().toISOString(),
                    requestKey
                });
                return pendingRequests.get(requestKey)!;
            }

            if (!params.account) {
                console.log('[useEmails] 账户为空，返回 null');
                return null;
            }
            
            // Clean params to remove empty/undefined values
            const queryParams: Record<string, unknown> = {
                page: params.page || 1,
                page_size: params.page_size || 20,
                folder: params.folder || "all",
                sort_by: params.sortBy || "date",
                sort_order: params.sortOrder || "desc",
            };

            // 如果设置了强制刷新，添加 refresh 参数
            if (params.forceRefresh) {
                queryParams.refresh = true;
            }

            // Handle search types
            if (params.search && params.search.trim() !== "") {
                if (params.searchType === "sender") {
                    queryParams.sender_search = params.search;
                } else {
                    // Default to subject search if not specified or "subject"
                    queryParams.subject_search = params.search;
                }
            }

            // Ensure folder is lowercase as per regex
            if (queryParams.folder && typeof queryParams.folder === 'string') {
                queryParams.folder = queryParams.folder.toLowerCase();
            }

            console.log('[useEmails] 发送 API 请求', {
                timestamp: new Date().toISOString(),
                account: params.account,
                url: `/emails/${params.account}`,
                queryParams
            });

            const startTime = Date.now();
            
            // 创建并存储请求 Promise
            const requestPromise = api.get<EmailListResponse>(`/emails/${params.account}`, {
                params: queryParams
            }).then(response => {
                const duration = Date.now() - startTime;
                console.log('[useEmails] API 请求完成', {
                    timestamp: new Date().toISOString(),
                    account: params.account,
                    requestKey,
                    duration: `${duration}ms`,
                    emailCount: response.data?.emails?.length || 0
                });
                
                // 请求完成后移除
                pendingRequests.delete(requestKey);
                return response.data;
            }).catch(error => {
                // 请求失败也要移除
                pendingRequests.delete(requestKey);
                throw error;
            });
            
            // 存储请求
            pendingRequests.set(requestKey, requestPromise);
            
            return requestPromise;
        },
        enabled: !!params.account,
        // 防止重复请求的配置
        staleTime: 0, // 数据立即过期，允许手动刷新
        refetchOnMount: false, // 挂载时不自动重新请求
        refetchOnWindowFocus: false, // 窗口聚焦时不重新请求
        refetchOnReconnect: false, // 重新连接时不重新请求
        // 使用 gcTime (原 cacheTime) 来控制缓存时间
        gcTime: 5 * 60 * 1000, // 5分钟
        // 防止短时间内的重复请求
        retry: false, // 不自动重试
    });
}

export function useEmailDetail(account: string, messageId: string) {
    return useQuery({
        queryKey: ["email", account, messageId],
        queryFn: async () => {
            const { data } = await api.get(`/emails/${account}/${messageId}`);
            return data;
        },
        enabled: !!account && !!messageId
    });
}

export function useSendEmail() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (data: { account: string; to: string; subject: string; body: string }) => {
            const response = await api.post("/emails/send", data);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["emails"] });
            toast.success("邮件发送成功");
        },
        onError: (error: unknown) => {
            const errorMessage = error && typeof error === 'object' && 'response' in error 
                ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || "发送邮件失败"
                : "发送邮件失败";
            toast.error(errorMessage);
        },
    });
}
