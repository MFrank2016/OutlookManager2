"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/useAuthStore";
import { Sidebar } from "@/components/layout/Sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const router = useRouter();
  const { isAuthenticated, fetchUser } = useAuthStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const storedToken = localStorage.getItem("auth_token");
    if (!storedToken) {
      router.push("/login");
    } else if (!isAuthenticated) {
      fetchUser().catch(() => router.push("/login"));
    }
  }, [isAuthenticated, router, fetchUser]);

  if (!mounted) {
    return null; 
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900 overflow-hidden">
      {/* Mobile: Top Navigation Bar */}
      <div className="md:hidden bg-slate-900 text-white border-b border-slate-800">
        <div className="flex items-center justify-between p-4 h-16">
          <h1 className="text-xl font-bold text-blue-400">Outlook Mgr</h1>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 rounded-md hover:bg-slate-800 transition-colors"
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
        {mobileMenuOpen && (
          <div className="border-t border-slate-800">
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
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>
      </main>
      </div>

      {/* Mobile: Main Content */}
      <div className="md:hidden flex-1 overflow-hidden">
        <main className="h-full overflow-y-auto px-0">
          {children}
        </main>
      </div>
    </div>
  );
}

