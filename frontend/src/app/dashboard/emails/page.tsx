"use client";

import { useState, useEffect, useRef } from "react";
import React from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { useAccounts } from "@/hooks/useAccounts";
import { useEmails, useEmailDetail } from "@/hooks/useEmails";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { SendEmailDialog } from "@/components/emails/SendEmailDialog";
import { 
    Search, 
    ArrowUpDown, 
    ChevronLeft, 
    ChevronRight,
    Inbox,
    Trash2,
    Copy,
    Check,
    RefreshCw,
    Trash,
    Eye
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { Email } from "@/types";
import { copyToClipboard } from "@/lib/clipboard";
import { useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

export default function EmailsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialAccount = searchParams.get("account");

  console.log('[EmailsPage] 组件渲染', {
    timestamp: new Date().toISOString(),
    initialAccount
  });

  const [selectedAccount, setSelectedAccount] = useState<string | null>(initialAccount);
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [emailDetailOpen, setEmailDetailOpen] = useState(false);
  const [deleteEmailId, setDeleteEmailId] = useState<string | null>(null);
  const [clearInboxOpen, setClearInboxOpen] = useState(false);
  
  // Filters
  const [search, setSearch] = useState("");
  const [searchType, setSearchType] = useState<"subject" | "sender">("subject");
  const [folder, setFolder] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [jumpPage, setJumpPage] = useState("");

  // 自动刷新配置
  const [isAutoRefreshEnabled] = useState(true);
  const queryClient = useQueryClient();

  const { data: accountsData } = useAccounts({ page_size: 100 });
  console.log('[EmailsPage] 调用 useEmails', {
    timestamp: new Date().toISOString(),
    account: selectedAccount || "",
    search,
    folder,
    page
  });

  const { data: emailsData, isLoading: isEmailsLoading, refetch: refetchEmails } = useEmails({
    account: selectedAccount || "",
    search,
    searchType,
    folder,
    sortBy,
    sortOrder,
    page,
    page_size: pageSize,
    forceRefresh: true // 邮件列表页始终从微软服务器获取最新数据
  });

  // 使用 ref 跟踪上一次更新的账户，避免循环更新
  const lastUpdatedAccountRef = useRef<string | null>(null);

  // 使用 useAutoRefresh Hook 进行自动刷新
  const { countdown: refreshCountdown } = useAutoRefresh({
    enabled: isAutoRefreshEnabled && !!selectedAccount,
    intervalSeconds: 30,
    onRefresh: async () => {
      await refetchEmails();
    },
    isLoading: isEmailsLoading,
  });

  // 手动刷新
  const handleManualRefresh = async () => {
    await refetchEmails();
    toast.success("邮件列表已刷新");
  };

  const handlePageSizeChange = (newPageSize: string) => {
    const size = parseInt(newPageSize);
    setPageSize(size);
    setPage(1);
  };

  const handleJumpPage = () => {
      const pageNum = parseInt(jumpPage);
      if (!emailsData) return;
      
      if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= emailsData.total_pages) {
          setPage(pageNum);
          setJumpPage("");
      } else {
          toast.error(`请输入有效的页码 (1-${emailsData.total_pages})`);
      }
  };

  // 从 URL 同步账户选择（处理浏览器前进/后退或直接修改 URL）
  useEffect(() => {
      const urlAccount = searchParams.get("account");
      console.log('[EmailsPage] URL同步useEffect触发', {
        timestamp: new Date().toISOString(),
        urlAccount,
        selectedAccount,
        lastUpdated: lastUpdatedAccountRef.current
      });
      
      if (urlAccount && urlAccount !== selectedAccount) {
          // 验证账户是否存在
          if (accountsData?.accounts?.some(acc => acc.email_id === urlAccount)) {
              // 只有当URL账户与ref不同时才更新（说明是外部URL变化）
              if (urlAccount !== lastUpdatedAccountRef.current) {
                  console.log('[EmailsPage] 从URL设置账户', { urlAccount });
                  lastUpdatedAccountRef.current = urlAccount;
                  setSelectedAccount(urlAccount);
              }
          }
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, accountsData]);

  // Update URL when account changes (避免循环更新)
  useEffect(() => {
      console.log('[EmailsPage] URL更新useEffect触发', {
        timestamp: new Date().toISOString(),
        selectedAccount,
        lastUpdated: lastUpdatedAccountRef.current,
        urlAccount: searchParams.get("account")
      });
      
      if (selectedAccount) {
          const currentAccountParam = searchParams.get("account");
          // 只有当选中的账户与URL不同，且不是由URL触发的变化时，才更新URL
          if (currentAccountParam !== selectedAccount && lastUpdatedAccountRef.current !== selectedAccount) {
              console.log('[EmailsPage] 更新URL为选中账户', { selectedAccount });
              lastUpdatedAccountRef.current = selectedAccount;
              const params = new URLSearchParams(searchParams.toString());
              params.set("account", selectedAccount);
              router.replace(`?${params.toString()}`);
          } else if (currentAccountParam === selectedAccount && lastUpdatedAccountRef.current !== selectedAccount) {
              // URL 已经匹配，只需更新 ref
              console.log('[EmailsPage] URL已匹配，更新ref', { selectedAccount });
              lastUpdatedAccountRef.current = selectedAccount;
          }
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAccount, router]);

  // If no account selected and accounts loaded, select first
  useEffect(() => {
      console.log('[EmailsPage] 默认账户useEffect触发', {
        timestamp: new Date().toISOString(),
        selectedAccount,
        hasAccounts: !!accountsData?.accounts?.length
      });
      
      if (!selectedAccount && accountsData?.accounts?.length && accountsData.accounts.length > 0) {
          const firstAccount = accountsData.accounts[0].email_id;
          console.log('[EmailsPage] 设置第一个账户', { firstAccount });
          setSelectedAccount(firstAccount);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountsData]);

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

  // 删除邮件
  const handleDeleteEmail = async (messageId: string) => {
    if (!selectedAccount) return;
    
    try {
      await api.delete(`/emails/${selectedAccount}/${messageId}`);
      toast.success("邮件已删除");
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      if (selectedEmailId === messageId) {
        setSelectedEmailId(null);
        setEmailDetailOpen(false);
      }
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error 
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || "删除邮件失败"
        : "删除邮件失败";
      toast.error(errorMessage);
    }
  };

  // 清空当前文件夹
  const handleClearFolder = async () => {
    if (!selectedAccount) return;
    
    const targetFolder = folder === "all" ? "inbox" : folder;
    
    try {
      interface EmailItem {
        message_id: string;
      }
      let allFolderEmails: EmailItem[] = [];
      let currentPage = 1;
      let hasMore = true;
      
      while (hasMore) {
        try {
          const response = await api.get(`/emails/${selectedAccount}`, {
            params: {
              folder: targetFolder,
              page: currentPage,
              page_size: 100,
            }
          });
          const pageEmails = response.data.emails || [];
          allFolderEmails = [...allFolderEmails, ...pageEmails];
          
          if (currentPage >= response.data.total_pages) {
            hasMore = false;
          } else {
            currentPage++;
          }
        } catch {
          hasMore = false;
        }
      }
      
      if (allFolderEmails.length === 0) {
        toast.info(`${targetFolder === "inbox" ? "收件箱" : targetFolder === "junk" ? "垃圾箱" : "文件夹"}已经是空的`);
        return;
      }

      let successCount = 0;
      let failCount = 0;
      
      toast.info(`开始删除 ${allFolderEmails.length} 封邮件...`);
      
      for (const email of allFolderEmails) {
        try {
          await api.delete(`/emails/${selectedAccount}/${email.message_id}`);
          successCount++;
        } catch {
          failCount++;
        }
      }

      const folderName = targetFolder === "inbox" ? "收件箱" : targetFolder === "junk" ? "垃圾箱" : "文件夹";
      toast.success(`清空${folderName}完成！成功删除 ${successCount} 封邮件${failCount > 0 ? `，失败 ${failCount} 封` : ""}`);
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      setSelectedEmailId(null);
      setEmailDetailOpen(false);
    } catch (error: unknown) {
      const errorMessage = error && typeof error === 'object' && 'response' in error 
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail || "清空失败"
        : "清空失败";
      toast.error(errorMessage);
    }
  };

  const openEmailDetail = (messageId: string) => {
    setSelectedEmailId(messageId);
    setEmailDetailOpen(true);
  };

  return (
    <div className="h-[calc(100vh-100px)] md:h-[calc(100vh-100px)] flex flex-col space-y-2 md:space-y-4 px-0 md:px-4">
      {/* Top Bar: Account Selection & Filters */}
      <div className="flex flex-col gap-2 bg-white p-3 md:p-4 rounded-lg shadow-sm border">
        {/* 第一行：账户选择 */}
        <div className="flex items-center gap-2">
            <Select value={selectedAccount || ""} onValueChange={setSelectedAccount}>
                <SelectTrigger className="flex-1 h-9">
                    <SelectValue placeholder="选择账户" />
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
                    className="h-9 w-9 shrink-0"
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

        {/* 第二行：搜索框（2:1） */}
        <div className="flex items-center gap-2">
            <div className="relative flex-[2]">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                <Input 
                    placeholder={searchType === "subject" ? "搜索主题..." : "搜索发件人..."}
                    className="pl-9 h-9" 
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
            </div>
            <Select value={searchType} onValueChange={(v: "subject" | "sender") => setSearchType(v)}>
                <SelectTrigger className="flex-1 h-9">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="subject">主题</SelectItem>
                    <SelectItem value="sender">发件人</SelectItem>
                </SelectContent>
            </Select>
        </div>

        {/* 第三行：文件夹 + 日期 */}
        <div className="flex items-center gap-2">
            <Select value={folder} onValueChange={setFolder}>
                <SelectTrigger className="flex-1 h-9 text-xs md:text-sm">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">全部邮件</SelectItem>
                    <SelectItem value="inbox">收件箱</SelectItem>
                    <SelectItem value="junk">垃圾邮件</SelectItem>
                </SelectContent>
            </Select>
            <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger className="flex-1 h-9 text-xs md:text-sm">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="date">日期</SelectItem>
                    <SelectItem value="subject">主题</SelectItem>
                    <SelectItem value="from_email">发件人</SelectItem>
                </SelectContent>
            </Select>
        </div>

        {/* 第四行：排序按钮 + 倒计时 + 撰写 + 清空 + 刷新 */}
        <div className="flex items-center gap-2">
            <Button 
                variant="ghost" 
                size="sm" 
                className="h-8 px-2"
                onClick={() => setSortOrder(prev => prev === "asc" ? "desc" : "asc")}
            >
                <ArrowUpDown className={cn("h-4 w-4 mr-1", sortOrder === "asc" && "rotate-180")} />
                <span className="text-xs md:text-sm">{sortOrder === "asc" ? "升序" : "降序"}</span>
            </Button>
            {isAutoRefreshEnabled && (
                <span className="text-xs text-slate-500 font-mono">
                    {refreshCountdown}s
                </span>
            )}
            <div className="ml-auto flex items-center gap-1.5">
                <SendEmailDialog account={selectedAccount} />
                {selectedAccount && (folder === "inbox" || folder === "junk" || folder === "all") && (
                    <Button
                        variant="outline"
                        size="sm"
                        className="h-8 px-2 text-xs text-red-600 hover:text-red-700 hover:bg-red-50 border-red-300"
                        onClick={() => setClearInboxOpen(true)}
                        title={folder === "inbox" ? "清空收件箱" : folder === "junk" ? "清空垃圾箱" : "清空收件箱"}
                    >
                        <Trash2 className="h-3.5 w-3.5 mr-1" />
                        <span className="hidden sm:inline">清空</span>
                    </Button>
                )}
                <Button
                    variant="outline"
                    size="sm"
                    className="h-8 px-2"
                    onClick={handleManualRefresh}
                    disabled={isEmailsLoading}
                    title="刷新邮件列表"
                >
                    <RefreshCw className={cn("h-4 w-4 mr-1", isEmailsLoading && "animate-spin")} />
                    <span className="hidden sm:inline text-xs md:text-sm">刷新</span>
                </Button>
            </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col min-h-0 bg-white rounded-lg shadow-sm border overflow-hidden mb-2 md:mb-4">
        {isEmailsLoading && !emailsData ? (
            <div className="p-8 text-center text-muted-foreground">加载邮件中...</div>
        ) : emailsData?.emails.length === 0 ? (
            <div className="p-12 text-center flex flex-col items-center text-muted-foreground">
                <Inbox className="h-12 w-12 mb-4 text-slate-200" />
                <p>未找到邮件</p>
            </div>
        ) : (
            <>
                {/* Desktop Table View */}
                <div className="hidden md:block overflow-auto">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-[250px]">发件人</TableHead>
                                <TableHead>主题</TableHead>
                                <TableHead className="w-[180px]">日期</TableHead>
                                <TableHead className="w-[100px] text-right">操作</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {emailsData?.emails.map((email: Email) => (
                                <TableRow 
                                    key={email.message_id}
                                    className="cursor-pointer hover:bg-slate-50"
                                    onClick={() => openEmailDetail(email.message_id)}
                                >
                                    <TableCell className="font-medium">
                                        <div className="flex items-center gap-2">
                                            <Avatar className="h-8 w-8">
                                                <AvatarFallback className="bg-blue-100 text-blue-700 text-xs">
                                                    {email.sender_initial}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div className="truncate" title={email.from_email}>
                                                {email.from_email.split('<')[0].trim() || email.from_email}
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell>
                                        <div className="flex flex-col">
                                            <div className="font-medium truncate flex items-center gap-2">
                                                {email.verification_code && (
                                                    <Badge variant="secondary" className="bg-amber-100 text-amber-800 text-[10px] px-1 py-0 h-4">
                                                        验证码: {email.verification_code}
                                                    </Badge>
                                                )}
                                                {email.subject}
                                            </div>
                                            <div className="text-xs text-slate-500 truncate max-w-[500px]">
                                                {email.body_preview || "无预览"}
                                            </div>
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-slate-500 text-sm">
                                        {new Date(email.date).toLocaleString('zh-CN', {
                                            year: 'numeric',
                                            month: '2-digit',
                                            day: '2-digit',
                                            hour: '2-digit',
                                            minute: '2-digit'
                                        })}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex justify-end gap-1">
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    openEmailDetail(email.message_id);
                                                }}
                                                title="查看"
                                            >
                                                <Eye className="h-4 w-4" />
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    setDeleteEmailId(email.message_id);
                                                }}
                                                title="删除"
                                            >
                                                <Trash className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </div>

                {/* Mobile Card View */}
                <div className="md:hidden flex flex-col p-3 gap-3 overflow-y-auto bg-gray-50">
                    {emailsData?.emails.map((email: Email) => {
                        // 解析发件人名称和邮箱
                        let senderName = email.from_email;
                        let senderEmail = "";
                        if (email.from_email.includes("<")) {
                            const parts = email.from_email.split("<");
                            senderName = parts[0].trim().replace(/^['"]+|['"]+$/g, '');
                            senderEmail = parts[1].replace(">", "").trim();
                        }

                        return (
                            <div 
                                key={email.message_id}
                                className="bg-white border border-gray-200 rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200"
                                onClick={() => openEmailDetail(email.message_id)}
                            >
                                {/* 卡片内容 */}
                                <div className="p-4 flex flex-col gap-3 w-full">
                                    {/* 头部：头像 + 发件人 + 时间 */}
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="flex items-center gap-2.5 flex-1 min-w-0">
                                            <Avatar className="h-10 w-10 shrink-0">
                                                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white text-sm font-semibold">
                                                    {email.sender_initial}
                                                </AvatarFallback>
                                            </Avatar>
                                            <div className="flex-1 min-w-0">
                                                <div className="font-semibold text-sm text-gray-900 truncate">
                                                    {senderName}
                                                </div>
                                                {senderEmail && (
                                                    <div className="text-xs text-gray-500 truncate">
                                                        {senderEmail}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-xs text-gray-500 whitespace-nowrap shrink-0 mt-0.5">
                                            {new Date(email.date).toLocaleString('zh-CN', {
                                                month: '2-digit',
                                                day: '2-digit',
                                                hour: '2-digit',
                                                minute: '2-digit'
                                            })}
                                        </div>
                                    </div>

                                    {/* 主题与预览 */}
                                    <div className="flex flex-col gap-2">
                                        {/* 主题 */}
                                        <div className="flex items-start gap-2">
                                            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></div>
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-semibold text-gray-900 line-clamp-2 break-words leading-relaxed">
                                                    {email.subject}
                                                </div>
                                            </div>
                                        </div>
                                        
                                        {/* 预览内容 */}
                                        {email.body_preview && email.body_preview.trim() !== "" && (
                                            <div className="bg-gray-50 rounded-lg px-3 py-2.5 border border-gray-100 w-full">
                                                <div className="text-xs text-gray-600 line-clamp-3 leading-relaxed break-words">
                                                    {email.body_preview}
                                                </div>
                                            </div>
                                        )}
                                        {(!email.body_preview || email.body_preview.trim() === "") && (
                                            <div className="bg-gray-50 rounded-lg px-3 py-2.5 border border-gray-100 w-full">
                                                <div className="text-xs text-gray-400 italic">
                                                    暂无预览内容
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* 验证码提示 */}
                                    {email.verification_code && (
                                        <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
                                            <div className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"></div>
                                            <span className="text-xs text-amber-700 font-medium">包含验证码</span>
                                        </div>
                                    )}

                                    {/* 验证码按钮（如果有） */}
                                    {email.verification_code && (
                                        <div className="pt-1">
                                            <Button
                                                variant="outline"
                                                className="w-full border-amber-300 text-amber-700 hover:bg-amber-50 rounded-xl h-9 text-sm font-medium"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleCopyCode(email.verification_code!);
                                                }}
                                            >
                                                <Copy className="h-3.5 w-3.5 mr-1.5" />
                                                {email.verification_code}
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </>
        )}
      </div>

      {emailsData && emailsData.total_emails > 0 && (
        <div className="flex items-center justify-between gap-2 bg-white p-2 rounded-lg shadow-sm border shrink-0 text-xs md:text-sm">
            {/* 左侧：总计 + 每页 */}
            <div className="flex items-center gap-2">
                <span className="text-muted-foreground whitespace-nowrap">
                    共 {emailsData.total_emails} 封
                </span>
                <div className="flex items-center gap-1.5">
                    <span className="text-muted-foreground whitespace-nowrap">每页</span>
                    <Select 
                        value={pageSize.toString()} 
                        onValueChange={handlePageSizeChange}
                    >
                        <SelectTrigger className="w-[80px] md:w-[70px] h-7 md:h-8 text-xs md:text-sm">
                            <SelectValue placeholder="20" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="10">10</SelectItem>
                            <SelectItem value="20">20</SelectItem>
                            <SelectItem value="50">50</SelectItem>
                            <SelectItem value="100">100</SelectItem>
                            <SelectItem value="200">200</SelectItem>
                            <SelectItem value="500">500</SelectItem>
                            <SelectItem value="1000">1000</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {/* 中间：翻页按钮 */}
            <div className="flex items-center gap-1">
                <Button
                    variant="outline"
                    size="sm"
                    className="h-7 w-7 md:h-8 md:w-8 p-0"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1 || isEmailsLoading}
                >
                    <ChevronLeft className="h-3.5 w-3.5 md:h-4 md:w-4" />
                </Button>
                
                <div className="flex items-center justify-center min-w-[70px] md:min-w-[80px] text-xs md:text-sm">
                    <span>{page} / {emailsData.total_pages}</span>
                </div>

                <Button
                    variant="outline"
                    size="sm"
                    className="h-7 w-7 md:h-8 md:w-8 p-0"
                    onClick={() => setPage(p => Math.min(emailsData.total_pages, p + 1))}
                    disabled={page >= emailsData.total_pages || isEmailsLoading}
                >
                    <ChevronRight className="h-3.5 w-3.5 md:h-4 md:w-4" />
                </Button>
            </div>

            {/* 右侧：跳转（桌面端） */}
            <div className="hidden sm:flex items-center gap-2">
                <Input
                    className="h-7 md:h-8 w-[50px] md:w-[60px] text-center px-1 text-xs md:text-sm"
                    placeholder="页码"
                    type="number"
                    min={1}
                    max={emailsData.total_pages}
                    value={jumpPage}
                    onChange={(e) => setJumpPage(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            handleJumpPage();
                        }
                    }}
                />
                <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-7 md:h-8 px-2 text-xs md:text-sm"
                    onClick={handleJumpPage}
                    disabled={!jumpPage}
                >
                    跳转
                </Button>
            </div>
        </div>
      )}

      <Dialog open={emailDetailOpen} onOpenChange={(open) => {
        setEmailDetailOpen(open);
      }}>
        <DialogContent className="max-w-[95vw] lg:max-w-7xl max-h-[90vh] overflow-hidden flex flex-col w-full">
          {selectedEmailId && selectedAccount && (
            <EmailDetailModalView 
              account={selectedAccount} 
              messageId={selectedEmailId}
              onDelete={() => {
                if (selectedEmailId) {
                  handleDeleteEmail(selectedEmailId);
                  setEmailDetailOpen(false);
                  setSelectedEmailId(null);
                }
              }}
            />
          )}
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!deleteEmailId} onOpenChange={(open) => !open && setDeleteEmailId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除这封邮件吗？此操作无法撤销。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (deleteEmailId) {
                  handleDeleteEmail(deleteEmailId);
                  setDeleteEmailId(null);
                }
              }}
              className="bg-red-600 hover:bg-red-700"
            >
              删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={clearInboxOpen} onOpenChange={setClearInboxOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {folder === "inbox" ? "确认清空收件箱" : folder === "junk" ? "确认清空垃圾箱" : "确认清空收件箱"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              确定要清空{folder === "inbox" ? "收件箱" : folder === "junk" ? "垃圾箱" : "收件箱"}吗？这将删除{folder === "inbox" ? "收件箱" : folder === "junk" ? "垃圾箱" : "收件箱"}中的所有邮件，此操作无法撤销。
              <br />
              <span className="text-xs text-muted-foreground mt-2 block">
                注意：将删除所有{folder === "inbox" ? "收件箱" : folder === "junk" ? "垃圾箱" : "收件箱"}中的邮件，不仅仅是当前页显示的邮件。
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                handleClearFolder();
                setClearInboxOpen(false);
              }}
              className="bg-red-600 hover:bg-red-700"
            >
              清空
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
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

function EmailDetailModalView({ account, messageId, onDelete }: { account: string, messageId: string, onDelete?: () => void }) {
    const { data: email, isLoading, error, refetch, isRefetching } = useEmailDetail(account, messageId);
    const [copied, setCopied] = useState(false);
    const [viewMode, setViewMode] = useState<"html" | "text" | "source">("html");
    const [refreshCountdown, setRefreshCountdown] = useState(30);
    const [isAutoRefreshEnabled] = useState(true);
    
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
                queueMicrotask(() => {
                    setStableEmailBody(body);
                    setStableEmailBodyKey(currentKey);
                    setRefreshCountdown(30);
                });
                countdownRef.current = 30;
            }
        }
    }, [messageId, viewMode, email, stableEmailBodyKey]);

    // 当切换邮件时，重置倒计时
    useEffect(() => {
        countdownRef.current = 30;
        queueMicrotask(() => setRefreshCountdown(30));
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
                        {onDelete && (
                            <Button
                                variant="ghost"
                                size="sm"
                                className="h-8 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    if (confirm("确定要删除这封邮件吗？")) {
                                        onDelete();
                                    }
                                }}
                                title="删除邮件"
                            >
                                <Trash className="h-4 w-4 mr-1" />
                                <span className="text-xs">删除</span>
                            </Button>
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
