"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { Sidebar } from "@/components/layout/Sidebar";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

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
  }, [isAuthenticated, router, fetchUser]);

  return (
    <div className="flex h-screen flex-col overflow-hidden page-enter">
      {/* Mobile: Top Navigation Bar */}
      <div className="md:hidden border-b border-border/70 bg-[color:var(--surface-0)] backdrop-blur-xl">
        <div className="flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-primary shadow-[0_0_16px_rgba(70,130,255,0.55)]" />
            <h1 className="bg-gradient-to-r from-[color:var(--foreground)] to-[color:var(--brand)] bg-clip-text text-lg font-semibold tracking-wide text-transparent">
              Outlook Mgr
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle compact />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="interactive-lift rounded-lg border border-border/70 bg-[color:var(--surface-2)] p-2 text-foreground"
              aria-label="Toggle menu"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>
        {mobileMenuOpen && (
          <div className="page-enter border-t border-border/70 bg-[color:var(--surface-1)]">
            <Sidebar
              collapsed={false}
              toggleCollapsed={() => {}}
              isMobile={true}
              onNavigate={() => setMobileMenuOpen(false)}
            />
          </div>
        )}
      </div>

      {/* Desktop: Sidebar */}
      <div className="hidden md:flex h-full">
        <Sidebar
          collapsed={sidebarCollapsed}
          toggleCollapsed={() => setSidebarCollapsed(!sidebarCollapsed)}
          isMobile={false}
        />
        <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 md:p-6">
            <div className="panel-surface soft-grid-bg relative min-h-full overflow-hidden p-3 md:p-4">
              {children}
            </div>
          </div>
        </main>
      </div>

      {/* Mobile: Main Content */}
      <div className="md:hidden flex-1 overflow-hidden">
        <main className="h-full overflow-y-auto p-2">
          <div className="panel-surface soft-grid-bg min-h-full p-2">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
