"use client";

import { ArrowUpDown, Copy, RefreshCw, Search, Share2, Trash2 } from "lucide-react";

import { SendEmailDialog } from "@/components/emails/SendEmailDialog";
import { FilterToolbar } from "@/components/ui/filter-toolbar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { Account } from "@/types";

interface EmailToolbarProps {
  accounts: Account[];
  selectedAccount: string | null;
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
  onSearch: () => void;
  onManualRefresh: () => void;
  onOpenCreateShare: () => void;
  onOpenClearFolder: () => void;
}

export function EmailToolbar({
  accounts,
  selectedAccount,
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
  onSearch,
  onManualRefresh,
  onOpenCreateShare,
  onOpenClearFolder,
}: EmailToolbarProps) {
  const hasAccount = Boolean(selectedAccount);
  const autoRefreshStatus = !hasAccount ? "未选择账户" : isAutoRefreshEnabled ? `${refreshCountdown}s` : "已关闭";
  const autoRefreshControl = (
    <Button
      variant="ghost"
      onClick={onToggleAutoRefresh}
      disabled={!hasAccount}
      aria-pressed={isAutoRefreshEnabled}
      className={cn(
        "group self-start inline-flex h-10 items-center gap-3 rounded-full border px-2.5 text-sm font-semibold shadow-[0_10px_24px_rgba(16,185,129,0.16)] transition-all duration-200",
        isAutoRefreshEnabled
          ? "border-emerald-300/80 bg-[linear-gradient(135deg,rgba(16,185,129,0.18),rgba(14,165,233,0.14))] text-emerald-900 hover:border-emerald-400 hover:bg-[linear-gradient(135deg,rgba(16,185,129,0.22),rgba(14,165,233,0.18))]"
          : "border-slate-300/80 bg-[color:var(--surface-1)]/85 text-slate-600 shadow-[0_10px_24px_rgba(15,23,42,0.08)] hover:border-slate-400 hover:bg-[color:var(--surface-1)]",
      )}
    >
      <span
        className={cn(
          "inline-flex h-7 items-center gap-2 rounded-full px-3",
          isAutoRefreshEnabled ? "bg-white/78 text-emerald-900" : "bg-white/88 text-slate-600",
        )}
      >
        <span
          className={cn(
            "h-2.5 w-2.5 rounded-full",
            isAutoRefreshEnabled ? "bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.14)]" : "bg-slate-400",
          )}
        />
        <span>自动刷新</span>
      </span>
      <span
        className={cn(
          "inline-flex min-w-[74px] items-center justify-center rounded-full px-3 py-1 text-xs font-mono tracking-[0.08em]",
          isAutoRefreshEnabled ? "bg-emerald-950 text-emerald-50" : "bg-slate-200 text-slate-600",
        )}
      >
        {autoRefreshStatus}
      </span>
    </Button>
  );

  return (
    <div className="panel-surface space-y-3 p-3 md:p-4">
      <div className="grid gap-3 md:grid-cols-[minmax(0,1.55fr)_auto]">
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
        <Button variant="outline" onClick={onCopyAccount} disabled={!hasAccount}>
          <Copy className="mr-2 h-4 w-4" />
          复制邮箱
        </Button>
      </div>

      <div className="grid gap-3 md:grid-cols-[minmax(0,2.7fr)_160px_auto]">
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
        <Button variant="outline" onClick={onToggleSortOrder}>
          <ArrowUpDown className={cn("mr-2 h-4 w-4", sortOrder === "asc" && "rotate-180")} />
          {sortOrder === "asc" ? "升序" : "降序"}
        </Button>
      </div>

      <FilterToolbar
        className="space-y-0 border-0 bg-transparent p-0 shadow-none"
        leading={autoRefreshControl}
        center={null}
        trailing={
          <>
            <SendEmailDialog account={selectedAccount} />
            <Button variant="outline" onClick={onOpenCreateShare} disabled={!hasAccount}>
              <Share2 className="mr-2 h-4 w-4" />
              创建分享
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
            <Button variant="outline" onClick={onManualRefresh} disabled={isEmailsLoading || isManualRefreshing}>
              <RefreshCw className={cn("mr-2 h-4 w-4", (isEmailsLoading || isManualRefreshing) && "animate-spin")} />
              刷新
            </Button>
          </>
        }
      />
    </div>
  );
}
