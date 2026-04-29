"use client";

import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { useRouter } from "next/navigation";

import { Sidebar } from "@/components/layout/Sidebar";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/useAuthStore";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const router = useRouter();
  const { isAuthenticated, fetchUser } = useAuthStore();

  useEffect(() => {
    const storedToken = localStorage.getItem("auth_token");
    if (!storedToken) {
      router.push("/login");
    } else if (!isAuthenticated) {
      fetchUser().catch(() => router.push("/login"));
    }
  }, [fetchUser, isAuthenticated, router]);

  const closeMobileMenu = () => {
    setMobileMenuOpen(false);
  };

  return (
    <div className="page-enter flex h-dvh overflow-hidden bg-[color:var(--surface-0)] text-foreground">
      <button
        type="button"
        aria-label="关闭菜单"
        onClick={closeMobileMenu}
        className={cn(
          "fixed inset-0 z-40 bg-black/45 backdrop-blur-sm transition-opacity md:hidden",
          mobileMenuOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
      />

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-72 transition-all duration-300 md:static md:z-auto md:translate-x-0",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          sidebarCollapsed && "md:w-20"
        )}
      >
        <Sidebar
          collapsed={sidebarCollapsed}
          toggleCollapsed={() => setSidebarCollapsed((value) => !value)}
          isMobile={false}
          mobileMode={mobileMenuOpen}
          onNavigate={closeMobileMenu}
        />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-border/70 bg-[color:var(--surface-0)]/88 backdrop-blur-xl">
          <div className="flex h-16 items-center justify-between px-3 md:px-6">
            <div className="flex items-center gap-2 md:gap-3">
              <Button
                type="button"
                size="icon"
                variant="ghost"
                onClick={() => setMobileMenuOpen((value) => !value)}
                className="h-9 w-9 border border-border/70 bg-[color:var(--surface-2)] text-[color:var(--text-soft)] hover:bg-[color:var(--surface-3)] hover:text-foreground md:hidden"
                aria-label={mobileMenuOpen ? "关闭菜单" : "打开菜单"}
              >
                {mobileMenuOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
              </Button>

              <div>
                <p className="text-[10px] uppercase tracking-[0.18em] text-[color:var(--text-faint)]">
                  OutlookManager2
                </p>
                <p className="text-sm font-medium md:text-base">管理控制台</p>
              </div>
            </div>

            <p className="hidden items-center gap-2 text-xs text-[color:var(--text-soft)] md:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              App Shell
            </p>
          </div>
        </header>

        <ScrollArea className="flex-1">
          <div className="min-h-full p-3 md:p-6">
            <main className="panel-surface soft-grid-bg min-h-full overflow-hidden p-3 md:p-4">
              {children}
            </main>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}
