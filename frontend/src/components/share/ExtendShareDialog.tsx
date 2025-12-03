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
import { useState, useEffect } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { ShareToken } from "@/types";

const formSchema = z.object({
  extend_type: z.enum(["duration", "datetime"] as const),
  extend_hours: z.string().optional(),
  extend_days: z.string().optional(),
  extend_to_time: z.string().optional(),
}).refine((data) => {
  if (data.extend_type === "duration") {
    return (data.extend_hours && Number(data.extend_hours) > 0) || 
           (data.extend_days && Number(data.extend_days) > 0);
  } else {
    return data.extend_to_time && data.extend_to_time.length > 0;
  }
}, {
  message: "请填写延期时间",
  path: ["extend_hours"],
});

type FormValues = z.infer<typeof formSchema>;

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

interface ExtendShareDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  token: ShareToken;
  onSuccess?: () => void;
}

export function ExtendShareDialog({ open, onOpenChange, token, onSuccess }: ExtendShareDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      extend_type: "duration",
      extend_hours: "24",
      extend_days: "0",
      extend_to_time: token.expiry_time ? isoToLocalDateTime(token.expiry_time) : formatLocalDateTime(new Date()),
    },
  });

  const extendType = form.watch("extend_type");

  useEffect(() => {
    if (open) {
      // 如果当前有过期时间，延长至指定时间的默认值应该是当前过期时间之后
      const defaultExtendToTime = token.expiry_time 
        ? isoToLocalDateTime(token.expiry_time)
        : formatLocalDateTime(new Date(Date.now() + 24 * 60 * 60 * 1000)); // 默认延长1天
      
      form.reset({
        extend_type: "duration",
        extend_hours: "24",
        extend_days: "0",
        extend_to_time: defaultExtendToTime,
      });
    }
  }, [open, token, form]);

  function onSubmit(values: FormValues) {
    setIsSubmitting(true);

    const payload: {
      extend_hours?: number;
      extend_days?: number;
      extend_to_time?: string;
    } = {};

    if (values.extend_type === "duration") {
      if (values.extend_hours && Number(values.extend_hours) > 0) {
        payload.extend_hours = Number(values.extend_hours);
      }
      if (values.extend_days && Number(values.extend_days) > 0) {
        payload.extend_days = Number(values.extend_days);
      }
    } else {
      if (values.extend_to_time) {
        payload.extend_to_time = new Date(values.extend_to_time).toISOString();
      }
    }

    api
      .post(`/share/tokens/by-token/${token.token}/extend`, payload)
      .then(() => {
        toast.success("分享码延期成功");
        onSuccess?.();
        onOpenChange(false);
      })
      .catch((err: { response?: { data?: { detail?: string } } }) => {
        toast.error(err.response?.data?.detail || "延期失败");
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
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>延期分享码</DialogTitle>
          <DialogDescription>
            为分享码 "{token.email_account_id}" 延长有效期
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="extend_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>延期方式</FormLabel>
                  <FormControl>
                    <div className="flex flex-col space-y-2">
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          id="duration"
                          name="extend_type"
                          value="duration"
                          checked={field.value === "duration"}
                          onChange={() => field.onChange("duration")}
                          className="cursor-pointer"
                        />
                        <label htmlFor="duration" className="cursor-pointer">
                          延长指定时间
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="radio"
                          id="datetime"
                          name="extend_type"
                          value="datetime"
                          checked={field.value === "datetime"}
                          onChange={() => field.onChange("datetime")}
                          className="cursor-pointer"
                        />
                        <label htmlFor="datetime" className="cursor-pointer">
                          延长至指定时间
                        </label>
                      </div>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {extendType === "duration" ? (
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="extend_hours"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>延长小时数</FormLabel>
                      <FormControl>
                        <Input type="number" min="0" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="extend_days"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>延长天数</FormLabel>
                      <FormControl>
                        <Input type="number" min="0" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            ) : (
              <FormField
                control={form.control}
                name="extend_to_time"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>延长至时间</FormLabel>
                    <FormControl>
                      <Input type="datetime-local" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={handleClose}>
                取消
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    延期中...
                  </>
                ) : (
                  "确认延期"
                )}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}

