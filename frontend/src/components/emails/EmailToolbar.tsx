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
  onSearch,
  onManualRefresh,
  onOpenCreateShare,
  onOpenClearFolder,
}: EmailToolbarProps) {
  const hasAccount = Boolean(selectedAccount);

  return (
    <FilterToolbar
      leading={
        <div className="grid gap-3 md:grid-cols-[minmax(0,1.4fr)_auto]">
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
      }
      center={
        <>
          <div className="grid gap-3 md:grid-cols-[minmax(0,1.8fr)_180px]">
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
          </div>

          <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
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
        </>
      }
      trailing={
        <>
          {isAutoRefreshEnabled ? (
            <span className="min-w-[56px] text-xs font-mono text-[color:var(--text-soft)]">
              {refreshCountdown}s
            </span>
          ) : null}
          <Button onClick={onSearch} disabled={isEmailsLoading} variant="outline">
            <Search className="mr-2 h-4 w-4" />
            查询
          </Button>
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
  );
}
