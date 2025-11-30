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
}

export function useEmails(params: EmailsParams) {
    return useQuery({
        queryKey: ["emails", params],
        queryFn: async () => {
            if (!params.account) return null;
            
            // Clean params to remove empty/undefined values
            const queryParams: any = {
                page: params.page || 1,
                page_size: params.page_size || 20,
                folder: params.folder || "all",
                sort_by: params.sortBy || "date",
                sort_order: params.sortOrder || "desc",
            };

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
            if (queryParams.folder) {
                queryParams.folder = queryParams.folder.toLowerCase();
            }

            const { data } = await api.get<EmailListResponse>(`/emails/${params.account}`, {
                params: queryParams
            });
            return data;
        },
        enabled: !!params.account
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
        mutationFn: async (data: { account: string, recipient: string, subject: string, body: string }) => {
             return api.post(`/emails/${data.account}/send`, {
                 to: data.recipient,
                 subject: data.subject,
                 body_text: data.body,
                 body_html: `<p>${data.body}</p>`
             });
        },
        onSuccess: () => {
            toast.success("Email sent successfully");
            queryClient.invalidateQueries({ queryKey: ["emails"] });
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || "Failed to send email");
        }
    })
}
