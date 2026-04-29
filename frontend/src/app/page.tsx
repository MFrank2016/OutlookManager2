"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, token } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && token) {
      router.push("/dashboard");
    } else {
      router.push("/login");
    }
  }, [isAuthenticated, token, router]);

  return (
    <div className="page-enter flex min-h-screen items-center justify-center bg-[color:var(--surface-0)] px-4">
      <div className="panel-surface flex flex-col items-center gap-4 px-8 py-10 text-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-muted border-t-primary"></div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-foreground">正在准备控制台</p>
          <p className="text-sm text-[color:var(--text-soft)]">正在根据登录状态跳转到管理后台或登录页。</p>
        </div>
      </div>
    </div>
  );
}
