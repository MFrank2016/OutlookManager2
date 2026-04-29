"use client";

import { useState } from "react";
import { useUsers, useDeleteUser } from "@/hooks/useAdmin";
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
import { Input } from "@/components/ui/input";
import { DataEmptyState } from "@/components/ui/data-empty-state";
import { DataLoadingState } from "@/components/ui/data-loading-state";
import { FilterToolbar } from "@/components/ui/filter-toolbar";
import { PageSection } from "@/components/layout/PageSection";
import { Trash, Edit, Search, ShieldAlert, ShieldCheck, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { UserDialog } from "./UserDialog";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export function UsersTable() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  
  const { data, isLoading } = useUsers({ 
      page, 
      page_size: 20,
      search 
  });
  const deleteUser = useDeleteUser();

  if (isLoading) {
    return (
      <DataLoadingState
        title="正在加载用户"
        description="用户列表、角色与状态信息正在同步。"
        rows={2}
      />
    );
  }

  return (
    <PageSection
      title="用户管理"
      description="管理后台用户、角色权限与启停状态。"
      contentClassName="space-y-4"
    >
      <FilterToolbar
        leading={
          <div className="relative min-w-[200px] max-w-md">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
                placeholder="搜索用户..." 
                className="pl-9" 
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                }}
            />
          </div>
        }
        trailing={<UserDialog />}
      />

      <div className="panel-surface overflow-hidden rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[50px]"></TableHead>
              <TableHead>用户</TableHead>
              <TableHead>角色</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>最后登录</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.users.length === 0 && (
                <TableRow>
                    <TableCell colSpan={6} className="p-0">
                        <DataEmptyState
                          title="未找到用户"
                          description={search ? "试试调整搜索关键词，或清空搜索后重试。" : "当前还没有可管理的用户记录。"}
                          className="min-h-[200px] rounded-none border-0"
                        />
                    </TableCell>
                </TableRow>
            )}
            {data?.users.map((user, index) => (
              <TableRow key={user.id} className={index % 2 === 0 ? "bg-white" : "bg-slate-50/50"}>
                <TableCell>
                    <Avatar className="h-8 w-8">
                        <AvatarFallback className={cn(
                            "text-xs text-white",
                            user.role === "admin"
                              ? "bg-gradient-to-br from-[color:var(--brand)] to-[color:var(--accent)] text-[color:var(--primary-foreground)]"
                              : "bg-slate-500"
                        )}>
                            {user.username.charAt(0).toUpperCase()}
                        </AvatarFallback>
                    </Avatar>
                </TableCell>
                <TableCell className="font-medium">
                    <div className="flex flex-col">
                        <span className="text-sm text-slate-900">{user.username}</span>
                        <span className="text-xs text-slate-500">{user.email || "无邮箱"}</span>
                    </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={cn(
                      "font-normal capitalize",
                      user.role === 'admin' 
                        ? "bg-blue-50 text-blue-700 border-blue-200" 
                        : "bg-slate-50 text-slate-700 border-slate-200"
                  )}>
                    {user.role === 'admin' && <ShieldAlert className="w-3 h-3 mr-1" />}
                    {user.role === 'user' && <ShieldCheck className="w-3 h-3 mr-1" />}
                    {user.role === 'admin' ? '管理员' : '普通用户'}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className={cn(
                      "font-normal",
                      user.is_active 
                        ? "bg-green-50 text-green-700 border-green-200" 
                        : "bg-red-50 text-red-700 border-red-200"
                  )}>
                    {user.is_active ? "激活" : "禁用"}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex items-center text-xs text-slate-500">
                    <Clock className="w-3 h-3 mr-1" />
                    {user.last_login
                        ? formatDistanceToNow(new Date(user.last_login), { addSuffix: true })
                        : "从未登录"}
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex justify-end gap-2">
                    <UserDialog 
                        user={user} 
                        trigger={
                            <Button variant="ghost" size="icon" className="hover:bg-blue-50/50 hover:text-blue-600">
                                <Edit className="h-4 w-4 text-slate-600" />
                            </Button>
                        } 
                    />
                    <Button
                      variant="ghost"
                      size="icon"
                      className="hover:bg-red-50 hover:text-red-600"
                      onClick={() => {
                        if (confirm(`确定要删除用户 ${user.username} 吗？`)) {
                          deleteUser.mutate(user.username);
                        }
                      }}
                      disabled={user.role === "admin"} 
                    >
                      <Trash className="h-4 w-4 text-slate-400" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between pt-2">
            <div className="text-sm text-muted-foreground">
                总计: {data.total_users} 个用户
            </div>
            <div className="flex gap-2">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                >
                    上一页
                </Button>
                <span className="flex items-center px-2 text-sm font-medium">
                    第 {page} 页，共 {data.total_pages} 页
                </span>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
                    disabled={page === data.total_pages}
                >
                    下一页
                </Button>
            </div>
        </div>
      )}
    </PageSection>
  );
}
