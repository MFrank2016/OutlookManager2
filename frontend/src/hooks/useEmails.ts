import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api, { buildV2MessagePath, buildV2MessageQueryParams, buildV2MessagesPath } from "@/lib/api";
import { Email, ProviderOverride, StrategyMode } from "@/types";
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
    refreshNonce?: number; // 手动刷新触发器
    hydrateDetails?: boolean;
    useV2?: boolean;
    overrideProvider?: ProviderOverride;
    strategyMode?: StrategyMode;
    skipCache?: boolean;
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
        params.hydrateDetails ? 1 : 0,
        params.sortBy || "date",
        params.sortOrder || "desc",
        params.refreshNonce || 0,
        params.useV2 ? "v2" : "v1",
        params.overrideProvider || "auto",
        params.strategyMode || "auto",
        params.skipCache ? 1 : 0,
    ];
    
    return useQuery({
        queryKey,
        queryFn: async () => {
            const requestKey = queryKey.join('-');
            
            // 如果已有相同的请求正在进行，等待它完成
            if (pendingRequests.has(requestKey)) {
                return pendingRequests.get(requestKey)!;
            }

            if (!params.account) {
                return null;
            }
            
            // Clean params to remove empty/undefined values
            const folder = (params.folder || "all").toLowerCase();
            const queryParams: Record<string, unknown> = params.useV2
                ? buildV2MessageQueryParams({
                    page: params.page || 1,
                    page_size: params.page_size || 20,
                    folder,
                    hydrate_details: params.hydrateDetails,
                    sort_by: params.sortBy || "date",
                    sort_order: params.sortOrder || "desc",
                    sender_search:
                        params.search && params.searchType === "sender"
                            ? params.search
                            : undefined,
                    subject_search:
                        params.search && params.searchType !== "sender"
                            ? params.search
                            : undefined,
                    override_provider: params.overrideProvider,
                    strategy_mode: params.strategyMode,
                    skip_cache: Boolean(params.skipCache || params.forceRefresh),
                })
                : {
                    page: params.page || 1,
                    page_size: params.page_size || 20,
                    folder,
                    sort_by: params.sortBy || "date",
                    sort_order: params.sortOrder || "desc",
                };

            if (!params.useV2) {
                if (params.forceRefresh) {
                    queryParams.refresh = true;
                }
                if (params.search && params.search.trim() !== "") {
                    if (params.searchType === "sender") {
                        queryParams.sender_search = params.search;
                    } else {
                        queryParams.subject_search = params.search;
                    }
                }
            }
            
            // 创建并存储请求 Promise
            const requestPromise = api.get<EmailListResponse>(
                params.useV2
                    ? buildV2MessagesPath(params.account)
                    : `/emails/${params.account}`,
                {
                params: queryParams
            }).then(response => {
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
        placeholderData: keepPreviousData,
        // 防止重复请求的配置
        staleTime: 15 * 1000,
        refetchOnMount: false, // 挂载时不自动重新请求
        refetchOnWindowFocus: false, // 窗口聚焦时不重新请求
        refetchOnReconnect: false, // 重新连接时不重新请求
        // 使用 gcTime (原 cacheTime) 来控制缓存时间
        gcTime: 5 * 60 * 1000, // 5分钟
        // 防止短时间内的重复请求
        retry: false, // 不自动重试
    });
}

export function useEmailDetail(
    account: string,
    messageId: string,
    options?: {
        enabled?: boolean;
        useV2?: boolean;
        overrideProvider?: ProviderOverride;
        strategyMode?: StrategyMode;
        skipCache?: boolean;
    }
) {
    return useQuery({
        queryKey: [
            "email",
            account,
            messageId,
            options?.useV2 ? "v2" : "v1",
            options?.overrideProvider || "auto",
            options?.strategyMode || "auto",
            options?.skipCache ? 1 : 0,
        ],
        queryFn: async () => {
            const params = options?.useV2
                ? buildV2MessageQueryParams({
                    override_provider: options.overrideProvider,
                    strategy_mode: options.strategyMode,
                    skip_cache: options.skipCache,
                })
                : undefined;
            const { data } = await api.get(
                options?.useV2
                    ? buildV2MessagePath(account, messageId)
                    : `/emails/${account}/${messageId}`,
                { params }
            );
            return data;
        },
        enabled: options?.enabled !== undefined ? options.enabled : (!!account && !!messageId)
    });
}

export function useSendEmail() {
    const queryClient = useQueryClient();
    
    return useMutation({
        mutationFn: async (data: { account: string; to: string; subject: string; body: string }) => {
            // 将纯文本转换为 HTML，保留换行
            const htmlBody = data.body
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/\n/g, '<br>');
            
            const response = await api.post(`/emails/${data.account}/send`, {
                to: data.to,
                subject: data.subject,
                body_text: data.body,
                body_html: `<p>${htmlBody}</p>`
            });
            if (response.data?.success === false) {
                throw new Error(response.data.message || "发送邮件失败");
            }
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["emails"] });
            toast.success("邮件发送成功");
        },
        onError: (error: unknown) => {
            const errorMessage =
                error instanceof Error
                    ? error.message
                    : error && typeof error === 'object' && 'response' in error
                        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || "发送邮件失败"
                        : "发送邮件失败";
            toast.error(errorMessage);
        },
    });
}
