"use client";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useState, useEffect, useMemo } from "react";
import { Copy, Check } from "lucide-react";
import api from "@/lib/api";
import { toast } from "sonner";
import { ShareToken } from "@/types";
import { useConfigs } from "@/hooks/useAdmin";
import { generateShareLink, getShareDomainFromConfigs } from "@/lib/shareUtils";

// 将 Date 对象格式化为本地时间的 datetime-local 格式 (YYYY-MM-DDTHH:mm)
const formatLocalDateTime = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
};

// 将 ISO 8601 时间字符串转换为本地时间的 datetime-local 格式
const isoToLocalDateTime = (isoString: string): string => {
  const date = new Date(isoString);
  return formatLocalDateTime(date);
};

const formSchema = z.object({
  valid_hours: z.string().optional(),
  valid_days: z.string().optional(),
  filter_start_time: z.string().min(1, "收件开始时间必填"),
  filter_end_time: z.string().optional(),
  subject_keyword: z.string().optional(),
  sender_keyword: z.string().optional(),
  is_active: z.boolean().optional(),
  max_emails: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;
// .refine... removed because when editing we might not change validity

interface ShareTokenDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  emailAccount?: string;
  tokenToEdit?: ShareToken;
  onSuccess?: () => void;
}

export function ShareTokenDialog({ open, onOpenChange, emailAccount, tokenToEdit, onSuccess }: ShareTokenDialogProps) {
  const [shareLink, setShareLink] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [copied, setCopied] = useState(false);
  const isEditing = !!tokenToEdit;

  // 获取系统配置（用于分享页域名）
  const { data: configsData } = useConfigs();
  const shareDomain = getShareDomainFromConfigs(configsData?.configs);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      valid_hours: "24",
      valid_days: "0",
      filter_start_time: formatLocalDateTime(new Date()),
      filter_end_time: "",
      subject_keyword: "",
      sender_keyword: "",
      is_active: true,
      max_emails: "10",
    },
  });

  // Compute share link from tokenToEdit
  const computedShareLink = useMemo(() => {
    if (tokenToEdit) {
      return generateShareLink(tokenToEdit.token, shareDomain || undefined);
    }
    return null;
  }, [tokenToEdit, shareDomain]);

  useEffect(() => {
    if (open) {
        if (tokenToEdit) {
            // Reset form with token values
            form.reset({
                valid_hours: "0", // We don't reverse calculate validity for now
                valid_days: "0",
                filter_start_time: isoToLocalDateTime(tokenToEdit.start_time),
                filter_end_time: tokenToEdit.end_time ? isoToLocalDateTime(tokenToEdit.end_time) : "",
                subject_keyword: tokenToEdit.subject_keyword || "",
                sender_keyword: tokenToEdit.sender_keyword || "",
                is_active: tokenToEdit.is_active,
                max_emails: String((tokenToEdit as any).max_emails || 10),
            });
        } else {
            // Reset to defaults
            form.reset({
                valid_hours: "24",
                valid_days: "0",
                filter_start_time: formatLocalDateTime(new Date()),
                filter_end_time: "",
                subject_keyword: "",
                sender_keyword: "",
                is_active: true,
                max_emails: "10",
            });
        }
    }
  }, [open, tokenToEdit, form]);

  useEffect(() => {
    setShareLink(computedShareLink);
  }, [computedShareLink]);

  function onSubmit(values: FormValues) {
    setIsSubmitting(true);
    
    if (isEditing && tokenToEdit) {
        // Update logic
        const payload = {
            start_time: new Date(values.filter_start_time).toISOString(),
            end_time: values.filter_end_time ? new Date(values.filter_end_time).toISOString() : null,
            subject_keyword: values.subject_keyword || null,
            sender_keyword: values.sender_keyword || null,
            is_active: values.is_active,
            // We don't update expiry_time based on hours/days here to avoid confusion, 
            // unless we add specific fields for "extend validity". 
            // For now, just update filters and active status.
        };

        api.put(`/share/tokens/by-token/${tokenToEdit.token}`, payload)
            .then(() => {
                toast.success("分享码已更新");
                onSuccess?.();
                onOpenChange(false);
            })
            .catch((err: { response?: { data?: { detail?: string } } }) => {
                toast.error(err.response?.data?.detail || "更新失败");
            })
            .finally(() => {
                setIsSubmitting(false);
            });

    } else {
        // Create logic
        if (!emailAccount) {
            toast.error("缺少邮箱账户");
            setIsSubmitting(false);
            return;
        }

        const payload = {
            email_account_id: emailAccount,
            valid_hours: values.valid_hours ? Number(values.valid_hours) : undefined,
            valid_days: values.valid_days ? Number(values.valid_days) : undefined,
            filter_start_time: new Date(values.filter_start_time).toISOString(),
            filter_end_time: values.filter_end_time ? new Date(values.filter_end_time).toISOString() : undefined,
            subject_keyword: values.subject_keyword || undefined,
            sender_keyword: values.sender_keyword || undefined,
            max_emails: values.max_emails ? Number(values.max_emails) : 10,
        };

        api.post("/share/tokens", payload)
        .then((response: { data: { token: string } }) => {
            const token = response.data.token;
            const link = generateShareLink(token, shareDomain || undefined);
            setShareLink(link);
            toast.success("分享码创建成功");
            onSuccess?.();
        })
        .catch((err: { response?: { data?: { detail?: string } } }) => {
            toast.error(err.response?.data?.detail || "创建失败");
        })
        .finally(() => {
            setIsSubmitting(false);
        });
    }
  }

  const handleCopy = () => {
    if (shareLink) {
      navigator.clipboard.writeText(shareLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      toast.success("链接已复制");
    }
  };

  const handleClose = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{isEditing ? "编辑分享链接" : `创建分享链接 - ${emailAccount}`}</DialogTitle>
          <DialogDescription>
            {isEditing ? "修改分享链接的筛选规则和状态。" : "生成一个临时访问链接，仅包含符合筛选条件的邮件。"}
          </DialogDescription>
        </DialogHeader>

        {!shareLink || isEditing ? (
            <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                {!isEditing && (
                    <div className="grid grid-cols-2 gap-4">
                        <FormField
                        control={form.control}
                        name="valid_hours"
                        render={({ field }) => (
                            <FormItem>
                            <FormLabel>有效期 (小时)</FormLabel>
                            <FormControl>
                                <Input type="number" min="0" {...field} />
                            </FormControl>
                            <FormMessage />
                            </FormItem>
                        )}
                        />
                        <FormField
                        control={form.control}
                        name="valid_days"
                        render={({ field }) => (
                            <FormItem>
                            <FormLabel>有效期 (天)</FormLabel>
                            <FormControl>
                                <Input type="number" min="0" {...field} />
                            </FormControl>
                            <FormMessage />
                            </FormItem>
                        )}
                        />
                    </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                    <FormField
                    control={form.control}
                    name="filter_start_time"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>收件开始时间 (必填)</FormLabel>
                        <FormControl>
                            <Input type="datetime-local" {...field} />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />

                    <FormField
                    control={form.control}
                    name="filter_end_time"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>收件结束时间 (可选)</FormLabel>
                        <FormControl>
                            <Input type="datetime-local" {...field} />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <FormField
                    control={form.control}
                    name="subject_keyword"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>主题关键词</FormLabel>
                        <FormControl>
                            <Input placeholder="关键词..." {...field} />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                    <FormField
                    control={form.control}
                    name="sender_keyword"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>发件人关键词</FormLabel>
                        <FormControl>
                            <Input placeholder="例如: @google.com" {...field} />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                    <FormField
                    control={form.control}
                    name="max_emails"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>最多返回邮件数</FormLabel>
                        <FormControl>
                            <Input type="number" min="1" max="100" placeholder="10" {...field} />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                </div>

                <DialogFooter>
                    <Button type="button" variant="outline" onClick={handleClose}>取消</Button>
                    <Button type="submit" disabled={isSubmitting}>
                        {isSubmitting ? "保存" : (isEditing ? "更新" : "生成链接")}
                    </Button>
                </DialogFooter>
            </form>
            </Form>
        ) : (
            <div className="space-y-4 py-4">
                <div className="flex items-center space-x-2">
                    <Input value={shareLink} readOnly />
                    <Button size="icon" onClick={handleCopy}>
                        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </Button>
                </div>
                <div className="text-sm text-muted-foreground text-center">
                    此链接允许访问符合条件的邮件，请妥善保管。
                </div>
                <DialogFooter>
                    <Button onClick={handleClose}>完成</Button>
                </DialogFooter>
            </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

