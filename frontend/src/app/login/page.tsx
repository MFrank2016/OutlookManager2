"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { ArrowRight, Mail } from "lucide-react";

import api from "@/lib/api";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/store/useAuthStore";
import { toast } from "sonner";

const formSchema = z.object({
  username: z.string().min(1, {
    message: "用户名必填",
  }),
  password: z.string().min(1, {
    message: "密码必填",
  }),
});

export default function LoginPage() {
  const router = useRouter();
  const login = useAuthStore((state) => state.login);
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      password: "",
    },
  });

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsLoading(true);
    try {
      const loginResponse = await api.post("/auth/login", {
        username: values.username,
        password: values.password,
      });
      const token = loginResponse.data.access_token;

      localStorage.setItem("auth_token", token);

      const userResponse = await api.get("/auth/me");
      const user = userResponse.data;

      login(token, user);

      toast.success("登录成功");
      router.push("/dashboard");
    } catch (error: unknown) {
      console.error(error);
      const msg =
        error && typeof error === "object" && "response" in error
          ? ((error as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
            "登录失败，请检查您的凭据。")
          : "登录失败，请检查您的凭据。";
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[linear-gradient(180deg,#f7f9fc_0%,#eef3f9_100%)] px-4 py-10 page-enter">
      <ThemeToggle
        compact
        className="absolute right-5 top-5 z-20 rounded-full border border-white/80 bg-white/80 shadow-[0_8px_24px_rgba(148,163,184,0.14)] backdrop-blur-md"
      />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.92),transparent_50%)]" />
        <div className="absolute left-[-8%] top-[-12%] h-[300px] w-[300px] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.05),transparent_70%)] blur-3xl" />
        <div className="absolute right-[-10%] bottom-[-16%] h-[280px] w-[280px] rounded-full bg-[radial-gradient(circle,rgba(96,165,250,0.05),transparent_72%)] blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.05]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(148,163,184,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.12) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
      </div>

      <Card className="interactive-lift relative z-10 flex w-full max-w-[840px] flex-col overflow-hidden rounded-[32px] border border-white/95 bg-white/92 py-0 shadow-[0_22px_52px_rgba(15,23,42,0.08)] backdrop-blur-xl sm:min-h-[520px]">
        <div className="absolute inset-x-0 top-0 h-px bg-[linear-gradient(90deg,rgba(255,255,255,0),rgba(148,163,184,0.35),rgba(255,255,255,0))]" />

        <CardHeader className="space-y-4 px-8 pb-2 pt-11 sm:px-14 sm:pt-12">
          <div className="flex flex-col items-center justify-center gap-4 text-center">
            <div className="relative flex h-[76px] w-[76px] items-center justify-center rounded-[24px] border border-sky-100/90 bg-[linear-gradient(180deg,rgba(219,234,254,0.98),rgba(186,230,253,0.95))] shadow-[0_14px_32px_rgba(37,99,235,0.14)]">
              <div className="absolute inset-[6px] rounded-[18px] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.34),rgba(255,255,255,0.18))]" />
              <div className="absolute top-[11px] h-[5px] w-[28px] rounded-full bg-white/55" />
              <div className="relative z-10 flex h-[42px] w-[48px] overflow-hidden rounded-[14px] border border-sky-200/70 bg-white/90 shadow-[0_8px_16px_rgba(37,99,235,0.12)]">
                <div className="flex w-[18px] items-center justify-center bg-[linear-gradient(180deg,#0ea5e9,#2563eb)] text-[11px] font-semibold tracking-[-0.04em] text-white">
                  O
                </div>
                <div className="flex flex-1 items-center justify-center bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(239,246,255,0.94))]">
                  <Mail className="h-[16px] w-[16px] text-sky-700" />
                </div>
              </div>
            </div>
            <CardTitle className="text-[1.85rem] font-semibold tracking-[-0.04em] text-slate-900">
              Outlook Manager
            </CardTitle>
          </div>
        </CardHeader>

        <CardContent className="flex flex-1 items-center justify-center px-8 pb-10 pt-4 sm:px-14 sm:pb-12 sm:pt-6">
          <div className="mx-auto w-full max-w-[500px] rounded-[24px] border border-slate-200/70 bg-white/96 p-7 shadow-[inset_0_1px_0_rgba(255,255,255,0.96),0_12px_26px_rgba(15,23,42,0.04)] sm:p-8">
            <div className="mx-auto flex w-full max-w-[420px] flex-col items-center">
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="w-full space-y-7">
                  <FormField
                    control={form.control}
                    name="username"
                    render={({ field }) => (
                      <FormItem className="mx-auto w-full max-w-[420px] space-y-3">
                        <FormLabel className="block w-full text-left text-[13px] font-medium text-slate-700">
                          用户名
                        </FormLabel>
                        <FormControl>
                          <Input
                            placeholder="请输入管理员用户名"
                            className="h-12 rounded-[16px] border-slate-200 bg-white px-4 text-[15px] shadow-[inset_0_1px_0_rgba(255,255,255,0.96)] transition-all duration-200 placeholder:text-slate-400 focus:border-sky-400 focus:bg-white focus-visible:ring-2 focus-visible:ring-sky-500/20"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem className="mx-auto w-full max-w-[420px] space-y-3">
                        <FormLabel className="block w-full text-left text-[13px] font-medium text-slate-700">
                          密码
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="password"
                            placeholder="请输入登录密码"
                            className="h-12 rounded-[16px] border-slate-200 bg-white px-4 text-[15px] shadow-[inset_0_1px_0_rgba(255,255,255,0.96)] transition-all duration-200 placeholder:text-slate-400 focus:border-sky-400 focus:bg-white focus-visible:ring-2 focus-visible:ring-sky-500/20"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button
                    type="submit"
                    className="group mx-auto mt-1 flex h-12 w-full max-w-[420px] rounded-[15px] bg-[linear-gradient(135deg,#2383e2,#2563eb)] text-[15px] font-semibold text-white shadow-[0_10px_20px_rgba(37,99,235,0.18)] transition-all duration-200 hover:translate-y-[-1px] hover:shadow-[0_14px_24px_rgba(37,99,235,0.22)] hover:brightness-[1.01]"
                    disabled={isLoading}
                  >
                    <span className="inline-flex items-center gap-2">
                      {isLoading ? "登录中..." : "进入控制台"}
                      {!isLoading && (
                        <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />
                      )}
                    </span>
                  </Button>
                </form>
              </Form>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
