"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import {
  ArrowRight,
  LockKeyhole,
} from "lucide-react";

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
      // 1. Login to get token
      const loginResponse = await api.post("/auth/login", {
        username: values.username,
        password: values.password,
      });
      const token = loginResponse.data.access_token;
      
      // Temporarily set token in localStorage so subsequent request has it (interceptor)
      // although store.login handles it, we need it immediately for the next call if store update is async/batched
      // Actually the interceptor reads from localStorage directly.
      localStorage.setItem("auth_token", token);

      // 2. Fetch user info
      const userResponse = await api.get("/auth/me");
      const user = userResponse.data;

      // 3. Update store
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
      <ThemeToggle compact className="absolute right-5 top-5 z-20 rounded-full border border-white/80 bg-white/80 shadow-[0_8px_24px_rgba(148,163,184,0.14)] backdrop-blur-md" />
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.92),transparent_50%)]" />
        <div className="absolute left-[-10%] top-[-14%] h-[380px] w-[380px] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.08),transparent_70%)] blur-3xl" />
        <div className="absolute right-[-12%] bottom-[-18%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle,rgba(96,165,250,0.08),transparent_72%)] blur-3xl" />
        <div className="absolute inset-0 opacity-[0.08]" style={{backgroundImage:"linear-gradient(rgba(148,163,184,0.12) 1px, transparent 1px), linear-gradient(90deg, rgba(148,163,184,0.12) 1px, transparent 1px)", backgroundSize:"48px 48px"}} />
      </div>

      <Card className="interactive-lift relative z-10 w-full max-w-[860px] overflow-hidden rounded-[34px] border border-white/85 bg-white/82 py-0 shadow-[0_28px_68px_rgba(15,23,42,0.1)] backdrop-blur-2xl">
        <div className="absolute inset-x-0 top-0 h-[2px] bg-[linear-gradient(90deg,rgba(255,255,255,0),rgba(59,130,246,0.52),rgba(255,255,255,0))]" />
        <CardHeader className="space-y-4 px-8 pb-1 pt-10 sm:px-14">
          <div className="flex flex-col items-center justify-center gap-4 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-[20px] border border-white/90 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(243,247,252,0.92))] shadow-[0_12px_28px_rgba(59,130,246,0.12)]">
              <LockKeyhole className="h-4.5 w-4.5 text-sky-600" />
            </div>
            <CardTitle className="text-[2rem] font-semibold tracking-[-0.04em] text-slate-900">
              Outlook Manager
            </CardTitle>
          </div>
        </CardHeader>

        <CardContent className="px-8 pb-10 pt-4 sm:px-14">
          <div className="rounded-[26px] border border-white/85 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(248,251,255,0.86))] p-7 shadow-[inset_0_1px_0_rgba(255,255,255,0.96),0_16px_34px_rgba(148,163,184,0.08)] sm:p-8">
            <div className="mx-auto max-w-[560px]">
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-7">
                <FormField
                  control={form.control}
                  name="username"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-[13px] font-medium text-slate-700">用户名</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="请输入管理员用户名"
                          className="h-12 rounded-[16px] border-slate-200/90 bg-white/94 px-4 text-[15px] shadow-[inset_0_1px_0_rgba(255,255,255,0.96)] transition-all duration-200 placeholder:text-slate-400 focus:border-sky-300 focus:bg-white focus:ring-4 focus:ring-sky-100/70"
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
                    <FormItem>
                      <FormLabel className="text-[13px] font-medium text-slate-700">密码</FormLabel>
                      <FormControl>
                        <Input
                          type="password"
                          placeholder="请输入登录密码"
                          className="h-12 rounded-[16px] border-slate-200/90 bg-white/94 px-4 text-[15px] shadow-[inset_0_1px_0_rgba(255,255,255,0.96)] transition-all duration-200 placeholder:text-slate-400 focus:border-sky-300 focus:bg-white focus:ring-4 focus:ring-sky-100/70"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <Button
                  type="submit"
                  className="group mt-6 h-12 w-full rounded-[16px] bg-[linear-gradient(135deg,#1d9bf0,#2563eb)] text-[15px] font-semibold text-white shadow-[0_14px_28px_rgba(37,99,235,0.22)] transition-all duration-200 hover:translate-y-[-1px] hover:shadow-[0_18px_34px_rgba(37,99,235,0.26)] hover:brightness-[1.02]"
                  disabled={isLoading}
                >
                  <span className="inline-flex items-center gap-2">
                    {isLoading ? "登录中..." : "进入控制台"}
                    {!isLoading && <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5" />}
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
