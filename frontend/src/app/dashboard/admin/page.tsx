"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UsersTable } from "@/components/admin/UsersTable";
import { ConfigTable } from "@/components/admin/ConfigTable";
import { TablesManager } from "@/components/admin/tables/TablesManager";
import { CacheManager } from "@/components/admin/cache/CacheManager";

export default function AdminPage() {
  return (
    <div className="page-enter space-y-6">
      <Tabs defaultValue="tables" className="space-y-4">
        <TabsList className="panel-surface grid h-12 w-full grid-cols-4">
          <TabsTrigger value="tables" className="text-lg font-semibold transition-all duration-200 data-[state=active]:border data-[state=active]:border-primary/45 data-[state=active]:bg-primary/20">
            📊 数据表管理
          </TabsTrigger>
          <TabsTrigger value="users" className="text-lg font-semibold transition-all duration-200 data-[state=active]:border data-[state=active]:border-primary/45 data-[state=active]:bg-primary/20">
            👥 用户管理
          </TabsTrigger>
          <TabsTrigger value="config" className="text-lg font-semibold transition-all duration-200 data-[state=active]:border data-[state=active]:border-primary/45 data-[state=active]:bg-primary/20">
            ⚙️ 系统配置
          </TabsTrigger>
          <TabsTrigger value="cache" className="text-lg font-semibold transition-all duration-200 data-[state=active]:border data-[state=active]:border-primary/45 data-[state=active]:bg-primary/20">
            💾 缓存管理
          </TabsTrigger>
        </TabsList>
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
      </Tabs>
    </div>
  );
}
