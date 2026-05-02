"use client";

import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ChevronDown, ChevronUp } from "lucide-react";

import { EmailDetailPanel } from "@/components/emails/EmailDetailPanel";
import { EmailListPanel } from "@/components/emails/EmailListPanel";
import { EmailToolbar } from "@/components/emails/EmailToolbar";
import { PageHeader } from "@/components/layout/PageHeader";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { DataEmptyState } from "@/components/ui/data-empty-state";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useAccounts } from "@/hooks/useAccounts";
import { useDeliveryStrategy } from "@/hooks/useDeliveryStrategy";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";
import { useEmails } from "@/hooks/useEmails";
import { useVerificationCodeAutoCopy } from "@/hooks/useVerificationCodeAutoCopy";
import { copyToClipboard } from "@/lib/clipboard";
import api, {
  buildV2MessagePath,
  buildV2MessageQueryParams,
  buildV2MessagesPath,
} from "@/lib/api";
import {
  mapProviderLabel,
  mapStrategyLabel,
  summarizeDeliveryStrategy,
} from "@/lib/microsoftAccess";
import { Email, ProviderOverride, StrategyMode } from "@/types";
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
import { ShareTokenDialog } from "@/components/share/ShareTokenDialog";

export default function EmailsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[60dvh] items-center justify-center text-sm text-muted-foreground">
          正在加载邮件页面...
        </div>
      }
    >
      <EmailsPageContent />
    </Suspense>
  );
}

function EmailsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialAccount = searchParams.get("account");

  const [selectedAccount, setSelectedAccount] = useState<string | null>(initialAccount);
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const [selectedEmailData, setSelectedEmailData] = useState<Email | null>(null);
  const [emailDetailOpen, setEmailDetailOpen] = useState(false);
  const [deleteEmailId, setDeleteEmailId] = useState<string | null>(null);
  const [clearInboxOpen, setClearInboxOpen] = useState(false);
  const [isCreateShareDialogOpen, setIsCreateShareDialogOpen] = useState(false);

  const [localSearch, setLocalSearch] = useState("");
  const [localSearchType, setLocalSearchType] = useState<"subject" | "sender">("subject");
  const [localFolder, setLocalFolder] = useState<string>("all");

  const [folder, setFolder] = useState<string>("all");
  const [sortBy, setSortBy] = useState<string>("date");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [querySortBy, setQuerySortBy] = useState<string>("date");
  const [querySortOrder, setQuerySortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [jumpPage, setJumpPage] = useState("");
  const [forceRefreshOnce, setForceRefreshOnce] = useState(false);
  const [pendingRefreshSource, setPendingRefreshSource] = useState<"idle" | "manual" | "auto">("idle");
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);
  const [isAutoRefreshEnabled, setIsAutoRefreshEnabled] = useState(true);
  const [useV2ReadPath, setUseV2ReadPath] = useState(true);
  const [isReadPathPanelCollapsed, setIsReadPathPanelCollapsed] = useState(true);
  const [overrideProvider, setOverrideProvider] = useState<ProviderOverride>("auto");
  const [strategyModeOverride, setStrategyModeOverride] = useState<StrategyMode>("auto");
  const [skipCache, setSkipCache] = useState(false);

  const queryClient = useQueryClient();
  const { data: accountsResponse } = useAccounts(
    { page_size: 100 },
    {
      refetchOnMount: false,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
      staleTime: 5 * 60 * 1000,
    }
  );
  const accounts = useMemo(() => accountsResponse?.accounts || [], [accountsResponse?.accounts]);
  const selectedAccountInfo = useMemo(
    () => accounts.find((account) => account.email_id === selectedAccount) ?? null,
    [accounts, selectedAccount]
  );

  const { data: emailsData, isLoading: isEmailsLoading, refetch: refetchEmails } = useEmails({
    account: selectedAccount || "",
    folder,
    sortBy: querySortBy,
    sortOrder: querySortOrder,
    page,
    page_size: pageSize,
    forceRefresh: forceRefreshOnce,
    useV2: useV2ReadPath,
    overrideProvider,
    strategyMode: strategyModeOverride,
    skipCache,
  });
  const { data: deliveryStrategy } = useDeliveryStrategy({
    email: selectedAccount,
    overrideProvider,
    strategyMode: strategyModeOverride,
    skipCache,
    enabled: useV2ReadPath && !!selectedAccount,
  });
  const refetchEmailsRef = useRef(refetchEmails);

  useEffect(() => {
    refetchEmailsRef.current = refetchEmails;
  }, [refetchEmails]);

  const filteredEmails = useMemo(() => {
    if (!emailsData?.emails) return [];
    if (!localSearch.trim()) return emailsData.emails;

    const searchLower = localSearch.toLowerCase().trim();
    return emailsData.emails.filter((email: Email) => {
      if (localSearchType === "sender") {
        return email.from_email.toLowerCase().includes(searchLower);
      }
      return email.subject.toLowerCase().includes(searchLower);
    });
  }, [emailsData?.emails, localSearch, localSearchType]);

  useVerificationCodeAutoCopy({
    emails: emailsData?.emails || [],
    resetKey: selectedAccount || "dashboard",
    enabled: !!selectedAccount,
    toastTitle: "主站邮件页发现新验证码",
  });

  const lastUpdatedAccountRef = useRef<string | null>(null);

  const handleAutoRefresh = useCallback(async () => {
    if (pendingRefreshSource !== "idle") {
      return;
    }
    setForceRefreshOnce(true);
    setPendingRefreshSource("auto");
  }, [pendingRefreshSource]);

  const { countdown: refreshCountdown } = useAutoRefresh({
    enabled: isAutoRefreshEnabled && !!selectedAccount,
    intervalSeconds: 30,
    onRefresh: handleAutoRefresh,
    isLoading: isEmailsLoading,
  });

  useEffect(() => {
    if (pendingRefreshSource === "idle" || !forceRefreshOnce) {
      return;
    }

    let cancelled = false;

    const runListRefresh = async () => {
      try {
        await refetchEmailsRef.current();
        if (!cancelled && pendingRefreshSource === "manual") {
          toast.success("邮件列表已刷新");
        }
      } finally {
        if (!cancelled) {
          setForceRefreshOnce(false);
          setPendingRefreshSource("idle");
          if (pendingRefreshSource === "manual") {
            setIsManualRefreshing(false);
          }
        }
      }
    };

    void runListRefresh();

    return () => {
      cancelled = true;
    };
  }, [forceRefreshOnce, pendingRefreshSource]);

  const handleManualRefresh = () => {
    if (pendingRefreshSource !== "idle") {
      return;
    }
    setForceRefreshOnce(true);
    setPendingRefreshSource("manual");
    setIsManualRefreshing(true);
  };

  const handlePageSizeChange = (newPageSize: string) => {
    setPageSize(parseInt(newPageSize, 10));
    setPage(1);
  };

  const handleJumpPage = () => {
    const pageNum = parseInt(jumpPage, 10);
    if (!emailsData) return;

    if (!Number.isNaN(pageNum) && pageNum >= 1 && pageNum <= emailsData.total_pages) {
      setPage(pageNum);
      setJumpPage("");
    } else {
      toast.error(`请输入有效的页码 (1-${emailsData.total_pages})`);
    }
  };

  useEffect(() => {
    const urlAccount = searchParams.get("account");

    if (urlAccount && urlAccount !== selectedAccount) {
      if (accounts.some((account) => account.email_id === urlAccount)) {
        if (urlAccount !== lastUpdatedAccountRef.current) {
          lastUpdatedAccountRef.current = urlAccount;
          setSelectedAccount(urlAccount);
        }
      }
    }
  }, [accounts, searchParams, selectedAccount]);

  useEffect(() => {
    if (!selectedAccount) {
      return;
    }

    const currentAccountParam = searchParams.get("account");
    if (currentAccountParam !== selectedAccount && lastUpdatedAccountRef.current !== selectedAccount) {
      lastUpdatedAccountRef.current = selectedAccount;
      const params = new URLSearchParams(searchParams.toString());
      params.set("account", selectedAccount);
      router.replace(`?${params.toString()}`);
    } else if (currentAccountParam === selectedAccount && lastUpdatedAccountRef.current !== selectedAccount) {
      lastUpdatedAccountRef.current = selectedAccount;
    }
  }, [router, searchParams, selectedAccount]);

  useEffect(() => {
    if (!selectedAccount && accounts.length > 0) {
      setSelectedAccount(accounts[0].email_id);
    }
  }, [accounts, selectedAccount]);

  useEffect(() => {
    setPage(1);
  }, [folder, selectedAccount]);

  useEffect(() => {
    setLocalSearch("");
    setLocalSearchType("subject");
    setLocalFolder("all");
    setFolder("all");
    setSortBy("date");
    setSortOrder("desc");
    setQuerySortBy("date");
    setQuerySortOrder("desc");
    setSelectedEmailId(null);
    setSelectedEmailData(null);
  }, [selectedAccount]);

  useEffect(() => {
    if (filteredEmails.length === 0) {
      setSelectedEmailId(null);
      setSelectedEmailData(null);
      return;
    }

    const selectedFromList = filteredEmails.find((email) => email.message_id === selectedEmailId);
    if (selectedFromList) {
      setSelectedEmailData(selectedFromList);
      return;
    }

    setSelectedEmailId(filteredEmails[0].message_id);
    setSelectedEmailData(filteredEmails[0]);
  }, [filteredEmails, selectedEmailId]);

  const handleSearch = () => {
    setFolder(localFolder);
    setQuerySortBy(sortBy);
    setQuerySortOrder(sortOrder);
    setPage(1);
  };

  const handleCopyCode = async (code: string) => {
    const success = await copyToClipboard(code);
    if (success) {
      toast.success("验证码已复制到剪贴板");
    } else {
      toast.error("复制失败，请手动复制");
    }
  };

  const handleCopyAccount = async () => {
    if (!selectedAccount) {
      toast.error("请先选择邮箱账户");
      return;
    }

    const success = await copyToClipboard(selectedAccount);
    if (success) {
      toast.success("邮箱地址已复制到剪贴板");
    } else {
      toast.error("复制失败");
    }
  };

  const handleDeleteEmail = async (messageId: string) => {
    if (!selectedAccount) return;

    try {
      await api.delete(
        useV2ReadPath
          ? buildV2MessagePath(selectedAccount, messageId)
          : `/emails/${selectedAccount}/${messageId}`,
        useV2ReadPath
          ? {
              params: buildV2MessageQueryParams({
                override_provider: overrideProvider,
                strategy_mode: strategyModeOverride,
              }),
            }
          : undefined
      );
      toast.success("邮件已删除");
      queryClient.invalidateQueries({ queryKey: ["emails"] });
      if (selectedEmailId === messageId) {
        setSelectedEmailId(null);
        setSelectedEmailData(null);
        setEmailDetailOpen(false);
      }
    } catch (error: unknown) {
      const errorMessage =
        error && typeof error === "object" && "response" in error
          ? ((error as { response?: { data?: { detail?: string } } }).response?.data?.detail || "删除邮件失败")
          : "删除邮件失败";
      toast.error(errorMessage);
    }
  };

  const handleClearFolder = async () => {
    if (!selectedAccount) return;

    const targetFolder = folder;

    try {
      const folderName =
        targetFolder === "inbox"
          ? "收件箱"
          : targetFolder === "junk"
            ? "垃圾箱"
            : targetFolder === "all"
              ? "全部邮件"
              : "收件箱";
      toast.info(`开始清空${folderName}...`);

      const response = await api.delete(
        useV2ReadPath
          ? buildV2MessagesPath(selectedAccount)
          : `/emails/${selectedAccount}/batch`,
        {
        params: useV2ReadPath
          ? buildV2MessageQueryParams({
              folder: targetFolder,
              override_provider: overrideProvider,
              strategy_mode: strategyModeOverride,
            })
          : {
              folder: targetFolder,
            },
      });

      const result = response.data;

      if (result.success) {
        if (result.total_count === 0) {
          toast.info(`${folderName}已经是空的`);
        } else {
          toast.success(
            `清空${folderName}完成！成功删除 ${result.success_count} 封邮件${result.fail_count > 0 ? `，失败 ${result.fail_count} 封` : ""}`
          );
        }
      } else {
        toast.error(result.message || "清空失败");
      }

      queryClient.invalidateQueries({ queryKey: ["emails"] });
      setSelectedEmailId(null);
      setSelectedEmailData(null);
      setEmailDetailOpen(false);
    } catch (error: unknown) {
      const errorMessage =
        error && typeof error === "object" && "response" in error
          ? ((error as { response?: { data?: { detail?: string } } }).response?.data?.detail || "清空失败")
          : "清空失败";
      toast.error(errorMessage);
    }
  };

  const openEmailDetail = (messageId: string, emailData?: Email) => {
    setSelectedEmailId(messageId);
    setSelectedEmailData(emailData || null);

    if (typeof window !== "undefined" && window.matchMedia("(max-width: 1279px)").matches) {
      setEmailDetailOpen(true);
    }
  };

  const detailPanel = selectedAccount && selectedEmailId ? (
    <EmailDetailPanel
      account={selectedAccount}
      messageId={selectedEmailId}
      emailData={selectedEmailData}
      useV2={useV2ReadPath}
      overrideProvider={overrideProvider}
      strategyMode={strategyModeOverride}
      skipCache={skipCache || forceRefreshOnce}
      onDelete={() => {
        if (selectedEmailId) {
          void handleDeleteEmail(selectedEmailId);
        }
      }}
    />
  ) : (
    <DataEmptyState
      title="请选择一封邮件"
      description="从左侧邮件列表中选择一封邮件，即可在这里查看正文、验证码与快捷操作。"
    />
  );

  return (
    <div className="page-enter space-y-3 md:space-y-4">
      <PageHeader
        title="邮件工作区"
        description="围绕账户、筛选、验证码与正文详情的一站式邮件处理面板。"
        className="pb-0 md:pb-0 border-b-0"
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsReadPathPanelCollapsed((current) => !current)}
          >
            {isReadPathPanelCollapsed ? (
              <ChevronDown className="mr-1.5 h-4 w-4" />
            ) : (
              <ChevronUp className="mr-1.5 h-4 w-4" />
            )}
            {isReadPathPanelCollapsed ? "展开读取路径栏" : "收起读取路径栏"}
          </Button>
        }
      />

      {!isReadPathPanelCollapsed ? (
        <div className="panel-surface space-y-3 p-4">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={useV2ReadPath ? "default" : "secondary"}>
              {useV2ReadPath ? "V2 调试读链路" : "V1 兼容读链路"}
            </Badge>
            <span className="text-sm text-muted-foreground">
              可直接切换 `/api/v2` 的 provider override、strategy mode 与 skip cache。
            </span>
          </div>

          <div className="grid gap-3 lg:grid-cols-[180px_180px_180px_auto]">
            <div className="space-y-2">
              <div className="text-xs text-muted-foreground">读取路径</div>
              <Select
                value={useV2ReadPath ? "v2" : "v1"}
                onValueChange={(value) => setUseV2ReadPath(value === "v2")}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="v1">V1 兼容</SelectItem>
                  <SelectItem value="v2">V2 调试</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="text-xs text-muted-foreground">Provider Override</div>
              <Select
                value={overrideProvider}
                onValueChange={(value) => setOverrideProvider(value as ProviderOverride)}
                disabled={!useV2ReadPath}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">自动</SelectItem>
                  <SelectItem value="graph">Graph API</SelectItem>
                  <SelectItem value="imap">IMAP</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <div className="text-xs text-muted-foreground">Strategy Mode</div>
              <Select
                value={strategyModeOverride}
                onValueChange={(value) => setStrategyModeOverride(value as StrategyMode)}
                disabled={!useV2ReadPath}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">自动选择</SelectItem>
                  <SelectItem value="graph_preferred">Graph 优先</SelectItem>
                  <SelectItem value="graph_only">仅 Graph</SelectItem>
                  <SelectItem value="imap_only">仅 IMAP</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <label className="flex items-center gap-3 rounded-xl border border-border/70 px-3 py-2 text-sm">
              <Checkbox
                checked={skipCache}
                onCheckedChange={(checked) => setSkipCache(Boolean(checked))}
                disabled={!useV2ReadPath}
              />
              <span>跳过缓存（skip_cache）</span>
            </label>
          </div>

          {useV2ReadPath && selectedAccount ? (
            <div className="rounded-xl border border-border/70 bg-[color:var(--surface-1)]/60 p-3 text-sm text-muted-foreground">
              <div className="font-medium text-foreground">
                {summarizeDeliveryStrategy(deliveryStrategy)}
              </div>
              <div className="mt-1 flex flex-wrap gap-3 text-xs">
                <span>账户：{selectedAccount}</span>
                <span>override：{mapProviderLabel(overrideProvider)}</span>
                <span>strategy：{mapStrategyLabel(strategyModeOverride)}</span>
                {deliveryStrategy?.resolved_provider ? (
                  <span>resolved：{mapProviderLabel(deliveryStrategy.resolved_provider)}</span>
                ) : null}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}

      <EmailToolbar
        accounts={accounts}
        selectedAccount={selectedAccount}
        selectedAccountInfo={selectedAccountInfo}
        localSearch={localSearch}
        localSearchType={localSearchType}
        localFolder={localFolder}
        sortBy={sortBy}
        sortOrder={sortOrder}
        refreshCountdown={refreshCountdown}
        isAutoRefreshEnabled={isAutoRefreshEnabled}
        isEmailsLoading={isEmailsLoading}
        isManualRefreshing={isManualRefreshing}
        onSelectedAccountChange={setSelectedAccount}
        onCopyAccount={handleCopyAccount}
        onLocalSearchChange={setLocalSearch}
        onLocalSearchTypeChange={setLocalSearchType}
        onLocalFolderChange={setLocalFolder}
        onSortByChange={setSortBy}
        onToggleSortOrder={() => setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"))}
        onToggleAutoRefresh={() => setIsAutoRefreshEnabled((current) => !current)}
        onSearch={handleSearch}
        onManualRefresh={handleManualRefresh}
        onOpenCreateShare={() => {
          if (!selectedAccount) {
            toast.error("请先选择邮箱账户");
            return;
          }
          setIsCreateShareDialogOpen(true);
        }}
        onOpenClearFolder={() => setClearInboxOpen(true)}
      />

      <div className="grid min-h-[72dvh] gap-4 xl:grid-cols-[minmax(320px,0.82fr)_minmax(460px,1.18fr)]">
        <div className="panel-surface p-3 md:p-4">
          {!selectedAccount ? (
            <DataEmptyState
              title="请先选择邮箱账户"
              description="从顶部工作区选择一个账户后，邮件列表和详情区才会加载。"
            />
          ) : (
            <EmailListPanel
              emails={filteredEmails}
              isLoading={isEmailsLoading}
              activeEmailId={selectedEmailId}
              searchKeyword={localSearch}
              page={page}
              pageSize={pageSize}
              totalPages={emailsData?.total_pages || 1}
              totalEmails={emailsData?.total_emails || 0}
              jumpPage={jumpPage}
              onJumpPageChange={setJumpPage}
              onJumpPage={handleJumpPage}
              onPrevPage={() => setPage((current) => Math.max(1, current - 1))}
              onNextPage={() => setPage((current) => Math.min(emailsData?.total_pages || 1, current + 1))}
              onPageSizeChange={handlePageSizeChange}
              onOpenEmail={openEmailDetail}
              onDeleteRequest={setDeleteEmailId}
              onCopyCode={handleCopyCode}
            />
          )}
        </div>

        <div className="hidden xl:block">{detailPanel}</div>
      </div>

      <Dialog open={emailDetailOpen} onOpenChange={setEmailDetailOpen}>
        <DialogContent className="max-h-[90vh] w-full max-w-[95vw] overflow-hidden lg:max-w-6xl">
          {detailPanel}
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
                  void handleDeleteEmail(deleteEmailId);
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
              {folder === "inbox" ? "确认清空收件箱" : folder === "junk" ? "确认清空垃圾箱" : folder === "all" ? "确认清空全部邮件" : "确认清空收件箱"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              确定要清空{folder === "inbox" ? "收件箱" : folder === "junk" ? "垃圾箱" : folder === "all" ? "全部邮件" : "收件箱"}吗？这将删除对应文件夹中的所有邮件，此操作无法撤销。
              <br />
              <span className="mt-2 block text-xs text-muted-foreground">
                注意：将删除文件夹中的所有邮件，不仅仅是当前页显示的邮件。
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                void handleClearFolder();
                setClearInboxOpen(false);
              }}
              className="bg-red-600 hover:bg-red-700"
            >
              清空
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <ShareTokenDialog
        open={isCreateShareDialogOpen}
        onOpenChange={setIsCreateShareDialogOpen}
        emailAccount={selectedAccount || undefined}
        onSuccess={() => {
          setIsCreateShareDialogOpen(false);
        }}
      />
    </div>
  );
}
