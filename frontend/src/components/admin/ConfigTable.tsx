"use client";

import { useConfigs, useDeleteConfig } from "@/hooks/useAdmin";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState, useMemo } from "react";
import { Edit, Trash2, Search, Plus, Check } from "lucide-react";
import { ConfigDialog } from "./ConfigDialog";
import { ConfigItem } from "@/types";
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
import { toast } from "sonner";

export function ConfigTable() {
  const { data, isLoading } = useConfigs();
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteKey, setDeleteKey] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const deleteConfig = useDeleteConfig();

  // 过滤配置列表
  const filteredConfigs = useMemo(() => {
    if (!data?.configs) return [];
    if (!searchQuery.trim()) return data.configs;

    const query = searchQuery.toLowerCase();
    return data.configs.filter(
      (config) =>
        config.key.toLowerCase().includes(query) ||
        config.value.toLowerCase().includes(query) ||
        (config.description?.toLowerCase().includes(query) ?? false)
    );
  }, [data?.configs, searchQuery]);

  const handleDelete = () => {
    if (deleteKey) {
      deleteConfig.mutate(deleteKey, {
        onSuccess: () => {
          setDeleteKey(null);
        },
      });
    }
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(key);
    toast.success("已复制到剪贴板");
    setTimeout(() => setCopiedKey(null), 2000);
  };

  if (isLoading) return <div className="p-4">加载配置中...</div>;

  return (
    <div className="space-y-4">
      {/* 搜索框和新增按钮 */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="搜索配置键、值或描述..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        <ConfigDialog />
      </div>

      {/* 配置表格 */}
      <div className="rounded-md border bg-white">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>配置项</TableHead>
              <TableHead>值</TableHead>
              <TableHead>描述</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredConfigs.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-gray-500 py-8">
                  {searchQuery ? "未找到匹配的配置" : "暂无配置项"}
                </TableCell>
              </TableRow>
            ) : (
              filteredConfigs.map((config) => (
                <ConfigRow
                  key={config.key}
                  config={config}
                  onDelete={() => setDeleteKey(config.key)}
                  onCopy={handleCopy}
                  copiedKey={copiedKey}
                />
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* 删除确认对话框 */}
      <AlertDialog open={!!deleteKey} onOpenChange={(open) => !open && setDeleteKey(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>确认删除</AlertDialogTitle>
            <AlertDialogDescription>
              确定要删除配置项 <strong>{deleteKey}</strong> 吗？此操作不可恢复。
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
              disabled={deleteConfig.isPending}
            >
              {deleteConfig.isPending ? "删除中..." : "删除"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function ConfigRow({
  config,
  onDelete,
  onCopy,
  copiedKey,
}: {
  config: ConfigItem;
  onDelete: () => void;
  onCopy: (text: string, key: string) => void;
  copiedKey: string | null;
}) {
  const isCopied = copiedKey === config.key;

  return (
    <TableRow>
      <TableCell
        className="font-medium cursor-pointer select-none hover:bg-gray-50"
        onDoubleClick={() => onCopy(config.key, config.key)}
        title="双击复制配置键"
      >
        {config.key}
      </TableCell>
      <TableCell
        className="cursor-pointer select-none hover:bg-gray-50 max-w-md break-words"
        onDoubleClick={() => onCopy(config.value, config.key)}
        title="双击复制配置值"
      >
        <div className="flex items-center gap-2">
          <span className="flex-1">{config.value}</span>
          {isCopied && <Check className="h-4 w-4 text-green-600" />}
        </div>
      </TableCell>
      <TableCell
        className="text-gray-500 cursor-pointer select-none hover:bg-gray-50"
        onDoubleClick={() => config.description && onCopy(config.description, config.key)}
        title={config.description ? "双击复制描述" : undefined}
      >
        {config.description || "-"}
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-2">
          <ConfigDialog
            config={config}
            trigger={
              <Button size="sm" variant="outline">
                <Edit className="h-4 w-4 mr-1" />
                编辑
              </Button>
            }
          />
          <Button size="sm" variant="outline" onClick={onDelete}>
            <Trash2 className="h-4 w-4 mr-1" />
            删除
          </Button>
        </div>
      </TableCell>
    </TableRow>
  );
}
