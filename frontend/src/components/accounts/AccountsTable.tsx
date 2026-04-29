"use client";

import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  CheckCircle,
  Clock,
  Eye,
  Mail,
  MoreHorizontal,
  RefreshCw,
  Share2,
  Tag,
  Trash,
  XCircle,
} from "lucide-react";

import { ShareTokenDialog } from "@/components/share/ShareTokenDialog";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDeleteAccount, useRefreshToken } from "@/hooks/useAccounts";
import { useResponsiveActions } from "@/hooks/useResponsiveActions";
import { cn } from "@/lib/utils";
import { Account } from "@/types";

import { TagsDialog } from "./TagsDialog";

interface AccountsTableProps {
  accounts: Account[];
  selectedAccounts?: string[];
  onSelectionChange?: (emailIds: string[]) => void;
}

export function AccountsTable({
  accounts,
  selectedAccounts = [],
  onSelectionChange,
}: AccountsTableProps) {
  const router = useRouter();
  const [expandedMobileTags, setExpandedMobileTags] = useState<Record<string, boolean>>({});
  const [tagDialogState, setTagDialogState] = useState<{
    open: boolean;
    email: string | null;
    tags: string[];
  }>({
    open: false,
    email: null,
    tags: [],
  });
  const [shareDialogState, setShareDialogState] = useState<{ open: boolean; email: string }>({
    open: false,
    email: "",
  });

  const deleteAccount = useDeleteAccount();
  const refreshToken = useRefreshToken();
  const showAllActions = useResponsiveActions(1200);

  const handleSelectAccount = (emailId: string, checked: boolean) => {
    if (checked) {
      onSelectionChange?.([...selectedAccounts, emailId]);
    } else {
      onSelectionChange?.(selectedAccounts.filter((id) => id !== emailId));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange?.(accounts.map((account) => account.email_id));
    } else {
      onSelectionChange?.([]);
    }
  };

  const isAllSelected = accounts.length > 0 && selectedAccounts.length === accounts.length;
  const isIndeterminate = selectedAccounts.length > 0 && selectedAccounts.length < accounts.length;

  const handleEditTags = (account: Account) => {
    setTagDialogState({ open: true, email: account.email_id, tags: account.tags || [] });
  };

  const handleShare = (account: Account) => {
    setShareDialogState({ open: true, email: account.email_id });
  };

  const getTagColor = (tag: string) => {
    const colors = [
      "bg-blue-100 text-blue-700 border border-blue-200",
      "bg-green-100 text-green-700 border border-green-200",
      "bg-amber-50 text-amber-700 border border-amber-200",
      "bg-slate-100 text-slate-700 border border-slate-200",
      "bg-indigo-100 text-indigo-700 border border-indigo-200",
      "bg-cyan-100 text-cyan-700 border border-cyan-200",
    ];

    let hash = 0;
    for (let index = 0; index < tag.length; index += 1) {
      hash = tag.charCodeAt(index) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  const getStatusBadgeClassName = (status: Account["status"]) => {
    if (status === "active") return "bg-green-500/10 text-green-600 border-green-500/25";
    if (status === "invalid") return "bg-red-500/10 text-red-600 border-red-500/25";
    return "bg-amber-500/10 text-amber-600 border-amber-500/25";
  };

  const getRefreshStatusClassName = (status: Account["refresh_status"]) => {
    if (status === "success") return "text-green-600";
    if (status === "failed") return "text-red-600";
    return "text-amber-600";
  };

  const desktopTagLimit = 6;
  const mobileTagLimit = 4;

  const renderActionButtons = (account: Account, compact = false) => (
    <>
      <Button variant="ghost" size={compact ? "icon" : "sm"} className={cn(compact ? "h-9 w-9" : "h-9 px-3")} asChild>
        <Link href={`/dashboard/emails?account=${account.email_id}`}>
          <Eye className="h-4 w-4" />
          {!compact ? <span>查看邮件</span> : null}
        </Link>
      </Button>
      <Button
        variant="ghost"
        size={compact ? "icon" : "sm"}
        className={cn(compact ? "h-9 w-9" : "h-9 px-3")}
        onClick={() => refreshToken.mutate(account.email_id)}
        throttle={true}
        throttleMs={300}
      >
        <RefreshCw className="h-4 w-4" />
        {!compact ? <span>刷新 Token</span> : null}
      </Button>
      <Button
        variant="ghost"
        size={compact ? "icon" : "sm"}
        className={cn(compact ? "h-9 w-9" : "h-9 px-3")}
        onClick={() => handleShare(account)}
        throttle={true}
        throttleMs={300}
      >
        <Share2 className="h-4 w-4" />
        {!compact ? <span>分享</span> : null}
      </Button>
      <Button
        variant="ghost"
        size={compact ? "icon" : "sm"}
        className={cn(compact ? "h-9 w-9" : "h-9 px-3")}
        onClick={() => handleEditTags(account)}
        throttle={true}
        throttleMs={300}
      >
        <Tag className="h-4 w-4" />
        {!compact ? <span>标签</span> : null}
      </Button>
      <Button
        variant="ghost"
        size={compact ? "icon" : "sm"}
        className={cn(
          compact ? "h-9 w-9 text-red-600 hover:text-red-700" : "h-9 px-3 text-red-600 hover:text-red-700"
        )}
        onClick={() => {
          if (confirm("确定要删除此账户吗？")) {
            deleteAccount.mutate(account.email_id);
          }
        }}
        throttle={true}
        throttleMs={300}
      >
        <Trash className="h-4 w-4" />
        {!compact ? <span>删除</span> : null}
      </Button>
    </>
  );

  return (
    <>
      <div className="grid gap-4 md:hidden">
        {accounts.map((account) => {
          const tags = account.tags || [];
          const isExpanded = !!expandedMobileTags[account.email_id];
          const visibleTags = isExpanded ? tags : tags.slice(0, mobileTagLimit);
          const hiddenCount = tags.length - visibleTags.length;
          const isSelected = selectedAccounts.includes(account.email_id);

          return (
            <Card
              key={account.email_id}
              className="interactive-lift cursor-pointer border-border/70 p-0"
              onClick={() => router.push(`/dashboard/emails?account=${encodeURIComponent(account.email_id)}`)}
            >
              <CardContent className="p-4">
                <div className="flex items-start gap-3">
                  <Checkbox
                    checked={isSelected}
                    onCheckedChange={(checked) => handleSelectAccount(account.email_id, checked as boolean)}
                    onClick={(event) => event.stopPropagation()}
                    className="mt-1"
                  />
                  <Avatar className="h-10 w-10 shrink-0">
                    <AvatarFallback className="bg-gradient-to-br from-[color:var(--brand)] to-[color:var(--accent)] text-[color:var(--primary-foreground)]">
                      {account.email_id.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                  <div className="min-w-0 flex-1">
                    <div className="mb-2 flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="mb-1 break-all text-sm font-medium">{account.email_id}</div>
                        <div className="break-all font-mono text-xs text-[color:var(--text-faint)]">
                          ID: {account.client_id.substring(0, 8)}...
                        </div>
                      </div>
                    </div>

                    <div className="mb-2">
                      {tags.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {visibleTags.map((tag) => (
                            <Badge
                              key={tag}
                              variant="secondary"
                              title={tag}
                              className={cn("max-w-[180px] truncate border-0 text-xs font-normal", getTagColor(tag))}
                            >
                              {tag}
                            </Badge>
                          ))}
                          {hiddenCount > 0 ? (
                            <Badge variant="secondary" className="border border-dashed bg-slate-100 text-xs font-normal text-slate-700">
                              +{hiddenCount}
                            </Badge>
                          ) : null}
                        </div>
                      ) : (
                        <span className="text-xs italic text-[color:var(--text-faint)]">无标签</span>
                      )}
                      {tags.length > mobileTagLimit ? (
                        <button
                          type="button"
                          className="mt-2 text-xs text-blue-600 hover:text-blue-700"
                          onClick={(event) => {
                            event.stopPropagation();
                            setExpandedMobileTags((prev) => ({
                              ...prev,
                              [account.email_id]: !isExpanded,
                            }));
                          }}
                        >
                          {isExpanded ? "收起标签" : `展开全部标签 (${tags.length})`}
                        </button>
                      ) : null}
                    </div>

                    <div className="mb-3 flex items-center gap-3">
                      <Badge variant="outline" className={cn("font-normal", getStatusBadgeClassName(account.status))}>
                        {account.status === "active" ? "正常" : account.status === "invalid" ? "无效" : "错误"}
                      </Badge>
                      <div className="flex items-center gap-1.5">
                        {account.refresh_status === "success" ? <CheckCircle className="h-3 w-3 text-green-500" /> : null}
                        {account.refresh_status === "failed" ? <XCircle className="h-3 w-3 text-red-500" /> : null}
                        {account.refresh_status === "pending" ? <Clock className="h-3 w-3 text-yellow-500" /> : null}
                        <span className={cn("text-xs", getRefreshStatusClassName(account.refresh_status))}>
                          {account.refresh_status === "success" ? "已刷新" : account.refresh_status === "failed" ? "刷新失败" : "待刷新"}
                        </span>
                      </div>
                    </div>

                    <div className="border-t border-border/70 pt-3">
                      <div className="mb-2 flex items-center gap-2 text-xs text-[color:var(--text-soft)]">
                        <Mail className="h-3.5 w-3.5" />
                        点击卡片即可进入邮件工作区
                      </div>
                      <div className="flex flex-wrap gap-2">{renderActionButtons(account)}</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[50px]">
                <Checkbox
                  checked={isAllSelected}
                  onCheckedChange={handleSelectAll}
                  className={cn(isIndeterminate && "data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground")}
                />
              </TableHead>
              <TableHead className="hidden w-[56px] sm:table-cell"></TableHead>
              <TableHead>账户</TableHead>
              <TableHead className="hidden min-w-[280px] w-[320px] md:table-cell">标签</TableHead>
              <TableHead className="hidden lg:table-cell">状态</TableHead>
              <TableHead className="hidden lg:table-cell">刷新状态</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.map((account) => (
              <TableRow
                key={account.email_id}
                data-state={selectedAccounts.includes(account.email_id) ? "selected" : undefined}
                className="cursor-pointer"
                onClick={() => router.push(`/dashboard/emails?account=${encodeURIComponent(account.email_id)}`)}
              >
                <TableCell onClick={(event) => event.stopPropagation()}>
                  <Checkbox
                    checked={selectedAccounts.includes(account.email_id)}
                    onCheckedChange={(checked) => handleSelectAccount(account.email_id, checked as boolean)}
                  />
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-gradient-to-br from-[color:var(--brand)] to-[color:var(--accent)] text-xs text-[color:var(--primary-foreground)]">
                      {account.email_id.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                </TableCell>
                <TableCell className="font-medium">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <Avatar className="h-6 w-6 sm:hidden">
                        <AvatarFallback className="bg-gradient-to-br from-[color:var(--brand)] to-[color:var(--accent)] text-xs text-[color:var(--primary-foreground)]">
                          {account.email_id.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <span className="break-all text-sm">{account.email_id}</span>
                    </div>
                    <span className="break-all font-mono text-xs text-[color:var(--text-faint)]">
                      ID: {account.client_id.substring(0, 8)}...
                    </span>
                    <div className="mt-1 flex flex-wrap gap-1.5 md:hidden">
                      {account.tags?.slice(0, 3).map((tag) => (
                        <Badge key={tag} variant="secondary" className={cn("border-0 text-xs font-normal", getTagColor(tag))}>
                          {tag}
                        </Badge>
                      ))}
                      {account.tags && account.tags.length > 3 ? (
                        <Badge variant="secondary" className="border-0 bg-[color:var(--surface-2)] text-xs font-normal text-[color:var(--text-soft)]">
                          +{account.tags.length - 3}
                        </Badge>
                      ) : null}
                    </div>
                    <div className="mt-1 flex items-center gap-2 lg:hidden">
                      <Badge variant="outline" className={cn("text-xs font-normal", getStatusBadgeClassName(account.status))}>
                        {account.status === "active" ? "正常" : account.status === "invalid" ? "无效" : "错误"}
                      </Badge>
                      {account.refresh_status === "success" ? <CheckCircle className="h-3 w-3 text-green-500" /> : null}
                      {account.refresh_status === "failed" ? <XCircle className="h-3 w-3 text-red-500" /> : null}
                      {account.refresh_status === "pending" ? <Clock className="h-3 w-3 text-yellow-500" /> : null}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <div className="max-w-[320px]">
                    <div className="flex flex-wrap gap-1.5">
                      {(account.tags || []).slice(0, desktopTagLimit).map((tag) => (
                        <Badge
                          key={tag}
                          variant="secondary"
                          title={tag}
                          className={cn("max-w-[130px] truncate border-0 text-xs font-normal", getTagColor(tag))}
                        >
                          {tag}
                        </Badge>
                      ))}
                      {(account.tags?.length || 0) > desktopTagLimit ? (
                        <Badge
                          variant="secondary"
                          title={(account.tags || []).slice(desktopTagLimit).join(", ")}
                          className="border border-dashed bg-[color:var(--surface-2)] text-xs font-normal text-[color:var(--text-soft)]"
                        >
                          +{(account.tags?.length || 0) - desktopTagLimit}
                        </Badge>
                      ) : null}
                      {!account.tags || account.tags.length === 0 ? (
                        <span className="text-xs italic text-[color:var(--text-faint)]">无标签</span>
                      ) : null}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="hidden lg:table-cell">
                  <Badge variant="outline" className={cn("font-normal", getStatusBadgeClassName(account.status))}>
                    {account.status === "active" ? "正常" : account.status === "invalid" ? "无效" : "错误"}
                  </Badge>
                </TableCell>
                <TableCell className="hidden lg:table-cell">
                  <div className="flex items-center gap-2">
                    {account.refresh_status === "success" ? <CheckCircle className="h-4 w-4 text-green-500" /> : null}
                    {account.refresh_status === "failed" ? <XCircle className="h-4 w-4 text-red-500" /> : null}
                    {account.refresh_status === "pending" ? <Clock className="h-4 w-4 text-yellow-500" /> : null}
                    <div className="flex flex-col">
                      <span className={cn("text-xs font-medium", getRefreshStatusClassName(account.refresh_status))}>
                        {account.refresh_status === "success" ? "成功" : account.refresh_status === "failed" ? "失败" : "待处理"}
                      </span>
                      {account.last_refresh_time ? (
                        <span className="text-[10px] text-[color:var(--text-faint)]">
                          {formatDistanceToNow(new Date(account.last_refresh_time), { addSuffix: true })}
                        </span>
                      ) : null}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="text-right" onClick={(event) => event.stopPropagation()}>
                  {showAllActions ? (
                    <div className="flex items-center justify-end gap-2">{renderActionButtons(account)}</div>
                  ) : (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-9 w-9 p-0 min-h-[44px] min-w-[44px]">
                          <span className="sr-only">打开菜单</span>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>操作</DropdownMenuLabel>
                        <DropdownMenuItem asChild>
                          <Link href={`/dashboard/emails?account=${account.email_id}`}>
                            <Eye className="mr-2 h-4 w-4" /> 查看邮件
                          </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => refreshToken.mutate(account.email_id)}>
                          <RefreshCw className="mr-2 h-4 w-4" /> 刷新 Token
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleEditTags(account)}>
                          <Tag className="mr-2 h-4 w-4" /> 管理标签
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleShare(account)}>
                          <Share2 className="mr-2 h-4 w-4" /> 分享链接
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem
                          className="text-red-600 focus:bg-red-50 focus:text-red-600"
                          onClick={() => {
                            if (confirm("确定要删除此账户吗？")) {
                              deleteAccount.mutate(account.email_id);
                            }
                          }}
                        >
                          <Trash className="mr-2 h-4 w-4" /> 删除账户
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <TagsDialog
        open={tagDialogState.open}
        onOpenChange={(open) => setTagDialogState((prev) => ({ ...prev, open }))}
        accountEmail={tagDialogState.email}
        initialTags={tagDialogState.tags}
      />

      <ShareTokenDialog
        open={shareDialogState.open}
        onOpenChange={(open) => setShareDialogState((prev) => ({ ...prev, open }))}
        emailAccount={shareDialogState.email}
      />
    </>
  );
}
