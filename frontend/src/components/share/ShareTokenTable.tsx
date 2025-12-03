"use client";

import { memo } from "react";
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
import { Checkbox } from "@/components/ui/checkbox";
import { Trash, Copy, Edit, Clock } from "lucide-react";
import { toast } from "sonner";
import { formatDistanceToNow, format } from "date-fns";
import { ShareToken } from "@/types";
import { generateShareLink } from "@/lib/shareUtils";

interface ShareTokenTableProps {
  tokens: ShareToken[] | undefined;
  selectedTokens: Set<number>;
  onToggleSelect: (tokenId: number, checked: boolean) => void;
  onToggleSelectAll: (checked: boolean) => void;
  onEdit: (token: ShareToken) => void;
  onExtend: (token: ShareToken) => void;
  onDelete: (token: string) => void;
  shareDomain?: string;
}

export const ShareTokenTable = memo(function ShareTokenTable({
  tokens,
  selectedTokens,
  onToggleSelect,
  onToggleSelectAll,
  onDelete,
  onEdit,
  onExtend,
  shareDomain,
}: ShareTokenTableProps) {
  const handleDoubleClickCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label}已复制到剪贴板`);
  };

  const handleCopyLink = (token: string) => {
    const link = generateShareLink(token, shareDomain);
    navigator.clipboard.writeText(link);
    toast.success("链接已复制");
  };

  return (
    <div className="rounded-md border bg-white shadow-sm overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-slate-50">
            <TableHead className="w-[50px]">
              <Checkbox
                checked={tokens && tokens.length > 0 && selectedTokens.size === tokens.length}
                onCheckedChange={onToggleSelectAll}
              />
            </TableHead>
            <TableHead>账户</TableHead>
            <TableHead>Token</TableHead>
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
              <TableCell colSpan={8} className="text-center text-muted-foreground h-24">
                暂无分享链接
              </TableCell>
            </TableRow>
          ) : (
            tokens.map((token) => {
              const isExpired = token.expiry_time && new Date(token.expiry_time) < new Date();
              const isSelected = selectedTokens.has(token.id);
              return (
                <TableRow key={token.id}>
                  <TableCell>
                    <Checkbox
                      checked={isSelected}
                      onCheckedChange={(checked) => onToggleSelect(token.id, checked as boolean)}
                    />
                  </TableCell>
                  <TableCell 
                    className="font-medium cursor-pointer select-none hover:bg-gray-50"
                    onDoubleClick={() => handleDoubleClickCopy(token.email_account_id, "账户")}
                    title="双击复制账户"
                  >
                    {token.email_account_id}
                  </TableCell>
                  <TableCell 
                    className="font-mono text-sm cursor-pointer select-none hover:bg-gray-50"
                    onDoubleClick={() => handleDoubleClickCopy(token.token, "Token")}
                    title="双击复制Token"
                  >
                    {token.token}
                  </TableCell>
                  <TableCell 
                    className="cursor-pointer select-none hover:bg-gray-50"
                    onDoubleClick={() => {
                      const expiryText = token.expiry_time 
                        ? format(new Date(token.expiry_time), "yyyy-MM-dd HH:mm")
                        : "永久有效";
                      handleDoubleClickCopy(expiryText, "有效期");
                    }}
                    title="双击复制有效期"
                  >
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
                  <TableCell 
                    className="cursor-pointer select-none hover:bg-gray-50"
                    onDoubleClick={() => {
                      const filterText = [
                        `开始: ${format(new Date(token.start_time), "yyyy-MM-dd HH:mm")}`,
                        token.end_time && `结束: ${format(new Date(token.end_time), "yyyy-MM-dd HH:mm")}`,
                        token.subject_keyword && `主题: ${token.subject_keyword}`,
                        token.sender_keyword && `发件人: ${token.sender_keyword}`
                      ].filter(Boolean).join('\n');
                      handleDoubleClickCopy(filterText, "筛选规则");
                    }}
                    title="双击复制筛选规则"
                  >
                    <div className="flex flex-col gap-1 text-xs">
                      <div>开始: {format(new Date(token.start_time), "yyyy-MM-dd HH:mm")}</div>
                      {token.end_time && <div>结束: {format(new Date(token.end_time), "yyyy-MM-dd HH:mm")}</div>}
                      {token.subject_keyword && <div>主题: {token.subject_keyword}</div>}
                      {token.sender_keyword && <div>发件人: {token.sender_keyword}</div>}
                    </div>
                  </TableCell>
                  <TableCell 
                    className="text-muted-foreground text-sm cursor-pointer select-none hover:bg-gray-50"
                    onDoubleClick={() => handleDoubleClickCopy(format(new Date(token.created_at), "yyyy-MM-dd HH:mm"), "创建时间")}
                    title="双击复制创建时间"
                  >
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
                        onClick={() => onExtend(token)}
                        title="延期"
                      >
                        <Clock className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => onEdit(token)}
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
                            onDelete(token.token);
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
  );
});

