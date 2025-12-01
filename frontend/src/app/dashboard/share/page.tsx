"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
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
import { Trash, Copy, Loader2, Edit, Plus } from "lucide-react";
import { toast } from "sonner";
import { formatDistanceToNow, format } from "date-fns";
import { ShareTokenDialog } from "@/components/share/ShareTokenDialog";
import { ShareToken } from "@/types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAccounts } from "@/hooks/useAccounts";

export default function ShareManagementPage() {
  const queryClient = useQueryClient();
  const [page] = useState(1);
  const [editToken, setEditToken] = useState<ShareToken | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<string>("");

  // 获取账户列表（使用现有的hook）
  const { data: accountsResponse } = useAccounts({
    page: 1,
    page_size: 100
  });
  
  const accountsData = accountsResponse?.accounts || [];

  const { data: tokens, isLoading } = useQuery({
    queryKey: ["share-tokens", page],
    queryFn: async () => {
      const res = await api.get<ShareToken[]>("/share/tokens", {
        params: { page, page_size: 50 }
      });
      return res.data;
    }
  });

  const deleteToken = useMutation({
    mutationFn: async (token: string) => {
      await api.delete(`/share/tokens/by-token/${token}`);
    },
    onSuccess: () => {
      toast.success("分享码已删除");
      queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || "删除失败");
    }
  });

  const handleCopyLink = (token: string) => {
    const link = `${window.location.origin}/shared/${token}`;
    navigator.clipboard.writeText(link);
    toast.success("链接已复制");
  };

  if (isLoading) {
    return <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-gray-400" /></div>;
  }

  return (
    <div className="space-y-6 px-0 md:px-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">分享管理</h1>
        <div className="flex gap-2">
          {accountsData && accountsData.length > 0 && (
            <>
              <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="选择邮箱账户" />
                </SelectTrigger>
                <SelectContent>
                  {accountsData.map((account: { email: string }) => (
                    <SelectItem key={account.email} value={account.email}>
                      {account.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                onClick={() => {
                  if (!selectedAccount) {
                    toast.error("请先选择邮箱账户");
                    return;
                  }
                  setIsCreateDialogOpen(true);
                }}
                className="gap-2"
              >
                <Plus className="h-4 w-4" />
                创建分享
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="rounded-md border bg-white shadow-sm overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-slate-50">
              <TableHead>账户</TableHead>
              <TableHead>有效期</TableHead>
              <TableHead>筛选规则</TableHead>
              <TableHead>创建时间</TableHead>
              <TableHead>状态</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!tokens || tokens.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-muted-foreground h-24">
                  暂无分享链接
                </TableCell>
              </TableRow>
            ) : (
              tokens.map((token) => {
                const isExpired = token.expiry_time && new Date(token.expiry_time) < new Date();
                return (
                  <TableRow key={token.id}>
                    <TableCell className="font-medium">{token.email_account_id}</TableCell>
                    <TableCell>
                      {token.expiry_time ? (
                        <div className="flex flex-col">
                          <span>{format(new Date(token.expiry_time), "yyyy-MM-dd HH:mm")}</span>
                          <span className="text-xs text-muted-foreground">
                            {isExpired ? "已过期" : formatDistanceToNow(new Date(token.expiry_time), { addSuffix: true })}
                          </span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">永久有效</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col gap-1 text-xs">
                        <div>开始: {format(new Date(token.start_time), "yyyy-MM-dd HH:mm")}</div>
                        {token.end_time && <div>结束: {format(new Date(token.end_time), "yyyy-MM-dd HH:mm")}</div>}
                        {token.subject_keyword && <div>主题: {token.subject_keyword}</div>}
                        {token.sender_keyword && <div>发件人: {token.sender_keyword}</div>}
                      </div>
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                      {format(new Date(token.created_at), "MM-dd HH:mm")}
                    </TableCell>
                    <TableCell>
                      <Badge variant={token.is_active && !isExpired ? "default" : "secondary"}>
                        {token.is_active ? (isExpired ? "已过期" : "有效") : "已禁用"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            setEditToken(token);
                            setIsEditDialogOpen(true);
                          }}
                          title="编辑"
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleCopyLink(token.token)}
                          title="复制链接"
                        >
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => {
                            if (window.confirm("确定要删除此分享链接吗？")) {
                              deleteToken.mutate(token.token);
                            }
                          }}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          title="删除"
                        >
                          <Trash className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>

      <ShareTokenDialog
        open={isEditDialogOpen}
        onOpenChange={(open) => {
            setIsEditDialogOpen(open);
            if (!open) setEditToken(null);
        }}
        tokenToEdit={editToken || undefined}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
          setEditToken(null);
        }}
      />
      
      <ShareTokenDialog
        open={isCreateDialogOpen}
        onOpenChange={(open) => {
            setIsCreateDialogOpen(open);
            if (!open) setSelectedAccount("");
        }}
        emailAccount={selectedAccount}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
          setIsCreateDialogOpen(false);
          setSelectedAccount("");
        }}
      />
    </div>
  );
}

