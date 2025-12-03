"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Loader2, Mail, ChevronLeft, ChevronRight, Eye, Copy, Check, Calendar, RefreshCw, Search } from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { useRouter } from "next/navigation";

interface EmailItem {
  message_id: string;
  subject: string;
  from_email: string;
  date: string;
  folder: string;
  sender_initial: string;
}

interface EmailDetail {
  message_id: string;
  subject: string;
  from_email: string;
  to_email: string;
  date: string;
  body_plain?: string;
  body_html?: string;
  verification_code?: string;
}

interface ShareTokenInfo {
  email_account_id: string;
  expiry_time?: string;
  is_active: boolean;
  start_time: string;
  end_time?: string;
  subject_keyword?: string;
  sender_keyword?: string;
}

export default function SharedEmailPage() {
  const params = useParams();
  const router = useRouter();
  const urlToken = params.token as string;
  const [inputToken, setInputToken] = useState<string>(urlToken || "");
  const [page, setPage] = useState(1);
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [emailDetailOpen, setEmailDetailOpen] = useState(false);
  const [viewMode, setViewMode] = useState<"html" | "text">("html");
  const pageSize = 20;
  
  // 使用输入框的token或URL中的token
  const token = inputToken || urlToken;

  // 处理API错误的辅助函数
  const handleApiError = async (response: Response): Promise<never> => {
    if (response.status === 429) {
      const errorData = await response.json().catch(() => ({ detail: "请求过于频繁" }));
      toast.error(errorData.detail || "请求过于频繁，请稍后再试");
      throw new Error(errorData.detail || "请求过于频繁，请稍后再试");
    }
    const errorData = await response.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(errorData.detail || "请求失败");
  };

  // 获取分享码信息
  const { data: tokenInfo, refetch: refetchTokenInfo } = useQuery<ShareTokenInfo>({
    queryKey: ["share-token-info", token],
    queryFn: async () => {
      const response = await fetch(`/share/${token}/info`);
      if (!response.ok) {
        await handleApiError(response);
      }
      return response.json();
    },
    enabled: !!token,
    retry: (failureCount, error) => {
      // 429错误不重试
      if (error instanceof Error && error.message.includes("请求过于频繁")) {
        return false;
      }
      return failureCount < 2;
    },
  });

  // 获取邮件列表
  const { data, isLoading, error, refetch: refetchEmails } = useQuery({
    queryKey: ["shared-emails", token, page],
    queryFn: async () => {
      const response = await fetch(`/share/${token}/emails?page=${page}&page_size=${pageSize}`);
      if (!response.ok) {
        await handleApiError(response);
      }
      return response.json();
    },
    enabled: !!token,
    retry: (failureCount, error) => {
      // 429错误不重试
      if (error instanceof Error && error.message.includes("请求过于频繁")) {
        return false;
      }
      return failureCount < 2;
    },
  });

  // 获取邮件详情
  const { data: emailDetail, isLoading: isDetailLoading, refetch: refetchEmailDetail } = useQuery<EmailDetail>({
    queryKey: ["shared-email-detail", token, selectedEmailId],
    queryFn: async () => {
      if (!selectedEmailId) return null;
      const response = await fetch(`/share/${token}/emails/${selectedEmailId}`);
      if (!response.ok) {
        await handleApiError(response);
      }
      return response.json();
    },
    enabled: !!selectedEmailId && emailDetailOpen,
    retry: (failureCount, error) => {
      // 429错误不重试
      if (error instanceof Error && error.message.includes("请求过于频繁")) {
        return false;
      }
      return failureCount < 2;
    },
  });

  // 手动刷新
  const handleRefresh = async () => {
    try {
      await Promise.all([
        refetchTokenInfo(),
        refetchEmails(),
      ]);
      toast.success("刷新成功");
    } catch (error) {
      // 错误已在handleApiError中处理
    }
  };

  // 查询token
  const handleSearchToken = () => {
    if (!inputToken || inputToken.trim() === "") {
      toast.error("请输入分享码");
      return;
    }
    // 导航到新的token页面
    router.push(`/shared/${inputToken.trim()}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="bg-white rounded-lg shadow-md p-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">访问失败</h1>
            <p className="text-gray-600 mb-6">
              {error instanceof Error ? error.message : "无法加载分享的邮件"}
            </p>
            <p className="text-sm text-gray-500">
              可能的原因：分享链接已过期、无效或已被禁用
            </p>
          </div>
        </div>
      </div>
    );
  }

  const emails: EmailItem[] = data?.emails || [];
  const total = data?.total_emails || 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Token输入框和查询按钮 */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                分享码
              </label>
              <Input
                type="text"
                placeholder="请输入分享码"
                value={inputToken}
                onChange={(e) => setInputToken(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleSearchToken();
                  }
                }}
                className="w-full"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={handleSearchToken}
                disabled={!inputToken || inputToken.trim() === ""}
                className="min-h-[44px]"
              >
                <Search className="h-4 w-4 mr-2" />
                查询
              </Button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">共享邮件</h1>
                <p className="text-sm text-gray-500 mt-1">
                  共 {total} 封邮件
                </p>
                {tokenInfo && (
                  <div className="mt-2 flex items-center gap-4 text-xs text-gray-600">
                    {tokenInfo.expiry_time && (
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>
                          有效期至: {format(new Date(tokenInfo.expiry_time), "yyyy-MM-dd HH:mm")}
                          {new Date(tokenInfo.expiry_time) > new Date() && (
                            <span className="ml-1 text-green-600">
                              ({formatDistanceToNow(new Date(tokenInfo.expiry_time), { addSuffix: true })})
                            </span>
                          )}
                        </span>
                      </div>
                    )}
                    {!tokenInfo.expiry_time && (
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span className="text-green-600">永久有效</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isLoading}
                className="min-h-[44px]"
              >
                <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
                刷新
              </Button>
            </div>
          </div>

          {emails.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">暂无邮件</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead>发件人</TableHead>
                      <TableHead>主题</TableHead>
                      <TableHead>时间</TableHead>
                      <TableHead>文件夹</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {emails.map((email) => (
                      <TableRow 
                        key={email.message_id} 
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => {
                          setSelectedEmailId(email.message_id);
                          setEmailDetailOpen(true);
                        }}
                      >
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-medium">
                              {email.sender_initial}
                            </div>
                            <span className="text-sm">{email.from_email}</span>
                          </div>
                        </TableCell>
                        <TableCell className="font-medium">{email.subject || "(无主题)"}</TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {format(new Date(email.date), "yyyy-MM-dd HH:mm")}
                        </TableCell>
                        <TableCell>
                          <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
                            {email.folder}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    第 {page} 页，共 {totalPages} 页
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4 mr-1" />
                      上一页
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      下一页
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* 邮件详情对话框 */}
      <Dialog open={emailDetailOpen} onOpenChange={setEmailDetailOpen}>
        <DialogContent className="max-w-[95vw] lg:max-w-5xl max-h-[90vh] overflow-hidden flex flex-col w-full">
          <DialogHeader className="pb-4 border-b">
            <DialogTitle className="text-lg font-bold break-words pr-8">
              {emailDetail?.subject || "加载中..."}
            </DialogTitle>
          </DialogHeader>

          {isDetailLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : emailDetail ? (
            <>
              {/* 邮件元数据 */}
              <div className="p-4 space-y-2 border-b">
                <div className="text-sm">
                  <span className="font-medium text-gray-600">发件人: </span>
                  <span className="text-gray-900">{emailDetail.from_email}</span>
                </div>
                <div className="text-sm">
                  <span className="font-medium text-gray-600">收件人: </span>
                  <span className="text-gray-900">{emailDetail.to_email || "无"}</span>
                </div>
                <div className="text-sm">
                  <span className="font-medium text-gray-600">日期: </span>
                  <span className="text-gray-900">
                    {format(new Date(emailDetail.date), "yyyy-MM-dd HH:mm:ss")}
                  </span>
                </div>
                {emailDetail.verification_code && (
                  <div className="text-sm">
                    <span className="font-medium text-gray-600">验证码: </span>
                    <Badge variant="secondary" className="bg-green-100 text-green-800">
                      {emailDetail.verification_code}
                    </Badge>
                  </div>
                )}
              </div>

              {/* 视图切换按钮 */}
              <div className="p-4 border-b flex gap-2 items-center justify-between">
                <div className="flex gap-2">
                  <Button
                    variant={viewMode === "html" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setViewMode("html")}
                    className="h-8"
                  >
                    HTML视图
                  </Button>
                  <Button
                    variant={viewMode === "text" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setViewMode("text")}
                    className="h-8"
                  >
                    纯文本
                  </Button>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => refetchEmailDetail()}
                  disabled={isDetailLoading}
                  className="h-8"
                >
                  <RefreshCw className={cn("h-4 w-4 mr-2", isDetailLoading && "animate-spin")} />
                  刷新
                </Button>
              </div>

              {/* 邮件正文 */}
              <ScrollArea className="flex-1 p-6">
                {viewMode === "html" && emailDetail.body_html ? (
                  <div 
                    className="prose prose-slate max-w-none dark:prose-invert email-content text-sm leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: emailDetail.body_html }} 
                  />
                ) : (
                  <pre className="whitespace-pre-wrap text-sm font-mono bg-gray-50 p-4 rounded">
                    {emailDetail.body_plain || emailDetail.body_html || "无内容"}
                  </pre>
                )}
              </ScrollArea>
            </>
          ) : (
            <div className="p-8 text-center text-gray-500">
              无法加载邮件详情
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
