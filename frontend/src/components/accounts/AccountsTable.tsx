"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Card } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal, RefreshCw, Trash, Tag, Mail, CheckCircle, XCircle, Clock, Eye, Send, CheckSquare, Square } from "lucide-react";
import { Account } from "@/types";
import { formatDistanceToNow } from "date-fns";
import { useState } from "react";
import { TagsDialog } from "./TagsDialog";
import { useDeleteAccount, useRefreshToken } from "@/hooks/useAccounts";
import { useResponsiveActions } from "@/hooks/useResponsiveActions";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Checkbox } from "@/components/ui/checkbox";

interface AccountsTableProps {
  accounts: Account[];
  isLoading: boolean;
  onBatchRefresh?: (emailIds: string[]) => void;
  selectedAccounts?: string[];
  onSelectionChange?: (emailIds: string[]) => void;
}

export function AccountsTable({ accounts, isLoading, onBatchRefresh, selectedAccounts = [], onSelectionChange }: AccountsTableProps) {
  const [tagDialogState, setTagDialogState] = useState<{ open: boolean; email: string | null; tags: string[] }>({
    open: false,
    email: null,
    tags: [],
  });
  
  const deleteAccount = useDeleteAccount();
  const refreshToken = useRefreshToken();
  const showAllActions = useResponsiveActions(1200);

  const handleSelectAccount = (emailId: string, checked: boolean) => {
    if (checked) {
      onSelectionChange?.([...selectedAccounts, emailId]);
    } else {
      onSelectionChange?.(selectedAccounts.filter(id => id !== emailId));
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      onSelectionChange?.(accounts.map(acc => acc.email_id));
    } else {
      onSelectionChange?.([]);
    }
  };

  const isAllSelected = accounts.length > 0 && selectedAccounts.length === accounts.length;
  const isIndeterminate = selectedAccounts.length > 0 && selectedAccounts.length < accounts.length;

  const handleEditTags = (account: Account) => {
    setTagDialogState({ open: true, email: account.email_id, tags: account.tags || [] });
  };

  // Function to generate a deterministic color for tags
  const getTagColor = (tag: string) => {
    const colors = ["bg-blue-100 text-blue-800", "bg-green-100 text-green-800", "bg-purple-100 text-purple-800", "bg-pink-100 text-purple-800", "bg-yellow-100 text-yellow-800", "bg-indigo-100 text-indigo-800"];
    let hash = 0;
    for (let i = 0; i < tag.length; i++) {
        hash = tag.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  if (isLoading) {
    return <div className="p-4 text-center">Loading accounts...</div>;
  }

  if (accounts.length === 0) {
    return <div className="p-4 text-center text-gray-500">No accounts found.</div>;
  }

  return (
    <>
      {/* 移动端：卡片式设计 */}
      <div className="md:hidden grid gap-4 px-4">
        {accounts.map((account) => (
          <Card key={account.email_id} className="p-4 hover:shadow-md transition-shadow">
            <div className="flex items-start gap-3">
              <Checkbox
                checked={selectedAccounts.includes(account.email_id)}
                onCheckedChange={(checked) => handleSelectAccount(account.email_id, checked as boolean)}
                onClick={(e) => e.stopPropagation()}
                className="mt-1"
              />
              <Avatar className="h-10 w-10 shrink-0">
                <AvatarFallback className="bg-blue-500 text-white">
                  {account.email_id.charAt(0).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm break-all mb-1">{account.email_id}</div>
                    <div className="text-xs text-gray-400 font-mono break-all">
                      ID: {account.client_id.substring(0, 8)}...
                    </div>
                  </div>
                </div>
                
                <div className="mb-2">
                  {account.tags && account.tags.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {account.tags.map(tag => (
                        <Badge key={tag} variant="secondary" className={cn("text-xs font-normal border-0", getTagColor(tag))}>
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  ) : (
                    <span className="text-xs text-gray-400 italic">无标签</span>
                  )}
                </div>

                <div className="flex items-center gap-3 mb-3">
                  <div className="flex items-center gap-1.5">
                    <div className={cn(
                      "h-2 w-2 rounded-full",
                      account.status === "active" ? "bg-green-500" :
                      account.status === "invalid" ? "bg-red-500" : "bg-yellow-500"
                    )} />
                    <span className="text-xs text-gray-600">
                      {account.status === "active" ? "正常" : account.status === "invalid" ? "无效" : "错误"}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    {account.refresh_status === "success" && <CheckCircle className="h-3 w-3 text-green-500" />}
                    {account.refresh_status === "failed" && <XCircle className="h-3 w-3 text-red-500" />}
                    {account.refresh_status === "pending" && <Clock className="h-3 w-3 text-yellow-500" />}
                    <span className="text-xs text-gray-500">
                      {account.refresh_status === "success" ? "已刷新" : 
                       account.refresh_status === "failed" ? "刷新失败" : "待刷新"}
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2 pt-2 border-t">
                  <Button
                    variant="default"
                    size="sm"
                    className="h-8 px-3 text-xs"
                    asChild
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Link href={`/dashboard/emails?account=${account.email_id}`}>
                      <Eye className="h-3 w-3 mr-1" />
                      查看
                    </Link>
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="h-8 px-3 text-xs"
                    asChild
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Link href={`/dashboard/emails?account=${account.email_id}`}>
                      <Send className="h-3 w-3 mr-1" />
                      发送
                    </Link>
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="h-8 px-3 text-xs"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEditTags(account);
                    }}
                  >
                    <Tag className="h-3 w-3 mr-1" />
                    标签
                  </Button>
                  <Button
                    variant="default"
                    size="sm"
                    className="h-8 px-3 text-xs"
                    onClick={(e) => {
                      e.stopPropagation();
                      refreshToken.mutate(account.email_id);
                    }}
                  >
                    <RefreshCw className="h-3 w-3 mr-1" />
                    刷新
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    className="h-8 px-3 text-xs"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm("确定要删除此账户吗？")) {
                        deleteAccount.mutate(account.email_id);
                      }
                    }}
                  >
                    <Trash className="h-3 w-3 mr-1" />
                    删除
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* 桌面端：表格设计 */}
      <div className="hidden md:block rounded-md border bg-white shadow-sm overflow-hidden overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50 hover:bg-slate-50">
              <TableHead className="w-[50px]">
                <Checkbox
                  checked={isAllSelected}
                  onCheckedChange={handleSelectAll}
                  className={cn(isIndeterminate && "data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground")}
                />
              </TableHead>
              <TableHead className="w-[50px] hidden sm:table-cell"></TableHead>
              <TableHead>Account</TableHead>
              <TableHead className="hidden md:table-cell">Tags</TableHead>
              <TableHead className="hidden lg:table-cell">Status</TableHead>
              <TableHead className="hidden lg:table-cell">Refresh Status</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.map((account, index) => (
              <TableRow 
                key={account.email_id} 
                className={cn(
                  index % 2 === 0 ? "bg-white" : "bg-slate-50/50",
                  "cursor-pointer hover:bg-blue-50/50 transition-colors"
                )}
                onClick={() => {
                  window.location.href = `/dashboard/emails?account=${encodeURIComponent(account.email_id)}`;
                }}
              >
                <TableCell onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={selectedAccounts.includes(account.email_id)}
                    onCheckedChange={(checked) => handleSelectAccount(account.email_id, checked as boolean)}
                  />
                </TableCell>
                <TableCell className="hidden sm:table-cell">
                    <Avatar className="h-8 w-8">
                        <AvatarFallback className="bg-blue-500 text-white text-xs">
                            {account.email_id.charAt(0).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                </TableCell>
                <TableCell className="font-medium">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <Avatar className="h-6 w-6 sm:hidden">
                        <AvatarFallback className="bg-blue-500 text-white text-xs">
                          {account.email_id.charAt(0).toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm break-all">{account.email_id}</span>
                    </div>
                    <span className="text-xs text-gray-400 font-mono break-all">ID: {account.client_id.substring(0, 8)}...</span>
                    <div className="flex flex-wrap gap-1.5 md:hidden mt-1">
                      {account.tags?.slice(0, 3).map(tag => (
                        <Badge key={tag} variant="secondary" className={cn("text-xs font-normal border-0", getTagColor(tag))}>
                          {tag}
                        </Badge>
                      ))}
                      {account.tags && account.tags.length > 3 && (
                        <Badge variant="secondary" className="text-xs font-normal border-0">
                          +{account.tags.length - 3}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 lg:hidden mt-1">
                      <Badge 
                        variant="outline" 
                        className={cn(
                            "font-normal text-xs",
                            account.status === "active" ? "bg-green-50 text-green-700 border-green-200" : 
                            account.status === "invalid" ? "bg-red-50 text-red-700 border-red-200" :
                            "bg-yellow-50 text-yellow-700 border-yellow-200"
                        )}
                      >
                        {account.status === "active" ? "Active" : account.status === "invalid" ? "Invalid" : "Error"}
                      </Badge>
                      {account.refresh_status === "success" && <CheckCircle className="h-3 w-3 text-green-500" />}
                      {account.refresh_status === "failed" && <XCircle className="h-3 w-3 text-red-500" />}
                      {account.refresh_status === "pending" && <Clock className="h-3 w-3 text-yellow-500" />}
                    </div>
                  </div>
                </TableCell>
                <TableCell className="hidden md:table-cell">
                  <div className="flex flex-wrap gap-1.5">
                    {account.tags?.map(tag => (
                      <Badge key={tag} variant="secondary" className={cn("text-xs font-normal border-0", getTagColor(tag))}>
                        {tag}
                      </Badge>
                    ))}
                    {(!account.tags || account.tags.length === 0) && <span className="text-xs text-gray-400 italic">No tags</span>}
                  </div>
                </TableCell>
                <TableCell className="hidden lg:table-cell">
                  <Badge 
                    variant="outline" 
                    className={cn(
                        "font-normal",
                        account.status === "active" ? "bg-green-50 text-green-700 border-green-200" : 
                        account.status === "invalid" ? "bg-red-50 text-red-700 border-red-200" :
                        "bg-yellow-50 text-yellow-700 border-yellow-200"
                    )}
                  >
                    {account.status === "active" ? "Active" : account.status === "invalid" ? "Invalid" : "Error"}
                  </Badge>
                </TableCell>
                <TableCell className="hidden lg:table-cell">
                   <div className="flex items-center gap-2">
                     {account.refresh_status === "success" && <CheckCircle className="h-4 w-4 text-green-500" />}
                     {account.refresh_status === "failed" && <XCircle className="h-4 w-4 text-red-500" />}
                     {account.refresh_status === "pending" && <Clock className="h-4 w-4 text-yellow-500" />}
                     <div className="flex flex-col">
                        <span className={cn(
                            "text-xs font-medium",
                            account.refresh_status === "success" ? "text-green-700" : 
                            account.refresh_status === "failed" ? "text-red-700" : "text-yellow-700"
                        )}>
                            {account.refresh_status === "success" ? "Success" : account.refresh_status === "failed" ? "Failed" : "Pending"}
                        </span>
                        {account.last_refresh_time && (
                        <span className="text-[10px] text-gray-400">
                            {formatDistanceToNow(new Date(account.last_refresh_time), { addSuffix: true })}
                        </span>
                        )}
                     </div>
                   </div>
                </TableCell>
                <TableCell className="text-right" onClick={(e) => e.stopPropagation()}>
                  {showAllActions ? (
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-10 px-3 min-h-[44px]"
                        asChild
                      >
                        <Link href={`/dashboard/emails?account=${account.email_id}`}>
                          <span className="mr-1.5">📧</span>
                          <span className="hidden sm:inline">查看邮件</span>
                        </Link>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-10 px-3 min-h-[44px]"
                        onClick={() => refreshToken.mutate(account.email_id)}
                      >
                        <span className="mr-1.5">🔄</span>
                        <span className="hidden sm:inline">刷新Token</span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-10 px-3 min-h-[44px]"
                        onClick={() => handleEditTags(account)}
                      >
                        <span className="mr-1.5">🏷️</span>
                        <span className="hidden sm:inline">管理标签</span>
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-10 px-3 min-h-[44px] text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() => {
                          if (confirm("确定要删除此账户吗？")) {
                            deleteAccount.mutate(account.email_id);
                          }
                        }}
                      >
                        <span className="mr-1.5">🗑️</span>
                        <span className="hidden sm:inline">删除</span>
                      </Button>
                    </div>
                  ) : (
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="h-8 w-8 p-0 min-h-[44px] min-w-[44px]">
                          <span className="sr-only">Open menu</span>
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuLabel>操作</DropdownMenuLabel>
                        <DropdownMenuItem asChild>
                           <Link href={`/dashboard/emails?account=${account.email_id}`}>
                             <span className="mr-2">📧</span> 查看邮件
                           </Link>
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => refreshToken.mutate(account.email_id)}>
                          <span className="mr-2">🔄</span> 刷新Token
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => handleEditTags(account)}>
                          <span className="mr-2">🏷️</span> 管理标签
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-red-600 focus:text-red-600 focus:bg-red-50" onClick={() => {
                            if (confirm("确定要删除此账户吗？")) {
                                deleteAccount.mutate(account.email_id);
                            }
                        }}>
                          <span className="mr-2">🗑️</span> 删除账户
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
        onOpenChange={(open) => setTagDialogState(prev => ({ ...prev, open }))}
        accountEmail={tagDialogState.email}
        initialTags={tagDialogState.tags}
      />
    </>
  );
}
