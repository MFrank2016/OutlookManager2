"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { useSendEmail } from "@/hooks/useEmails";
import { Send } from "lucide-react";

const sendEmailSchema = z.object({
  recipient: z.string().email(),
  subject: z.string().min(1, "主题必填"),
  body: z.string().min(1, "正文必填"),
});

export function SendEmailDialog({ account }: { account: string | null }) {
    const [open, setOpen] = useState(false);
    const sendEmail = useSendEmail();

    const form = useForm<z.infer<typeof sendEmailSchema>>({
        resolver: zodResolver(sendEmailSchema),
        defaultValues: {
            recipient: "",
            subject: "",
            body: "",
        }
    });

    const onSubmit = (values: z.infer<typeof sendEmailSchema>) => {
        if (!account) return;
        sendEmail.mutate({
            account,
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
            <DialogTrigger asChild>
                <Button 
                    variant="outline"
                    size="sm"
                    className="h-8 px-3"
                    disabled={!account}
                >
                    <Send className="mr-1.5 h-3.5 w-3.5" />
                    <span className="text-xs md:text-sm">撰写</span>
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[600px]">
                <DialogHeader>
                    <DialogTitle>发送邮件 ({account})</DialogTitle>
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
                        <div className="flex justify-end">
                            <Button type="submit" disabled={sendEmail.isPending}>
                                {sendEmail.isPending ? "发送中..." : "发送邮件"}
                            </Button>
                        </div>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>
    );
}

