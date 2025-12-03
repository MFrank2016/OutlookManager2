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
import { Textarea } from "@/components/ui/textarea";
import { useState, useEffect } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";

// 将 Date 对象格式化为本地时间的 datetime-local 格式 (YYYY-MM-DDTHH:mm)
const formatLocalDateTime = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
};

const formSchema = z.object({
  email_accounts: z.string().min(1, "邮箱账号不能为空"),
  valid_hours: z.string().optional(),
  valid_days: z.string().optional(),
  filter_start_time: z.string().min(1, "收件开始时间必填"),
  filter_end_time: z.string().optional(),
  subject_keyword: z.string().optional(),
  sender_keyword: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface BatchShareResult {
  email_account_id: string;
  status: "success" | "failed" | "ignored";
  token?: string;
  error_message?: string;
}

interface BatchShareResponse {
  success_count: number;
  failed_count: number;
  ignored_count: number;
  results: BatchShareResult[];
}

interface BatchShareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess?: () => void;
}

export function BatchShareDialog({ open, onOpenChange, onSuccess }: BatchShareDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [batchResult, setBatchResult] = useState<BatchShareResponse | null>(null);
  const [showDetails, setShowDetails] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email_accounts: "",
      valid_hours: "24",
      valid_days: "0",
      filter_start_time: formatLocalDateTime(new Date()),
      filter_end_time: "",
      subject_keyword: "",
      sender_keyword: "",
    },
  });

  useEffect(() => {
    if (open) {
      form.reset({
        email_accounts: "",
        valid_hours: "24",
        valid_days: "0",
        filter_start_time: formatLocalDateTime(new Date()),
        filter_end_time: "",
        subject_keyword: "",
        sender_keyword: "",
      });
      setBatchResult(null);
      setShowDetails(false);
    }
  }, [open, form]);

  function onSubmit(values: FormValues) {
    setIsSubmitting(true);
    setBatchResult(null);

    // 解析邮箱账号列表（支持换行和逗号分隔）
    const emailAccounts = values.email_accounts
      .split(/[,\n]/)
      .map((email) => email.trim())
      .filter((email) => email.length > 0);

    if (emailAccounts.length === 0) {
      toast.error("请输入至少一个邮箱账号");
      setIsSubmitting(false);
      return;
    }

    const payload = {
      email_accounts: emailAccounts,
      valid_hours: values.valid_hours ? Number(values.valid_hours) : undefined,
      valid_days: values.valid_days ? Number(values.valid_days) : undefined,
      filter_start_time: new Date(values.filter_start_time).toISOString(),
      filter_end_time: values.filter_end_time ? new Date(values.filter_end_time).toISOString() : undefined,
      subject_keyword: values.subject_keyword || undefined,
      sender_keyword: values.sender_keyword || undefined,
    };

    api
      .post<BatchShareResponse>("/share/tokens/batch", payload)
      .then((response) => {
        setBatchResult(response.data);
        const { success_count, failed_count, ignored_count } = response.data;
        toast.success(
          `批量创建完成：成功 ${success_count}，失败 ${failed_count}，忽略 ${ignored_count}`
        );
        onSuccess?.();
      })
      .catch((err: { response?: { data?: { detail?: string } } }) => {
        toast.error(err.response?.data?.detail || "批量创建失败");
      })
      .finally(() => {
        setIsSubmitting(false);
      });
  }

  const handleClose = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>批量创建分享链接</DialogTitle>
          <DialogDescription>
            输入多个邮箱账号（每行一个或逗号分隔），统一设置分享参数。
          </DialogDescription>
        </DialogHeader>

        {!batchResult ? (
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="email_accounts"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>邮箱账号列表（每行一个或逗号分隔）</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="example1@email.com&#10;example2@email.com&#10;example3@email.com"
                        className="min-h-[120px] font-mono text-sm"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

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
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={handleClose}>
                  取消
                </Button>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      创建中...
                    </>
                  ) : (
                    "批量创建"
                  )}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        ) : (
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{batchResult.success_count}</div>
                <div className="text-sm text-muted-foreground">成功</div>
              </div>
              <div className="text-center p-4 bg-red-50 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{batchResult.failed_count}</div>
                <div className="text-sm text-muted-foreground">失败</div>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-600">{batchResult.ignored_count}</div>
                <div className="text-sm text-muted-foreground">忽略</div>
              </div>
            </div>

            <div>
              <Button
                variant="outline"
                className="w-full"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? (
                  <>
                    <ChevronUp className="mr-2 h-4 w-4" />
                    隐藏详细结果
                  </>
                ) : (
                  <>
                    <ChevronDown className="mr-2 h-4 w-4" />
                    查看详细结果
                  </>
                )}
              </Button>
              {showDetails && (
                <div className="mt-2 max-h-[300px] overflow-y-auto space-y-2 border rounded-lg p-4">
                  {batchResult.results.map((result, index) => (
                    <div
                      key={index}
                      className="flex items-start justify-between p-2 border-b last:border-b-0"
                    >
                      <div className="flex-1">
                        <div className="font-medium text-sm">{result.email_account_id}</div>
                        {result.status === "success" && result.token && (
                          <div className="text-xs text-muted-foreground mt-1 font-mono">
                            分享码: {result.token}
                          </div>
                        )}
                        {result.error_message && (
                          <div className="text-xs text-red-600 mt-1">{result.error_message}</div>
                        )}
                      </div>
                      <Badge
                        variant={
                          result.status === "success"
                            ? "default"
                            : result.status === "failed"
                            ? "destructive"
                            : "secondary"
                        }
                      >
                        {result.status === "success"
                          ? "成功"
                          : result.status === "failed"
                          ? "失败"
                          : "忽略"}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
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

