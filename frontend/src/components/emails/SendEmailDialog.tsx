"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { AlertCircle, Send } from "lucide-react";

import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { useSendEmail } from "@/hooks/useEmails";
import { getAccountSendSupport } from "@/lib/microsoftAccess";
import { Account } from "@/types";

const sendEmailSchema = z.object({
  recipient: z.string().email(),
  subject: z.string().min(1, "主题必填"),
  body: z.string().min(1, "正文必填"),
});

export function SendEmailDialog({ account }: { account: Account | null }) {
    const [open, setOpen] = useState(false);
    const sendEmail = useSendEmail();
    const sendCapability = getAccountSendSupport(account);
    const accountEmail = account?.email_id ?? null;

    const form = useForm<z.infer<typeof sendEmailSchema>>({
        resolver: zodResolver(sendEmailSchema),
        defaultValues: {
            recipient: "",
            subject: "",
            body: "",
        }
    });

    const onSubmit = (values: z.infer<typeof sendEmailSchema>) => {
        if (!accountEmail || !sendCapability.canSend) return;
        sendEmail.mutate({
            account: accountEmail,
            to: values.recipient,
            subject: values.subject,
            body: values.body
        }, {
            onSuccess: () => {
                setOpen(false);
                form.reset();
            }
        });
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <div className="flex flex-col gap-1.5">
                <DialogTrigger asChild>
                    <Button
                        variant="outline"
                        size="sm"
                        className="h-8 px-3"
                        disabled={!account?.email_id || !sendCapability.canSend}
                        title={sendCapability.reason}
                    >
                        <Send className="mr-1.5 h-3.5 w-3.5" />
                        <span className="text-xs md:text-sm">撰写</span>
                    </Button>
                </DialogTrigger>
                {account?.email_id && !sendCapability.canSend ? (
                    <div className="inline-flex items-center gap-1.5 text-[11px] font-medium text-amber-700">
                        <AlertCircle className="h-3.5 w-3.5" />
                        <span>{sendCapability.reason}</span>
                    </div>
                ) : null}
            </div>
            <DialogContent className="sm:max-w-[640px]">
                <DialogHeader>
                    <DialogTitle>发送邮件 ({accountEmail})</DialogTitle>
                    <DialogDescription>
                        从当前账户直接发送邮件，适合验证链路、回复测试或临时通知。
                    </DialogDescription>
                </DialogHeader>
                <Form {...form}>
                    <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                            control={form.control}
                            name="recipient"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>收件人</FormLabel>
                                    <FormControl>
                                        <Input placeholder="recipient@example.com" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="subject"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>主题</FormLabel>
                                    <FormControl>
                                        <Input placeholder="主题" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <FormField
                            control={form.control}
                            name="body"
                            render={({ field }) => (
                                <FormItem>
                                    <FormLabel>消息</FormLabel>
                                    <FormControl>
                                        <Textarea placeholder="在此输入您的消息..." className="min-h-[200px]" {...field} />
                                    </FormControl>
                                    <FormMessage />
                                </FormItem>
                            )}
                        />
                        <DialogFooter>
                            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                                取消
                            </Button>
                            <Button type="submit" disabled={sendEmail.isPending || !sendCapability.canSend}>
                                {sendEmail.isPending ? "发送中..." : "发送邮件"}
                            </Button>
                        </DialogFooter>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}
