"use client";

import { useState, useEffect, useRef, useMemo } from "react";
import React from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAccounts } from "@/hooks/useAccounts";
import { useEmails, useEmailDetail } from "@/hooks/useEmails";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { formatDistanceToNow } from "date-fns";
import { cn } from "@/lib/utils";
import { SendEmailDialog } from "@/components/emails/SendEmailDialog";
import { 
    Search, 
    Filter, 
    ArrowUpDown, 
    ChevronLeft, 
    ChevronRight,
    Inbox,
    Trash2,
    Mail,
    Key,
    Copy,
    Check,
    RefreshCw
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { copyToClipboard } from "@/lib/clipboard";
import { useQueryClient } from "@tanstack/react-query";

export default function EmailsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialAccount = searchParams.get("account");

  const [selectedAccount, setSelectedAccount] = useState<string | null>(initialAccount);
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [emailDetailOpen, setEmailDetailOpen] = useState(false);
  
  // Filters
  const [search, setSearch] = useState("");
  const [searchType, setSearchType] = useState<"subject" | "sender">("subject");
  const [folder, setFolder] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // 自动刷新倒计时
  const [refreshCountdown, setRefreshCountdown] = useState(30);
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(true);
  const queryClient = useQueryClient();

  const { data: accountsData } = useAccounts({ page_size: 100 });
  const { data: emailsData, isLoading: isEmailsLoading, refetch: refetchEmails } = useEmails({
    account: selectedAccount || "",
    search,
    searchType,
    folder,
    sortBy,
    sortOrder,
    page,
    page_size: pageSize
  });

  // 使用 ref 存储 refetch 函数，避免重复渲染
  const refetchEmailsRef = useRef(refetchEmails);
  useEffect(() => {
    refetchEmailsRef.current = refetchEmails;
  }, [refetchEmails]);

  // 自动刷新倒计时
  useEffect(() => {
    if (!isAutoRefreshEnabled || !selectedAccount || isEmailsLoading) {
      return;
    }

    const interval = setInterval(() => {
      setRefreshCountdown((prev) => {
        if (prev <= 1) {
          refetchEmailsRef.current().then(() => {
            setRefreshCountdown(30);
          }).catch(() => {
            setRefreshCountdown(30);
          });
          return 30;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isAutoRefreshEnabled, selectedAccount, isEmailsLoading]); // 移除 refetchEmails 依赖

  // 当筛选条件改变时，重置倒计时
  useEffect(() => {
    setRefreshCountdown(30);
  }, [search, folder, sortBy, sortOrder, selectedAccount, page]);

  // 手动刷新
  const handleManualRefresh = async () => {
    setRefreshCountdown(30);
    await refetchEmails();
    toast.success("邮件列表已刷新");
  };

  // Update URL when account changes
  useEffect(() => {
      if (selectedAccount) {
          const currentAccountParam = searchParams.get("account");
          if (currentAccountParam !== selectedAccount) {
              const params = new URLSearchParams(searchParams.toString());
              params.set("account", selectedAccount);
              router.replace(`?${params.toString()}`);
          }
      }
  }, [selectedAccount, router, searchParams]);

  // If no account selected and accounts loaded, select first
  useEffect(() => {
      if (!selectedAccount && accountsData?.accounts?.length && accountsData.accounts.length > 0) {
          const firstAccount = accountsData.accounts[0].email_id;
          if (firstAccount !== selectedAccount) {
             setSelectedAccount(firstAccount);
          }
      }
  }, [accountsData, selectedAccount]);

  // Reset page when filters change
  useEffect(() => {
      setPage(1);
  }, [search, folder, sortBy, sortOrder, selectedAccount]);

  // 复制验证码处理函数
  const handleCopyCode = async (code: string) => {
    const success = await copyToClipboard(code);
    if (success) {
      toast.success("验证码已复制到剪贴板");
    } else {
      toast.error("复制失败，请手动复制");
    }
  };

  return (
    <div className="h-[calc(100vh-100px)] md:h-[calc(100vh-100px)] flex flex-col space-y-4 px-0 md:px-4">
      {/* Top Bar: Account Selection & Filters */}
      <div className="flex flex-col gap-4 bg-white p-4 rounded-lg shadow-sm border">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4">
            <div className="flex-1 sm:w-64 flex items-center gap-2">
                <Select value={selectedAccount || ""} onValueChange={setSelectedAccount}>
                    <SelectTrigger className="flex-1">
                        <SelectValue placeholder="Select Account" />
                    </SelectTrigger>
                    <SelectContent>
                        {accountsData?.accounts.map(acc => (
                            <SelectItem key={acc.email_id} value={acc.email_id}>
                                {acc.email_id}
                            </SelectItem>
                        ))}
                    </SelectContent>
                </Select>
                {selectedAccount && (
                    <Button
                        variant="ghost"
                        size="icon"
                        className="h-9 w-9 min-h-[44px] min-w-[44px] shrink-0"
                        onClick={async () => {
                            const success = await copyToClipboard(selectedAccount);
                            if (success) {
                                toast.success("邮箱地址已复制到剪贴板");
                            } else {
                                toast.error("复制失败");
                            }
                        }}
                        title="复制邮箱地址"
                    >
                        <Copy className="h-4 w-4" />
                    </Button>
                )}
            </div>
            <div className="flex-1 flex flex-col sm:flex-row gap-2">
                <div className="relative flex-1">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                    <Input 
                        placeholder={searchType === "subject" ? "Search subject..." : "Search sender..."}
                        className="pl-9" 
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>
                <Select value={searchType} onValueChange={(v: any) => setSearchType(v)}>
                    <SelectTrigger className="w-full sm:w-[130px]">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="subject">Subject</SelectItem>
                        <SelectItem value="sender">Sender</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <div className="w-full sm:w-auto">
                <SendEmailDialog account={selectedAccount} />
            </div>
        </div>

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 text-sm">
            <div className="flex items-center gap-2">
                <span className="text-muted-foreground hidden sm:inline">Folder:</span>
                <Select value={folder} onValueChange={setFolder}>
                    <SelectTrigger className="w-full sm:w-[140px] h-8">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="all">All Mail</SelectItem>
                        <SelectItem value="inbox">Inbox</SelectItem>
                        <SelectItem value="junk">Junk Email</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            <div className="flex items-center gap-2">
                <span className="text-muted-foreground hidden sm:inline">Sort:</span>
                <Select value={sortBy} onValueChange={setSortBy}>
                    <SelectTrigger className="w-full sm:w-[140px] h-8">
                        <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="date">Date</SelectItem>
                        <SelectItem value="subject">Subject</SelectItem>
                        <SelectItem value="from_email">Sender</SelectItem>
                    </SelectContent>
                </Select>
                <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-8 px-2 min-w-[44px]"
                    onClick={() => setSortOrder(prev => prev === "asc" ? "desc" : "asc")}
                >
                    <ArrowUpDown className={cn("h-4 w-4 sm:mr-1", sortOrder === "asc" && "rotate-180")} />
                    <span className="hidden sm:inline">{sortOrder === "asc" ? "Asc" : "Desc"}</span>
                </Button>
            </div>

            {emailsData && (
                <div className="ml-auto flex items-center gap-2 flex-wrap">
                    <span className="text-muted-foreground text-xs sm:text-sm">
                        <span className="hidden sm:inline">Page </span>{page}<span className="hidden sm:inline"> of {emailsData.total_pages}</span>
                        <span className="hidden md:inline"> ({emailsData.total_emails} total)</span>
                    </span>
                    <div className="flex gap-1">
                        <Button
                            variant="outline"
                            size="icon"
                            className="h-8 w-8 min-w-[44px] min-h-[44px]"
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                        >
                            <ChevronLeft className="h-4 w-4" />
                        </Button>
                        <Button
                            variant="outline"
                            size="icon"
                            className="h-8 w-8 min-w-[44px] min-h-[44px]"
                            onClick={() => setPage(p => Math.min(emailsData.total_pages, p + 1))}
                            disabled={page >= emailsData.total_pages}
                        >
                            <ChevronRight className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            )}
        </div>
      </div>

      <div className="flex-1 flex flex-col lg:flex-row gap-4 min-h-0">
        {/* Email List */}
        <Card className="w-full lg:w-[400px] flex flex-col border-none shadow-md">
            <div className="p-3 border-b bg-slate-50/50 font-medium text-sm text-slate-600 flex justify-between items-center">
                <span>Message List</span>
                <div className="flex items-center gap-2">
                  {isAutoRefreshEnabled && (
                    <span className="text-xs text-slate-500 font-mono">
                      {refreshCountdown}s
                    </span>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0"
                    onClick={handleManualRefresh}
                    disabled={isEmailsLoading}
                    title="刷新邮件列表"
                  >
                    <RefreshCw className={cn("h-3 w-3", isEmailsLoading && "animate-spin")} />
                  </Button>
                </div>
            </div>
            <ScrollArea className="flex-1 bg-white">
                {isEmailsLoading && !emailsData ? (
                    <div className="p-8 text-center text-muted-foreground">Loading emails...</div>
                ) : (
                    <div className="divide-y">
                        {emailsData?.emails.map((email, idx) => (
                            <div 
                                key={email.message_id}
                                onClick={() => {
                                  setSelectedEmailId(email.message_id);
                                  // 只在移动端和中等屏幕显示弹窗，桌面端使用侧边栏
                                  if (typeof window !== 'undefined' && window.innerWidth < 1024) {
                                    setEmailDetailOpen(true);
                                  }
                                }}
                                className={cn(
                                    "p-3 cursor-pointer hover:bg-slate-50 transition-all duration-200 group relative border border-slate-200",
                                    selectedEmailId === email.message_id 
                                        ? "bg-blue-50/80 border-l-4 border-l-blue-600 border-r-2 border-r-blue-400 border-t-2 border-t-blue-400 border-b-2 border-b-blue-400 shadow-md ring-2 ring-blue-200" 
                                        : "border-l-4 border-l-transparent",
                                    idx % 2 === 0 ? "bg-white" : "bg-slate-50/30" // Zebra striping
                                )}
                            >
                                <div className="flex justify-between items-start mb-1 gap-2">
                                    <div className="font-semibold text-sm text-slate-900 truncate flex-1 min-w-0">
                                        {email.from_email}
                                    </div>
                                    <span className="text-[10px] text-slate-400 whitespace-nowrap shrink-0">
                                        {formatDistanceToNow(new Date(email.date), { addSuffix: true })}
                                    </span>
                                </div>
                                
                                <div className="text-xs sm:text-sm font-medium text-slate-700 truncate mb-1.5 flex items-center gap-2 min-w-0">
                                    {email.verification_code ? (
                                        <div className="inline-flex items-center gap-1.5 mr-2 shrink-0">
                                            <span className="inline-flex items-center text-amber-600 text-xs">
                                                <Key className="w-3 h-3 mr-0.5" />
                                                {email.verification_code}
                                            </span>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="h-7 w-7 min-w-[32px] min-h-[32px] p-0 text-amber-600 hover:text-amber-700 hover:bg-amber-50"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleCopyCode(email.verification_code!);
                                                }}
                                                title="复制验证码"
                                            >
                                                <Copy className="w-3 h-3" />
                                            </Button>
                                        </div>
                                    ) : null}
                                    <span className="truncate flex-1 min-w-0">{email.subject}</span>
                                </div>
                                
                                <div className="flex items-center gap-2 mt-1.5">
                                    <Badge variant="secondary" className="text-[9px] px-1.5 py-0 h-4 font-normal">
                                        {email.folder}
                                    </Badge>
                                    {/* Add more badges/flags here if available */}
                                </div>
                            </div>
                        ))}
                        {emailsData?.emails.length === 0 && (
                            <div className="p-12 text-center flex flex-col items-center text-muted-foreground">
                                <Inbox className="h-12 w-12 mb-4 text-slate-200" />
                                <p>No emails found</p>
                            </div>
                        )}
                    </div>
                )}
            </ScrollArea>
        </Card>

        {/* Email Detail - Desktop View (Large screens only) */}
        <Card className="hidden lg:flex flex-1 flex-col border-none shadow-md overflow-hidden">
            {selectedEmailId ? (
                <EmailDetailView account={selectedAccount!} messageId={selectedEmailId} />
            ) : (
                <div className="flex-1 flex flex-col items-center justify-center text-slate-300 bg-slate-50/30">
                    <Mail className="h-16 w-16 mb-4 opacity-20" />
                    <p className="text-lg font-medium text-slate-400">Select an email to read</p>
                </div>
            )}
        </Card>
        
        {/* Mobile/Tablet: Show placeholder when no email selected */}
        <Card className="lg:hidden flex-1 flex-col border-none shadow-md overflow-hidden">
            <div className="flex-1 flex flex-col items-center justify-center text-slate-300 bg-slate-50/30">
                <Mail className="h-16 w-16 mb-4 opacity-20" />
                <p className="text-lg font-medium text-slate-400">点击邮件查看详情</p>
            </div>
        </Card>
      </div>

      {/* Email Detail - Modal Dialog (Mobile & Tablet, also available on Desktop) */}
      <Dialog open={emailDetailOpen} onOpenChange={(open) => {
        setEmailDetailOpen(open);
        // 关闭弹窗时不清除选中的邮件ID，这样桌面端可以继续在侧边栏查看
      }}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col w-[95vw] lg:w-auto">
          {selectedEmailId && (
            <EmailDetailModalView 
              account={selectedAccount!} 
              messageId={selectedEmailId}
              onClose={() => setEmailDetailOpen(false)}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// 倒计时显示组件，使用 React.memo 避免不必要的重新渲染
const CountdownDisplay = React.memo(({ countdown }: { countdown: number }) => (
    <span className="text-xs text-gray-500 font-mono">
        {countdown}s
    </span>
));
CountdownDisplay.displayName = "CountdownDisplay";

// 邮件内容组件，使用 React.memo 完全隔离，避免倒计时更新导致重新渲染
const EmailContent = React.memo(({ 
    content, 
    viewMode, 
    contentKey 
}: { 
    content: string; 
    viewMode: "html" | "text" | "source";
    contentKey: string;
}) => {
    if (viewMode === "html") {
        return (
            <div 
                key={contentKey}
                className="prose prose-slate max-w-none dark:prose-invert email-content text-sm leading-relaxed"
                dangerouslySetInnerHTML={{ __html: content }} 
            />
        );
    }
    return (
        <pre key={contentKey} className="whitespace-pre-wrap text-sm font-mono bg-gray-50 p-4 rounded">
            {content}
        </pre>
    );
});
EmailContent.displayName = "EmailContent";

function EmailDetailModalView({ account, messageId, onClose }: { account: string, messageId: string, onClose: () => void }) {
    const { data: email, isLoading, error, refetch, isRefetching } = useEmailDetail(account, messageId);
    const [copied, setCopied] = useState(false);
    const [viewMode, setViewMode] = useState<"html" | "text" | "source">("html");
    const [refreshCountdown, setRefreshCountdown] = useState(30);
    const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(true);
    
    // 存储邮件内容，只在 messageId 或 viewMode 变化时更新，避免自动刷新时重新渲染
    const [stableEmailBody, setStableEmailBody] = useState<string>("");
    const [stableEmailBodyKey, setStableEmailBodyKey] = useState<string>("");
    
    // 使用 ref 存储倒计时，避免状态更新导致组件重新渲染
    const countdownRef = useRef(30);

    // 使用 ref 存储 refetch 函数，避免重复渲染
    const refetchRef = useRef(refetch);
    useEffect(() => {
        refetchRef.current = refetch;
    }, [refetch]);

    // 当切换邮件或视图模式时，更新稳定的邮件内容
    useEffect(() => {
        if (email) {
            const currentKey = `${messageId}-${viewMode}`;
            if (currentKey !== stableEmailBodyKey) {
                let body = "";
                switch (viewMode) {
                    case "html":
                        body = email.body_html || email.body_plain || "";
                        break;
                    case "text":
                        body = email.body_plain || "";
                        break;
                    case "source":
                        body = email.body_html || email.body_plain || "";
                        break;
                    default:
                        body = email.body_html || email.body_plain || "";
                }
                setStableEmailBody(body);
                setStableEmailBodyKey(currentKey);
                countdownRef.current = 30;
                setRefreshCountdown(30);
            }
        }
    }, [messageId, viewMode, email, stableEmailBodyKey]);

    // 当切换邮件时，重置倒计时
    useEffect(() => {
        countdownRef.current = 30;
        setRefreshCountdown(30);
    }, [messageId]);

    // 自动刷新倒计时 - 使用 ref 存储倒计时值，只在需要显示时更新状态
    useEffect(() => {
        // 只有在邮件加载完成且不是加载状态时才启动倒计时
        if (!isAutoRefreshEnabled || isLoading || !email) {
            return;
        }

        const interval = setInterval(() => {
            countdownRef.current -= 1;
            
            if (countdownRef.current <= 0) {
                // 倒计时结束，自动刷新
                refetchRef.current().then(() => {
                    countdownRef.current = 30;
                    setRefreshCountdown(30);
                }).catch(() => {
                    countdownRef.current = 30;
                    setRefreshCountdown(30);
                });
            } else {
                // 只在倒计时变化时更新显示，减少重新渲染
                // 每5秒更新一次显示，或者当倒计时小于10秒时每秒更新
                if (countdownRef.current % 5 === 0 || countdownRef.current <= 10) {
                    setRefreshCountdown(countdownRef.current);
                }
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [isAutoRefreshEnabled, isLoading, messageId]); // 只依赖必要的值，email 通过 isLoading 间接控制

    const handleManualRefresh = async () => {
        countdownRef.current = 30;
        setRefreshCountdown(30);
        await refetch();
        toast.success("邮件已刷新");
    };

    if (isLoading && !email) return (
      <DialogHeader>
        <DialogTitle>加载中...</DialogTitle>
      </DialogHeader>
    );
    if (error) return (
      <DialogHeader>
        <DialogTitle>加载失败</DialogTitle>
      </DialogHeader>
    );
    if (!email) return (
      <DialogHeader>
        <DialogTitle>邮件未找到</DialogTitle>
      </DialogHeader>
    );

    const handleCopyCode = async (code: string) => {
        const success = await copyToClipboard(code);
        if (success) {
            setCopied(true);
            toast.success("验证码已复制到剪贴板");
            setTimeout(() => setCopied(false), 2000);
        } else {
            toast.error("复制失败，请手动复制");
        }
    };

    // 使用稳定的邮件内容，避免自动刷新时重新渲染导致图片闪烁
    // emailContentKey 用于稳定组件，只在 messageId 或 viewMode 变化时重新渲染
    const emailContentKey = `${messageId}-${viewMode}`;

    return (
        <>
            <DialogHeader className="pb-4 border-b">
                <DialogTitle className="text-lg font-bold break-words pr-8">
                    {email.subject}
                </DialogTitle>
            </DialogHeader>

            <div className="flex-1 overflow-y-auto">
                {/* 邮件元数据 */}
                <div className="p-4 space-y-2 border-b">
                    <div className="text-sm">
                        <span className="font-medium text-gray-600">发件人: </span>
                        <span className="text-gray-900">{email.from_email}</span>
                    </div>
                    <div className="text-sm">
                        <span className="font-medium text-gray-600">收件人: </span>
                        <span className="text-gray-900">{email.to_email || "无"}</span>
                    </div>
                    <div className="text-sm">
                        <span className="font-medium text-gray-600">日期: </span>
                        <span className="text-gray-900">
                            {new Date(email.date).toLocaleString('zh-CN', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit'
                            })} ({new Date(email.date).toLocaleString()})
                        </span>
                    </div>
                    <div className="text-sm">
                        <span className="font-medium text-gray-600">邮件ID: </span>
                        <span className="text-gray-900 font-mono text-xs">{email.message_id}</span>
                    </div>
                </div>

                {/* 视图切换按钮 */}
                <div className="p-4 border-b flex gap-2">
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
                    <Button
                        variant={viewMode === "source" ? "default" : "outline"}
                        size="sm"
                        onClick={() => setViewMode("source")}
                        className="h-8"
                    >
                        源码
                    </Button>
                    <div className="ml-auto flex items-center gap-2">
                        {isAutoRefreshEnabled && (
                            <CountdownDisplay countdown={refreshCountdown} />
                        )}
                        <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={handleManualRefresh}
                            disabled={isRefetching}
                            title="刷新邮件"
                        >
                            <RefreshCw className={cn("h-4 w-4", isRefetching && "animate-spin")} />
                        </Button>
                    </div>
                </div>

                {/* 验证码显示 */}
                {email.verification_code && (
                    <div className="p-4 bg-green-50 border-b border-green-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <span className="font-medium text-green-800">🔑 检测到验证码: </span>
                                <code className="bg-white px-2 py-1 rounded text-green-900 font-bold text-base">
                                    {email.verification_code}
                                </code>
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                className="text-green-700 border-green-300 hover:bg-green-100"
                                onClick={() => handleCopyCode(email.verification_code!)}
                            >
                                {copied ? (
                                    <>
                                        <Check className="w-4 h-4 mr-1" />
                                        已复制
                                    </>
                                ) : (
                                    <>
                                        <Copy className="w-4 h-4 mr-1" />
                                        复制
                                    </>
                                )}
                            </Button>
                        </div>
                    </div>
                )}

                {/* 邮件正文 - 使用独立的 memo 组件，完全隔离倒计时更新 */}
                <ScrollArea className="flex-1 p-6">
                    <EmailContent 
                        content={stableEmailBody}
                        viewMode={viewMode}
                        contentKey={emailContentKey}
                    />
                </ScrollArea>
            </div>
        </>
    );
}

function EmailDetailView({ account, messageId }: { account: string, messageId: string }) {
    const { data: email, isLoading, error, refetch, isRefetching } = useEmailDetail(account, messageId);
    const [copied, setCopied] = useState(false);
    const [refreshCountdown, setRefreshCountdown] = useState(30); // 30秒自动刷新
    const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(true);
    
    // 存储邮件内容，只在 messageId 变化时更新，避免自动刷新时重新渲染
    const [stableEmailBody, setStableEmailBody] = useState<string>("");
    const [stableMessageId, setStableMessageId] = useState<string>("");
    
    // 使用 ref 存储倒计时，避免状态更新导致组件重新渲染
    const countdownRef = useRef(30);

    // 使用 ref 存储 refetch 函数，避免重复渲染
    const refetchRef = useRef(refetch);
    useEffect(() => {
        refetchRef.current = refetch;
    }, [refetch]);

    // 当切换邮件时，更新稳定的邮件内容并重置倒计时
    useEffect(() => {
        if (email && messageId !== stableMessageId) {
            setStableEmailBody(email.body_html || email.body_plain || "");
            setStableMessageId(messageId);
            countdownRef.current = 30;
            setRefreshCountdown(30);
        }
    }, [messageId, email, stableMessageId]);

    // 自动刷新倒计时 - 使用 ref 存储倒计时值，只在需要显示时更新状态
    useEffect(() => {
        // 只有在邮件加载完成且不是加载状态时才启动倒计时
        if (!isAutoRefreshEnabled || isLoading || !email) {
            // 如果禁用自动刷新或正在加载或没有邮件数据，停止倒计时
            return;
        }

        const interval = setInterval(() => {
            countdownRef.current -= 1;
            
            if (countdownRef.current <= 0) {
                // 倒计时结束，自动刷新
                refetchRef.current().then(() => {
                    countdownRef.current = 30;
                    setRefreshCountdown(30);
                }).catch(() => {
                    countdownRef.current = 30;
                    setRefreshCountdown(30);
                });
            } else {
                // 只在倒计时变化时更新显示，减少重新渲染
                // 每5秒更新一次显示，或者当倒计时小于10秒时每秒更新
                if (countdownRef.current % 5 === 0 || countdownRef.current <= 10) {
                    setRefreshCountdown(countdownRef.current);
                }
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [isAutoRefreshEnabled, isLoading, messageId]); // 只依赖必要的值，email 通过 isLoading 间接控制

    // 手动刷新时重置倒计时
    const handleManualRefresh = async () => {
        countdownRef.current = 30;
        setRefreshCountdown(30);
        await refetch();
        toast.success("邮件已刷新");
    };

    if (isLoading && !email) return <div className="flex-1 flex items-center justify-center text-muted-foreground">Loading content...</div>;
    if (error) return <div className="flex-1 flex items-center justify-center text-red-500">Failed to load email</div>;
    if (!email) return <div className="flex-1 flex items-center justify-center text-muted-foreground">Email not found</div>;

    const handleCopyCode = async (code: string) => {
        const success = await copyToClipboard(code);
        if (success) {
            setCopied(true);
            toast.success("验证码已复制到剪贴板");
            setTimeout(() => setCopied(false), 2000);
        } else {
            toast.error("复制失败，请手动复制");
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
            <div className="p-4 sm:p-6 border-b bg-slate-50/30">
                <div className="flex flex-col gap-3 sm:gap-4 mb-3 sm:mb-4">
                    <div className="flex flex-col sm:flex-row justify-between items-start gap-3 sm:gap-4">
                        <div className="flex-1 flex items-start gap-2 min-w-0">
                            <h2 className="text-base sm:text-lg md:text-xl font-bold text-slate-900 leading-tight flex-1 break-words">{email.subject}</h2>
                            <div className="flex items-center gap-2 shrink-0">
                                {isAutoRefreshEnabled && (
                                    <CountdownDisplay countdown={refreshCountdown} />
                                )}
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-8 w-8 min-h-[44px] min-w-[44px] p-0"
                                    onClick={handleManualRefresh}
                                    disabled={isRefetching}
                                    title="刷新邮件"
                                >
                                    <RefreshCw className={cn("h-4 w-4", isRefetching && "animate-spin")} />
                                </Button>
                            </div>
                        </div>
                        {email.verification_code && (
                            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 shrink-0 w-full sm:w-auto">
                                <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100 border-amber-200 text-xs sm:text-sm md:text-base px-2 sm:px-3 py-1 sm:py-1.5 text-center">
                                    Code: {email.verification_code}
                                </Badge>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    className="h-9 sm:h-10 px-2 sm:px-3 min-h-[44px] text-amber-700 border-amber-300 hover:bg-amber-50 w-full sm:w-auto"
                                    onClick={() => handleCopyCode(email.verification_code!)}
                                    title="复制验证码"
                                >
                                    {copied ? (
                                        <>
                                            <Check className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-1.5" />
                                            <span className="text-xs sm:text-sm">已复制</span>
                                        </>
                                    ) : (
                                        <>
                                            <Copy className="w-3 h-3 sm:w-4 sm:h-4 mr-1 sm:mr-1.5" />
                                            <span className="text-xs sm:text-sm">复制</span>
                                        </>
                                    )}
                                </Button>
                            </div>
                        )}
                    </div>
                    
                    <div className="flex flex-col gap-2 sm:gap-3">
                        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-2 sm:gap-3">
                            <div className="space-y-1.5 sm:space-y-1 flex-1 w-full">
                                <div className="flex items-start sm:items-center gap-2 text-xs sm:text-sm text-slate-600">
                                    <span className="font-medium text-slate-500 w-10 sm:w-12 shrink-0">From:</span> 
                                    <span className="font-semibold text-slate-900 break-all break-words">{email.from_email}</span>
                                </div>
                                <div className="flex items-start sm:items-center gap-2 text-xs sm:text-sm text-slate-600">
                                    <span className="font-medium text-slate-500 w-10 sm:w-12 shrink-0">To:</span> 
                                    <span className="break-all break-words">{email.to_email}</span>
                                </div>
                            </div>
                            <div className="text-[10px] sm:text-xs text-slate-400 shrink-0 self-start sm:self-end">
                                {new Date(email.date).toLocaleString(undefined, { 
                                    dateStyle: 'medium', 
                                    timeStyle: 'short' 
                                })}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <ScrollArea className="flex-1 p-3 sm:p-4 md:p-6 lg:p-8">
                <EmailContent 
                    content={stableEmailBody}
                    viewMode="html"
                    contentKey={messageId}
                />
            </ScrollArea>
        </div>
    );
}
