"use client";

import { ArrowUpDown, ChevronDown, ChevronUp, Copy, RefreshCw, Search, Share2, Trash2 } from "lucide-react";

import { SendEmailDialog } from "@/components/emails/SendEmailDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { Account } from "@/types";

interface EmailToolbarProps {
  accounts: Account[];
  selectedAccount: string | null;
  selectedAccountInfo: Account | null;
  isExpanded: boolean;
  localSearch: string;
  localSearchType: "subject" | "sender";
  localFolder: string;
  sortBy: string;
  sortOrder: "asc" | "desc";
  refreshCountdown: number;
  isAutoRefreshEnabled: boolean;
  isEmailsLoading: boolean;
  isManualRefreshing: boolean;
  onSelectedAccountChange: (emailId: string) => void;
  onCopyAccount: () => void;
  onLocalSearchChange: (value: string) => void;
  onLocalSearchTypeChange: (value: "subject" | "sender") => void;
  onLocalFolderChange: (value: string) => void;
  onSortByChange: (value: string) => void;
  onToggleSortOrder: () => void;
  onToggleAutoRefresh: () => void;
  onToggleExpanded: () => void;
  onSearch: () => void;
  onManualRefresh: () => void;
  onOpenCreateShare: () => void;
  onOpenClearFolder: () => void;
}

export function EmailToolbar({
  accounts,
  selectedAccount,
  selectedAccountInfo,
  isExpanded,
  localSearch,
  localSearchType,
  localFolder,
  sortBy,
  sortOrder,
  refreshCountdown,
  isAutoRefreshEnabled,
  isEmailsLoading,
  isManualRefreshing,
  onSelectedAccountChange,
  onCopyAccount,
  onLocalSearchChange,
  onLocalSearchTypeChange,
  onLocalFolderChange,
  onSortByChange,
  onToggleSortOrder,
  onToggleAutoRefresh,
  onToggleExpanded,
  onSearch,
  onManualRefresh,
  onOpenCreateShare,
  onOpenClearFolder,
}: EmailToolbarProps) {
  const hasAccount = Boolean(selectedAccount);
  const autoRefreshStatus = !hasAccount ? "未选择账户" : isAutoRefreshEnabled ? `${refreshCountdown}s` : "已关闭";
  const summaryAccountLabel = selectedAccount ?? "请先选择邮箱账户";
  const autoRefreshLabel = !hasAccount ? "等待选择账户" : isAutoRefreshEnabled ? "自动刷新进行中" : "自动刷新已关闭";

  return (
    <div className="panel-surface overflow-hidden p-0">
      <div className="px-4 py-4 md:px-5">
        <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
          <div className="min-w-0">
            <div className="text-[11px] font-medium uppercase tracking-[0.18em] text-[color:var(--text-faint)]">
              当前邮箱
            </div>
            <div className="mt-2 rounded-2xl border border-border/70 bg-[color:var(--surface-1)]/75 px-3 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]">
              <div className="truncate text-sm font-semibold text-foreground">{summaryAccountLabel}</div>
              <div className="mt-1 text-xs text-[color:var(--text-soft)]">
                收起时只保留邮箱、刷新倒计时与手动刷新入口。
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 xl:justify-end">
            <div className="inline-flex h-10 items-center gap-2 rounded-full border border-border/70 bg-[color:var(--surface-1)]/85 px-3 text-xs text-[color:var(--text-soft)] shadow-[0_12px_30px_rgba(15,23,42,0.06)]">
              <span
                className={cn(
                  "h-2.5 w-2.5 rounded-full",
                  hasAccount && isAutoRefreshEnabled
                    ? "bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.14)]"
                    : "bg-slate-400"
                )}
              />
              <span>{autoRefreshLabel}</span>
              <span
                className={cn(
                  "rounded-full px-2.5 py-1 font-mono tracking-[0.08em]",
                  hasAccount && isAutoRefreshEnabled
                    ? "bg-emerald-950 text-emerald-50"
                    : "bg-slate-200 text-slate-600"
                )}
              >
                {autoRefreshStatus}
              </span>
            </div>

            <Button
              variant="outline"
              onClick={onManualRefresh}
              disabled={!hasAccount || isEmailsLoading || isManualRefreshing}
            >
              <RefreshCw className={cn("mr-2 h-4 w-4", (isEmailsLoading || isManualRefreshing) && "animate-spin")} />
              刷新
            </Button>

            <Button variant="ghost" size="sm" onClick={onToggleExpanded}>
              {isExpanded ? (
                <ChevronUp className="mr-1.5 h-4 w-4" />
              ) : (
                <ChevronDown className="mr-1.5 h-4 w-4" />
              )}
              {isExpanded ? "收起更多筛选" : "展开更多筛选"}
            </Button>
          </div>
        </div>
      </div>

      {!isExpanded ? null : (
        <div className="border-t border-border/70 px-4 pb-4 pt-4 md:px-5">
          <div className="space-y-4">
            <div className="grid gap-3 lg:grid-cols-[minmax(0,1.6fr)_auto]">
              <div className="w-full">
                <Select value={selectedAccount ?? undefined} onValueChange={onSelectedAccountChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="选择邮箱账户" />
                  </SelectTrigger>
                  <SelectContent>
                    {accounts.map((account) => (
                      <SelectItem key={account.email_id} value={account.email_id}>
                        {account.email_id}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Button variant="outline" onClick={onCopyAccount} disabled={!hasAccount}>
                <Copy className="mr-2 h-4 w-4" />
                复制邮箱
              </Button>
            </div>

            <div className="grid gap-3 xl:grid-cols-[minmax(0,2.8fr)_180px_auto]">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-[color:var(--text-faint)]" />
                <Input
                  placeholder={localSearchType === "subject" ? "搜索主题..." : "搜索发件人..."}
                  className="pl-10"
                  value={localSearch}
                  onChange={(event) => onLocalSearchChange(event.target.value)}
                  debounce={true}
                  debounceMs={500}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      onSearch();
                    }
                  }}
                />
              </div>
              <Select value={localSearchType} onValueChange={(value: "subject" | "sender") => onLocalSearchTypeChange(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="subject">主题</SelectItem>
                  <SelectItem value="sender">发件人</SelectItem>
                </SelectContent>
              </Select>
              <Button onClick={onSearch} disabled={isEmailsLoading} variant="outline">
                <Search className="mr-2 h-4 w-4" />
                查询
              </Button>
            </div>

            <div className="grid gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
              <div className="w-full">
                <Select value={localFolder} onValueChange={onLocalFolderChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">全部邮件</SelectItem>
                    <SelectItem value="inbox">收件箱</SelectItem>
                    <SelectItem value="junk">垃圾邮件</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="w-full">
                <Select value={sortBy} onValueChange={onSortByChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="date">日期</SelectItem>
                    <SelectItem value="subject">主题</SelectItem>
                    <SelectItem value="from_email">发件人</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button variant="outline" onClick={onToggleSortOrder}>
                <ArrowUpDown className={cn("mr-2 h-4 w-4", sortOrder === "asc" && "rotate-180")} />
                {sortOrder === "asc" ? "升序" : "降序"}
              </Button>
            </div>

            <div className="rounded-2xl border border-border/70 bg-[color:var(--surface-1)]/65 p-3">
              <div className="flex flex-wrap items-center gap-2">
                <SendEmailDialog account={selectedAccountInfo} />
                <Button variant="outline" onClick={onOpenCreateShare} disabled={!hasAccount}>
                  <Share2 className="mr-2 h-4 w-4" />
                  创建分享
                </Button>
                <Button
                  variant="outline"
                  onClick={onToggleAutoRefresh}
                  disabled={!hasAccount}
                  aria-pressed={isAutoRefreshEnabled}
                  className={cn(
                    isAutoRefreshEnabled
                      ? "border-emerald-300/80 bg-emerald-50/70 text-emerald-800 hover:bg-emerald-100"
                      : "text-[color:var(--text-soft)]"
                  )}
                >
                  <RefreshCw className={cn("mr-2 h-4 w-4", isAutoRefreshEnabled && "text-emerald-700")} />
                  {isAutoRefreshEnabled ? "关闭自动刷新" : "开启自动刷新"}
                </Button>
                <Button
                  variant="outline"
                  className="border-red-300 text-red-600 hover:bg-red-50 hover:text-red-700"
                  onClick={onOpenClearFolder}
                  disabled={!hasAccount}
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  清空
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
