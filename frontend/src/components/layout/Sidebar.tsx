"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import {
  LayoutDashboard,
  Mail,
  Settings,
  Book,
  Menu,
  LogOut,
  Share2
} from "lucide-react";
import { useAuthStore } from "@/store/useAuthStore";

interface SidebarProps {
  collapsed: boolean;
  toggleCollapsed: () => void;
  isMobile?: boolean;
  onNavigate?: () => void;
}

export function Sidebar({ collapsed, toggleCollapsed, isMobile = false, onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  const routes = [
    {
      label: "账户管理",
      icon: LayoutDashboard,
      href: "/dashboard",
      active: pathname === "/dashboard" || pathname.startsWith("/dashboard/accounts"),
    },
    {
      label: "邮件",
      icon: Mail,
      href: "/dashboard/emails",
      active: pathname.startsWith("/dashboard/emails"),
    },
    {
      label: "分享管理",
      icon: Share2,
      href: "/dashboard/share",
      active: pathname.startsWith("/dashboard/share"),
    },
    {
      label: "管理面板",
      icon: Settings,
      href: "/dashboard/admin",
      active: pathname.startsWith("/dashboard/admin"),
      adminOnly: true,
    },
    {
      label: "API文档",
      icon: Book,
      href: "/dashboard/api-docs",
      active: pathname.startsWith("/dashboard/api-docs"),
    },
  ];

  const handleLinkClick = () => {
    if (isMobile && onNavigate) {
      onNavigate();
    }
  };

  const activeLinkClass =
    "border border-primary/50 bg-primary/20 text-foreground shadow-[0_8px_24px_rgba(70,130,255,0.2)]";
  const idleLinkClass =
    "border border-transparent text-[color:var(--text-soft)] hover:border-border/80 hover:bg-[color:var(--surface-2)] hover:text-foreground";

  if (isMobile) {
    return (
      <nav className="space-y-1 px-2 py-4">
        {routes.map((route) => {
          if (route.adminOnly && user?.role !== "admin") return null;

          return (
            <Link
              key={route.href}
              href={route.href}
              onClick={handleLinkClick}
              className={cn(
                "interactive-lift flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                route.active ? activeLinkClass : idleLinkClass
              )}
            >
              <route.icon className="mr-3 h-5 w-5" />
              <span>{route.label}</span>
            </Link>
          );
        })}
        <div className="mt-4 border-t border-border/70 pt-4">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[color:var(--brand)] to-[color:var(--accent)] text-sm font-bold text-[color:var(--primary-foreground)]">
              {user?.username?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.username}</p>
              <p className="truncate text-xs text-[color:var(--text-faint)]">
                {user?.role === "admin" ? "管理员" : "普通用户"}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              className="text-[color:var(--text-faint)] hover:bg-red-50 hover:text-red-600"
              title="退出登录"
            >
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </nav>
    );
  }

  return (
    <div
      className={cn(
        "relative flex h-screen flex-col border-r border-border/70 bg-[color:var(--surface-0)] text-foreground transition-all duration-300 ease-in-out backdrop-blur-xl",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_0%,color-mix(in_oklch,var(--brand)_18%,transparent),transparent_42%)] opacity-90" />

      {/* Header */}
      <div className="relative flex h-16 items-center justify-between border-b border-border/70 p-4">
        {!collapsed && (
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-primary shadow-[0_0_16px_rgba(70,130,255,0.55)]" />
            <h1 className="truncate bg-gradient-to-r from-[color:var(--foreground)] to-[color:var(--brand)] bg-clip-text text-lg font-semibold tracking-wide text-transparent">
              Outlook Mgr
            </h1>
          </div>
        )}
        <div className={cn("flex items-center gap-2", collapsed ? "mx-auto" : "ml-auto")}>
          <ThemeToggle compact />
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleCollapsed}
            className="text-[color:var(--text-faint)] hover:bg-[color:var(--surface-2)] hover:text-foreground"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Nav */}
      <ScrollArea className="relative flex-1 py-4">
        <nav className="space-y-1 px-2">
          {routes.map((route) => {
            if (route.adminOnly && user?.role !== "admin") return null;

            return (
              <Link
                key={route.href}
                href={route.href}
                className={cn(
                  "interactive-lift flex items-center rounded-lg px-3 py-2 text-base font-medium transition-all duration-200",
                  route.active ? activeLinkClass : idleLinkClass,
                  collapsed && "justify-center px-0"
                )}
                title={collapsed ? route.label : undefined}
              >
                <route.icon className={cn("h-5 w-5", !collapsed && "mr-3")} />
                {!collapsed && <span>{route.label}</span>}
              </Link>
            );
          })}
        </nav>
      </ScrollArea>

      {/* User / Logout */}
      <div className="relative border-t border-border/70 p-4">
        <div className={cn("flex items-center", collapsed ? "justify-center flex-col gap-2" : "gap-3")}>
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[color:var(--brand)] to-[color:var(--accent)] text-sm font-bold text-[color:var(--primary-foreground)]">
            {user?.username?.[0]?.toUpperCase() || "U"}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-base font-medium truncate">{user?.username}</p>
              <p className="truncate text-sm text-[color:var(--text-faint)]">
                {user?.role === "admin" ? "管理员" : "普通用户"}
              </p>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={logout}
            className={cn(
              "text-[color:var(--text-faint)] hover:bg-red-50 hover:text-red-600",
              !collapsed && "ml-auto"
            )}
            title="退出登录"
          >
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </div>
  );
}
