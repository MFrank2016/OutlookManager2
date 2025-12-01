"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
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
                "flex items-center px-3 py-2 rounded-md transition-colors text-sm font-medium",
                route.active
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )}
            >
              <route.icon className="h-5 w-5 mr-3" />
              <span>{route.label}</span>
            </Link>
          );
        })}
        <div className="pt-4 mt-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold shrink-0">
              {user?.username?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.username}</p>
              <p className="text-xs text-slate-400 truncate">{user?.role === 'admin' ? '管理员' : '普通用户'}</p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={logout}
              className="text-slate-400 hover:text-red-400 hover:bg-slate-800"
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
        "relative flex flex-col h-screen bg-slate-900 text-white transition-all duration-300 ease-in-out border-r border-slate-800",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 h-16 border-b border-slate-800">
        {!collapsed && (
          <h1 className="text-xl font-bold truncate text-blue-400">Outlook Mgr</h1>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleCollapsed}
          className={cn(
            "text-slate-400 hover:text-white hover:bg-slate-800",
            collapsed ? "mx-auto" : "ml-auto"
          )}
        >
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      {/* Nav */}
      <ScrollArea className="flex-1 py-4">
        <nav className="space-y-1 px-2">
          {routes.map((route) => {
            if (route.adminOnly && user?.role !== "admin") return null;
            
            return (
              <Link
                key={route.href}
                href={route.href}
                className={cn(
                  "flex items-center px-3 py-2 rounded-md transition-colors text-sm font-medium",
                  route.active
                    ? "bg-blue-600 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white",
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
      <div className="p-4 border-t border-slate-800">
        <div className={cn("flex items-center", collapsed ? "justify-center flex-col gap-2" : "gap-3")}>
          <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold shrink-0">
            {user?.username?.[0]?.toUpperCase() || "U"}
          </div>
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.username}</p>
              <p className="text-xs text-slate-400 truncate">{user?.role === 'admin' ? '管理员' : '普通用户'}</p>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={logout}
            className={cn(
              "text-slate-400 hover:text-red-400 hover:bg-slate-800",
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

