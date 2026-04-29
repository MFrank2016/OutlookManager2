import { Database, HardDrive, KeyRound, Settings2, Users2 } from "lucide-react";

import { TabsList, TabsTrigger } from "@/components/ui/tabs";

const MODULES = [
  {
    value: "tables",
    label: "数据表管理",
    icon: Database,
  },
  {
    value: "users",
    label: "用户管理",
    icon: Users2,
  },
  {
    value: "config",
    label: "系统配置",
    icon: Settings2,
  },
  {
    value: "cache",
    label: "缓存管理",
    icon: HardDrive,
  },
  {
    value: "verification-rules",
    label: "验证码规则",
    icon: KeyRound,
  },
] as const;

export function AdminModuleTabs() {
  return (
    <TabsList className="grid h-auto w-full grid-cols-2 gap-2 rounded-2xl bg-[color:var(--surface-1)]/80 p-2 md:grid-cols-5">
      {MODULES.map((module) => {
        const Icon = module.icon;
        return (
          <TabsTrigger
            key={module.value}
            value={module.value}
            className="min-h-[52px] flex-col gap-1.5 rounded-xl px-3 py-3 text-xs font-medium md:text-sm"
          >
            <Icon className="h-4 w-4" />
            <span>{module.label}</span>
          </TabsTrigger>
        );
      })}
    </TabsList>
  );
}
