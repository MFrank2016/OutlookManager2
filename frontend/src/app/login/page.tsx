"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useRouter } from "next/navigation";
import { ArrowRight, LockKeyhole } from "lucide-react";

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
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[linear-gradient(180deg,color-mix(in_oklch,var(--surface-0)_94%,white_6%)_0%,color-mix(in_oklch,var(--surface-1)_88%,var(--surface-0)_12%)_100%)] px-4 py-10 page-enter">
      <ThemeToggle
        compact
        className="absolute right-5 top-5 z-20 rounded-full border border-border/80 bg-[color:var(--panel)]/85 shadow-[var(--shadow-soft)] backdrop-blur-md"
      />

      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,color-mix(in_oklch,var(--surface-1)_90%,transparent),transparent_52%)]" />
        <div className="absolute left-[-10%] top-[-14%] h-[380px] w-[380px] rounded-full bg-[radial-gradient(circle,color-mix(in_oklch,var(--brand)_18%,transparent),transparent_70%)] blur-3xl" />
        <div className="absolute right-[-12%] bottom-[-18%] h-[360px] w-[360px] rounded-full bg-[radial-gradient(circle,color-mix(in_oklch,var(--accent)_18%,transparent),transparent_72%)] blur-3xl" />
        <div
          className="absolute inset-0 opacity-[0.08]"
          style={{
            backgroundImage:
              "linear-gradient(color-mix(in oklch, var(--text-faint) 16%, transparent) 1px, transparent 1px), linear-gradient(90deg, color-mix(in oklch, var(--text-faint) 16%, transparent) 1px, transparent 1px)",
            backgroundSize: "48px 48px",
          }}
        />
      </div>

      <Card className="interactive-lift relative z-10 w-full max-w-[860px] overflow-hidden rounded-[34px] border border-border/80 bg-[color:var(--panel)]/88 py-0 shadow-[var(--shadow-pop)] backdrop-blur-2xl">
        <div className="absolute inset-x-0 top-0 h-[2px] bg-[linear-gradient(90deg,transparent,color-mix(in_oklch,var(--brand)_56%,transparent),transparent)]" />

        <CardHeader className="space-y-4 px-8 pb-1 pt-10 sm:px-14">
          <div className="flex flex-col items-center justify-center gap-4 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-[20px] border border-border/80 bg-[linear-gradient(180deg,color-mix(in_oklch,var(--surface-1)_96%,transparent),color-mix(in_oklch,var(--surface-2)_88%,transparent))] shadow-[0_12px_28px_color-mix(in_oklch,var(--brand)_26%,transparent)]">
              <LockKeyhole className="h-4.5 w-4.5 text-[color:var(--brand)]" />
            </div>
            <CardTitle className="text-[2rem] font-semibold tracking-[-0.04em] text-foreground">
              Outlook Manager
            </CardTitle>
          </div>
        </CardHeader>

        <CardContent className="px-8 pb-10 pt-4 sm:px-14">
          <div className="rounded-[26px] border border-border/75 bg-[color:color-mix(in_oklch,var(--surface-1)_86%,transparent)] p-7 shadow-[inset_0_1px_0_color-mix(in_oklch,var(--surface-1)_88%,transparent),0_16px_34px_color-mix(in_oklch,var(--brand)_10%,transparent)] sm:p-8">
            <div className="mx-auto max-w-[560px]">
              <Form {...form}>
                <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-7">
                  <FormField
                    control={form.control}
                    name="username"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-[13px] font-medium text-[color:var(--text-soft)]">
                          用户名
                        </FormLabel>
                        <FormControl>
                          <Input
                            placeholder="请输入管理员用户名"
                            className="h-12 rounded-[16px] border-[color:var(--border)] bg-[color:color-mix(in_oklch,var(--surface-1)_90%,transparent)] px-4 text-[15px] text-foreground shadow-[inset_0_1px_0_color-mix(in_oklch,var(--surface-1)_92%,transparent)] placeholder:text-[color:var(--text-faint)] focus:border-[color:var(--brand)] focus:bg-[color:var(--surface-1)] focus:ring-4 focus:ring-[color:color-mix(in_oklch,var(--brand)_18%,transparent)]"
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
                        <FormLabel className="text-[13px] font-medium text-[color:var(--text-soft)]">
                          密码
                        </FormLabel>
                        <FormControl>
                          <Input
                            type="password"
                            placeholder="请输入登录密码"
                            className="h-12 rounded-[16px] border-[color:var(--border)] bg-[color:color-mix(in_oklch,var(--surface-1)_90%,transparent)] px-4 text-[15px] text-foreground shadow-[inset_0_1px_0_color-mix(in_oklch,var(--surface-1)_92%,transparent)] placeholder:text-[color:var(--text-faint)] focus:border-[color:var(--brand)] focus:bg-[color:var(--surface-1)] focus:ring-4 focus:ring-[color:color-mix(in_oklch,var(--brand)_18%,transparent)]"
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <Button
                    type="submit"
                    className="group mt-6 h-12 w-full rounded-[16px] bg-[linear-gradient(135deg,color-mix(in_oklch,var(--brand)_92%,oklch(0.56_0.15_236)_8%),color-mix(in_oklch,var(--primary)_80%,oklch(0.47_0.15_256)_20%))] text-[15px] font-semibold text-primary-foreground shadow-[0_14px_28px_color-mix(in_oklch,var(--brand)_34%,transparent)] transition-all duration-200 hover:translate-y-[-1px] hover:shadow-[0_18px_34px_color-mix(in_oklch,var(--brand)_42%,transparent)] hover:brightness-[1.02]"
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
