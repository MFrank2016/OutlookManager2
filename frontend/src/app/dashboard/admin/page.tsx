"use client";

import { CacheManager } from "@/components/admin/cache/CacheManager";
import { ConfigTable } from "@/components/admin/ConfigTable";
import { AdminModuleTabs } from "@/components/admin/AdminModuleTabs";
import { VerificationRulesTab } from "@/components/admin/verification-rules/VerificationRulesTab";
import { TablesManager } from "@/components/admin/tables/TablesManager";
import { UsersTable } from "@/components/admin/UsersTable";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageIntro } from "@/components/layout/PageIntro";
import { Tabs, TabsContent } from "@/components/ui/tabs";

export default function AdminPage() {
  return (
    <div className="page-enter space-y-4">
      <PageHeader
        title="管理面板"
        description="集中处理数据表、用户、配置、缓存与验证码规则等后台能力。"
      />

      <PageIntro description="切换不同控制模块时，共享同一套专业化控制台结构与主题表现。">
        <div className="grid gap-2 text-xs text-[color:var(--text-soft)] sm:grid-cols-3 xl:grid-cols-5">
          <div className="rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-2">数据与结构：表记录、字段与 SQL</div>
          <div className="rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-2">用户权限：账户、角色、启停状态</div>
          <div className="rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-2">系统配置：运行参数与业务键值</div>
          <div className="rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-2">缓存策略：容量、命中率与清理操作</div>
          <div className="rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-2">验证码规则：匹配、提取与测试</div>
        </div>
      </PageIntro>

      <Tabs defaultValue="tables" className="space-y-4">
        <AdminModuleTabs />
        <TabsContent value="tables" className="space-y-4">
          <TablesManager />
        </TabsContent>
        <TabsContent value="users" className="space-y-4">
          <UsersTable />
        </TabsContent>
        <TabsContent value="config" className="space-y-4">
          <ConfigTable />
        </TabsContent>
        <TabsContent value="cache" className="space-y-4">
          <CacheManager />
        </TabsContent>
        <TabsContent value="verification-rules" className="space-y-4">
          <VerificationRulesTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
