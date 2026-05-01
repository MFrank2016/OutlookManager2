"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ChevronLeft, ChevronRight, PackagePlus, RefreshCw, Search, Trash2 } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { AccountsTable } from "@/components/accounts/AccountsTable";
import { AddAccountDialog } from "@/components/accounts/AddAccountDialog";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageSection } from "@/components/layout/PageSection";
import { Badge } from "@/components/ui/badge";
import { DataEmptyState } from "@/components/ui/data-empty-state";
import { DataLoadingState } from "@/components/ui/data-loading-state";
import { Card, CardContent } from "@/components/ui/card";
import { FilterToolbar } from "@/components/ui/filter-toolbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { SelectionBar } from "@/components/ui/selection-bar";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useAccountHealth } from "@/hooks/useAccountHealth";
import api from "@/lib/api";
import { useDeliveryStrategy } from "@/hooks/useDeliveryStrategy";
import { useAccounts, useBatchDeleteAccounts } from "@/hooks/useAccounts";
import {
  getCapabilityHighlights,
  mapProviderLabel,
  mapStrategyLabel,
  summarizeDeliveryStrategy,
} from "@/lib/microsoftAccess";
import { useAccountsFilterStore } from "@/store/useAccountsFilterStore";

export default function DashboardPage() {
  const getErrorMessage = (error: unknown, fallback: string) => {
    const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
    return typeof detail === "string" ? detail : fallback;
  };

  const {
    page: storedPage,
    pageSize: storedPageSize,
    search: storedSearch,
    includeTags: storedIncludeTags,
    excludeTags: storedExcludeTags,
    refreshStatus: storedRefreshStatus,
    reset,
    setFilters,
  } = useAccountsFilterStore();

  const [page, setPage] = useState(storedPage || 1);
  const [search, setSearch] = useState(storedSearch || "");
  const [includeTags, setIncludeTags] = useState(storedIncludeTags || "");
  const [excludeTags, setExcludeTags] = useState(storedExcludeTags || "");
  const [refreshStatus, setRefreshStatus] = useState<string | undefined>(storedRefreshStatus);
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [isBatchRefreshing, setIsBatchRefreshing] = useState(false);
  const [queryParams, setQueryParams] = useState({
    page: storedPage || 1,
    page_size: storedPageSize || 10,
    email_search: storedSearch || "",
    include_tags: storedIncludeTags || "",
    exclude_tags: storedExcludeTags || "",
    refresh_status: storedRefreshStatus as string | undefined,
  });
  const [jumpPage, setJumpPage] = useState("");
  const queryClient = useQueryClient();
  const batchDeleteAccounts = useBatchDeleteAccounts();

  const { data, isLoading, isFetching, refetch } = useAccounts({
    page: queryParams.page,
    page_size: queryParams.page_size,
    email_search: queryParams.email_search,
    include_tags: queryParams.include_tags || undefined,
    exclude_tags: queryParams.exclude_tags || undefined,
    refresh_status: queryParams.refresh_status,
  });
  const summaryAccountId = selectedAccounts[0] || data?.accounts?.[0]?.email_id || null;
  const { data: accountHealth, isLoading: isHealthLoading } = useAccountHealth(summaryAccountId, !!summaryAccountId);
  const { data: deliveryStrategy, isLoading: isStrategyLoading } = useDeliveryStrategy({
    email: summaryAccountId,
    enabled: !!summaryAccountId,
  });
  const capabilityHighlights = useMemo(
    () => getCapabilityHighlights(accountHealth?.capability),
    [accountHealth?.capability]
  );

  useEffect(() => {
    if (!data?.accounts) {
      return;
    }

    const visibleAccountIds = new Set(data.accounts.map((account) => account.email_id));
    setSelectedAccounts((current) => current.filter((emailId) => visibleAccountIds.has(emailId)));
  }, [data?.accounts]);

  const hasDraftFilters = useMemo(
    () => Boolean(search.trim() || includeTags.trim() || excludeTags.trim() || refreshStatus),
    [search, includeTags, excludeTags, refreshStatus]
  );

  const hasAppliedFilters = useMemo(
    () =>
      Boolean(
        queryParams.email_search ||
        queryParams.include_tags ||
        queryParams.exclude_tags ||
        queryParams.refresh_status
      ),
    [queryParams]
  );

  const handleSearch = () => {
    const newParams = {
      page: 1,
      page_size: queryParams.page_size,
      email_search: search.trim(),
      include_tags: includeTags.trim(),
      exclude_tags: excludeTags.trim(),
      refresh_status: refreshStatus,
    };
    const isSameQuery =
      queryParams.page === newParams.page &&
      queryParams.page_size === newParams.page_size &&
      queryParams.email_search === newParams.email_search &&
      (queryParams.include_tags || "") === (newParams.include_tags || "") &&
      (queryParams.exclude_tags || "") === (newParams.exclude_tags || "") &&
      queryParams.refresh_status === newParams.refresh_status;

    if (isSameQuery) {
      setFilters({
        page: 1,
        pageSize: newParams.page_size,
        search,
        includeTags,
        excludeTags,
        refreshStatus,
      });
      void refetch();
      return;
    }

    setQueryParams(newParams);
    setPage(1);
    setFilters({
      page: 1,
      pageSize: newParams.page_size,
      search,
      includeTags,
      excludeTags,
      refreshStatus,
    });
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    setQueryParams((prev) => ({ ...prev, page: newPage }));
    setFilters({ page: newPage });
  };

  const handlePageSizeChange = (newPageSize: string) => {
    const size = parseInt(newPageSize, 10);
    setQueryParams((prev) => ({ ...prev, page_size: size, page: 1 }));
    setPage(1);
    setFilters({ pageSize: size, page: 1 });
  };

  const handleJumpPage = () => {
    const pageNum = parseInt(jumpPage, 10);
    if (!data) return;

    if (!Number.isNaN(pageNum) && pageNum >= 1 && pageNum <= data.total_pages) {
      handlePageChange(pageNum);
      setJumpPage("");
    } else {
      toast.error(`请输入有效的页码 (1-${data.total_pages})`);
    }
  };

  const handleResetFilters = () => {
    const preservedPageSize = queryParams.page_size;
    setSearch("");
    setIncludeTags("");
    setExcludeTags("");
    setRefreshStatus(undefined);
    setJumpPage("");
    setPage(1);
    setQueryParams({
      page: 1,
      page_size: preservedPageSize,
      email_search: "",
      include_tags: "",
      exclude_tags: "",
      refresh_status: undefined,
    });
    reset({ pageSize: preservedPageSize });
  };

  const handleRefreshResults = async () => {
    await refetch();
  };

  const handleBatchRefresh = async () => {
    if (selectedAccounts.length === 0) {
      toast.warning("请先选择要刷新的账户");
      return;
    }

    if (!confirm(`确定要批量刷新 ${selectedAccounts.length} 个账户的 Token 吗？`)) {
      return;
    }

    setIsBatchRefreshing(true);
    try {
      const response = await api.post("/accounts/batch-refresh-tokens", {
        email_ids: selectedAccounts,
      });

      const result = response.data;
      toast.success(`批量刷新完成：成功 ${result.success_count}，失败 ${result.failed_count}`);
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setSelectedAccounts([]);
    } catch (error: unknown) {
      toast.error(getErrorMessage(error, "批量刷新失败"));
    } finally {
      setIsBatchRefreshing(false);
    }
  };

  const handleBatchDelete = async () => {
    if (selectedAccounts.length === 0) {
      toast.warning("请先选择要删除的账户");
      return;
    }

    if (!confirm(`确定要批量删除 ${selectedAccounts.length} 个账户吗？此操作不可恢复！`)) {
      return;
    }

    try {
      await batchDeleteAccounts.mutateAsync(selectedAccounts);
      setSelectedAccounts([]);
    } catch (error: unknown) {
      toast.error(getErrorMessage(error, "批量删除失败"));
    }
  };

  const resultDescription = data
    ? `第 ${page} 页，共 ${data.total_accounts} 个账户。支持筛选、批量刷新与批量删除。`
    : "集中查看 Outlook 账户状态、标签与批量操作。";

  return (
    <div className="page-enter space-y-3 md:space-y-4">
      <PageHeader
        title="账户管理"
        description="统一查看 Outlook 账户状态、筛选标签并执行批量工作流。"
        actions={
          <>
            <Button asChild variant="secondary">
              <Link href="/dashboard/accounts/batch">
                <PackagePlus className="mr-2 h-4 w-4" /> 批量添加
              </Link>
            </Button>
            <AddAccountDialog />
          </>
        }
      />

      <FilterToolbar
        leading={
          <div className="relative w-full">
            <Search className="absolute left-3 top-3 h-4 w-4 text-[color:var(--text-faint)]" />
            <Input
              placeholder="搜索邮箱..."
              className="pl-10"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              debounce={true}
              debounceMs={500}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSearch();
                }
              }}
            />
          </div>
        }
        center={
          <>
            <div className="grid gap-3 md:grid-cols-2">
              <Input
                placeholder="包含标签（多个用逗号分隔）..."
                value={includeTags}
                onChange={(event) => setIncludeTags(event.target.value)}
                debounce={true}
                debounceMs={500}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    handleSearch();
                  }
                }}
              />
              <Input
                placeholder="排除标签（多个用逗号分隔）..."
                value={excludeTags}
                onChange={(event) => setExcludeTags(event.target.value)}
                debounce={true}
                debounceMs={500}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    handleSearch();
                  }
                }}
              />
            </div>
            <Select value={refreshStatus ?? "all"} onValueChange={(value) => setRefreshStatus(value === "all" ? undefined : value)}>
              <SelectTrigger>
                <SelectValue placeholder="筛选状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="success">成功</SelectItem>
                <SelectItem value="failed">失败</SelectItem>
                <SelectItem value="pending">待处理</SelectItem>
              </SelectContent>
            </Select>
          </>
        }
        trailing={
          <>
            <Button
              variant="outline"
              onClick={handleResetFilters}
              disabled={!hasDraftFilters && !hasAppliedFilters}
            >
              重置
            </Button>
            <Button variant="outline" onClick={handleRefreshResults} disabled={isFetching}>
              <RefreshCw className={cn("mr-2 h-4 w-4", isFetching && "animate-spin")} />
              刷新
            </Button>
            <Button onClick={handleSearch} disabled={isLoading} throttle={true} throttleMs={300}>
              <Search className="mr-2 h-4 w-4" />
              查询
            </Button>
          </>
        }
      />

      {selectedAccounts.length > 0 ? (
        <SelectionBar
          selectedCount={selectedAccounts.length}
          itemLabel="个账户"
          primaryActions={
            <Button
              variant="secondary"
              size="sm"
              onClick={handleBatchRefresh}
              disabled={isBatchRefreshing || batchDeleteAccounts.isPending}
              throttle={true}
              throttleMs={300}
            >
              <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", isBatchRefreshing && "animate-spin")} />
              批量刷新 Token
            </Button>
          }
          secondaryActions={
            <Button
              variant="destructive"
              size="sm"
              onClick={handleBatchDelete}
              disabled={batchDeleteAccounts.isPending || isBatchRefreshing}
              throttle={true}
              throttleMs={300}
            >
              <Trash2 className="mr-1.5 h-3.5 w-3.5" />
              {batchDeleteAccounts.isPending ? "删除中..." : "批量删除"}
            </Button>
          }
          onClear={() => setSelectedAccounts([])}
        />
      ) : null}

      <PageSection
        title="Microsoft Access 摘要"
        description={
          summaryAccountId
            ? `聚焦 ${summaryAccountId} 的策略、能力与最近 provider 状态。`
            : "选择或加载一个账户后，这里会展示 v2 health / delivery-strategy 摘要。"
        }
        contentClassName="grid gap-3 md:grid-cols-3"
      >
        <Card className="border-border/70">
          <CardContent className="space-y-2 p-4">
            <div className="text-xs text-muted-foreground">当前聚焦账户</div>
            <div className="break-all text-sm font-medium text-foreground">
              {summaryAccountId || "暂无"}
            </div>
            <div className="flex flex-wrap gap-2">
              {accountHealth?.strategy_mode ? (
                <Badge variant="secondary">{mapStrategyLabel(accountHealth.strategy_mode)}</Badge>
              ) : null}
              {accountHealth?.last_provider_used ? (
                <Badge variant="outline">{mapProviderLabel(accountHealth.last_provider_used)}</Badge>
              ) : null}
            </div>
          </CardContent>
        </Card>

        <Card className="border-border/70">
          <CardContent className="space-y-2 p-4">
            <div className="text-xs text-muted-foreground">能力快照</div>
            {isHealthLoading ? (
              <div className="text-sm text-muted-foreground">正在加载...</div>
            ) : capabilityHighlights.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {capabilityHighlights.map((item) => (
                  <Badge key={item} variant="outline">
                    {item}
                  </Badge>
                ))}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">暂无能力摘要</div>
            )}
            {accountHealth?.last_error?.message ? (
              <div className="text-xs text-amber-700">
                最近异常：{accountHealth.last_error.message}
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card className="border-border/70">
          <CardContent className="space-y-2 p-4">
            <div className="text-xs text-muted-foreground">投递策略解释</div>
            <div className="text-sm text-foreground">
              {isStrategyLoading
                ? "正在加载..."
                : summarizeDeliveryStrategy(deliveryStrategy)}
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
              {deliveryStrategy?.recommended_provider ? (
                <span>推荐：{mapProviderLabel(deliveryStrategy.recommended_provider)}</span>
              ) : null}
              {deliveryStrategy?.resolved_provider ? (
                <span>当前：{mapProviderLabel(deliveryStrategy.resolved_provider)}</span>
              ) : null}
            </div>
          </CardContent>
        </Card>
      </PageSection>

      <PageSection title="账户列表" description={resultDescription} contentClassName="space-y-4">
        {isLoading && !data ? (
          <DataLoadingState
            title="正在加载账户"
            description="账户列表、标签与刷新状态正在同步。"
          />
        ) : data && data.accounts.length > 0 ? (
          <AccountsTable
            accounts={data.accounts}
            selectedAccounts={selectedAccounts}
            onSelectionChange={setSelectedAccounts}
          />
        ) : (
          <DataEmptyState
            title={hasAppliedFilters ? "未找到匹配账户" : "暂无账户数据"}
            description={
              hasAppliedFilters
                ? "试试清空筛选条件，或检查标签与刷新状态是否设置过窄。"
                : "你还没有可管理的账户，可以先添加单个账户或走批量导入。"
            }
            action={
              hasAppliedFilters ? (
                <Button variant="outline" onClick={handleResetFilters}>
                  清空筛选
                </Button>
              ) : (
                <div className="flex flex-wrap items-center justify-center gap-2">
                  <AddAccountDialog />
                  <Button asChild variant="secondary">
                    <Link href="/dashboard/accounts/batch">
                      <PackagePlus className="mr-2 h-4 w-4" /> 批量添加
                    </Link>
                  </Button>
                </div>
              )
            }
          />
        )}

        {data && data.total_accounts > 0 ? (
          <div className="flex shrink-0 items-center justify-between gap-2 rounded-xl border border-border/70 bg-[color:var(--surface-1)]/75 p-3 text-xs md:text-sm">
            <div className="flex items-center gap-2">
              <span className="text-muted-foreground whitespace-nowrap">共 {data.total_accounts} 个</span>
              <div className="flex items-center gap-1.5">
                <span className="text-muted-foreground whitespace-nowrap">每页</span>
                <Select value={queryParams.page_size.toString()} onValueChange={handlePageSizeChange}>
                  <SelectTrigger className="w-[72px]" size="sm">
                    <SelectValue placeholder="10" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10</SelectItem>
                    <SelectItem value="20">20</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="1000">1000</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <Button
                variant="outline"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={() => handlePageChange(Math.max(1, page - 1))}
                disabled={page === 1 || isLoading}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>

              <div className="flex min-w-[80px] items-center justify-center text-sm">
                <span>{page} / {data.total_pages}</span>
              </div>

              <Button
                variant="outline"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={() => handlePageChange(Math.min(data.total_pages, page + 1))}
                disabled={page === data.total_pages || isLoading}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            <div className="hidden items-center gap-2 sm:flex">
              <Input
                className="h-8 w-[64px] px-2 text-center text-sm"
                placeholder="页码"
                type="number"
                min={1}
                max={data.total_pages}
                value={jumpPage}
                onChange={(event) => setJumpPage(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    handleJumpPage();
                  }
                }}
              />
              <Button variant="ghost" size="sm" className="h-8 px-2" onClick={handleJumpPage} disabled={!jumpPage}>
                跳转
              </Button>
            </div>
          </div>
        ) : null}
      </PageSection>
    </div>
  );
}
