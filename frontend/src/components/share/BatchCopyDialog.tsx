"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { ShareToken } from "@/types";
import { format } from "date-fns";
import { useConfigs } from "@/hooks/useAdmin";
import { generateShareLink, getShareDomainFromConfigs } from "@/lib/shareUtils";

interface BatchCopyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  tokens: ShareToken[];
  selectedTokens?: ShareToken[];
}

type CopyField = "account" | "token" | "link" | "expiry" | "created_at" | "start_time" | "end_time" | "subject_keyword" | "sender_keyword";

const FIELD_LABELS: Record<CopyField, string> = {
  account: "账户",
  token: "分享码",
  link: "分享链接",
  expiry: "有效期",
  created_at: "创建时间",
  start_time: "开始时间",
  end_time: "结束时间",
  subject_keyword: "主题关键词",
  sender_keyword: "发件人关键词",
};

export function BatchCopyDialog({
  open,
  onOpenChange,
  tokens,
  selectedTokens = [],
}: BatchCopyDialogProps) {
  const [delimiter, setDelimiter] = useState<string>("tab");
  const [customDelimiter, setCustomDelimiter] = useState<string>("");
  const [selectedFields, setSelectedFields] = useState<CopyField[]>([
    "account",
    "token",
    "link",
  ]);
  const [rowSelection, setRowSelection] = useState<"current" | "selected">("current");

  // 获取系统配置（用于分享页域名）
  const { data: configsData } = useConfigs();
  const shareDomain = getShareDomainFromConfigs(configsData?.configs);

  // 当 selectedTokens 变为空时，重置 rowSelection 为 "current"
  useEffect(() => {
    if (selectedTokens.length === 0 && rowSelection === "selected") {
      setRowSelection("current");
    }
  }, [selectedTokens.length, rowSelection]);

  // 当对话框打开时，如果 selectedTokens 为空，确保 rowSelection 是 "current"
  useEffect(() => {
    if (open && selectedTokens.length === 0) {
      setRowSelection("current");
    }
  }, [open, selectedTokens.length]);

  const getDelimiterValue = () => {
    switch (delimiter) {
      case "comma":
        return ",";
      case "tab":
        return "\t";
      case "space":
        return " ";
      case "custom":
        return customDelimiter;
      default:
        return "\t";
    }
  };

  const getFieldValue = (token: ShareToken, field: CopyField): string => {
    switch (field) {
      case "account":
        return token.email_account_id;
      case "token":
        return token.token;
      case "link":
        return generateShareLink(token.token, shareDomain || undefined);
      case "expiry":
        return token.expiry_time
          ? format(new Date(token.expiry_time), "yyyy-MM-dd HH:mm")
          : "永久有效";
      case "created_at":
        return format(new Date(token.created_at), "yyyy-MM-dd HH:mm");
      case "start_time":
        return format(new Date(token.start_time), "yyyy-MM-dd HH:mm");
      case "end_time":
        return token.end_time
          ? format(new Date(token.end_time), "yyyy-MM-dd HH:mm")
          : "";
      case "subject_keyword":
        return token.subject_keyword || "";
      case "sender_keyword":
        return token.sender_keyword || "";
      default:
        return "";
    }
  };

  const handleCopy = () => {
    let tokensToCopy: ShareToken[];

    if (rowSelection === "selected") {
      if (selectedTokens.length === 0) {
        toast.error("没有选中的行，请先选择要复制的行");
        return;
      }
      tokensToCopy = selectedTokens;
    } else {
      tokensToCopy = tokens;
    }

    if (tokensToCopy.length === 0) {
      toast.error("没有可复制的数据");
      return;
    }

    if (selectedFields.length === 0) {
      toast.error("请至少选择一个字段");
      return;
    }

    const delimiterValue = getDelimiterValue();
    const lines = tokensToCopy.map((token) => {
      return selectedFields.map((field) => getFieldValue(token, field)).join(delimiterValue);
    });

    const textToCopy = lines.join("\n");
    navigator.clipboard.writeText(textToCopy);
    toast.success(`已复制 ${tokensToCopy.length} 行数据`);
  };

  const toggleField = (field: CopyField) => {
    setSelectedFields((prev) =>
      prev.includes(field)
        ? prev.filter((f) => f !== field)
        : [...prev, field]
    );
  };

  const handleClose = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>批量复制</DialogTitle>
          <DialogDescription>
            配置复制选项，将选中的数据复制到剪贴板
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          <div className="space-y-2">
            <Label>分隔符</Label>
            <Select value={delimiter} onValueChange={setDelimiter}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="tab">制表符 (Tab)</SelectItem>
                <SelectItem value="comma">逗号 (,)</SelectItem>
                <SelectItem value="space">空格</SelectItem>
                <SelectItem value="custom">自定义</SelectItem>
              </SelectContent>
            </Select>
            {delimiter === "custom" && (
              <Input
                placeholder="输入自定义分隔符"
                value={customDelimiter}
                onChange={(e) => setCustomDelimiter(e.target.value)}
                className="mt-2"
              />
            )}
          </div>

          <div className="space-y-2">
            <Label>复制字段</Label>
            <div className="grid grid-cols-2 gap-2 border rounded-lg p-3 max-h-[200px] overflow-y-auto">
              {Object.entries(FIELD_LABELS).map(([field, label]) => (
                <div key={field} className="flex items-center space-x-2">
                  <Checkbox
                    id={`field-${field}`}
                    checked={selectedFields.includes(field as CopyField)}
                    onCheckedChange={() => toggleField(field as CopyField)}
                  />
                  <Label
                    htmlFor={`field-${field}`}
                    className="text-sm font-normal cursor-pointer"
                  >
                    {label}
                  </Label>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <Label>数据行选择</Label>
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <input
                  type="radio"
                  id="row-current"
                  name="row-selection"
                  value="current"
                  checked={rowSelection === "current"}
                  onChange={(e) => setRowSelection(e.target.value as typeof rowSelection)}
                  className="cursor-pointer"
                />
                <Label htmlFor="row-current" className="cursor-pointer">
                  当前页 ({tokens.length} 条)
                </Label>
              </div>
              {selectedTokens.length > 0 && (
                <div className="flex items-center space-x-2">
                  <input
                    type="radio"
                    id="row-selected"
                    name="row-selection"
                    value="selected"
                    checked={rowSelection === "selected"}
                    onChange={(e) => setRowSelection(e.target.value as typeof rowSelection)}
                    className="cursor-pointer"
                  />
                  <Label htmlFor="row-selected" className="cursor-pointer">
                    已选中 ({selectedTokens.length} 条)
                  </Label>
                </div>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={handleClose}>
            取消
          </Button>
          <Button type="button" onClick={handleCopy}>
            复制
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

