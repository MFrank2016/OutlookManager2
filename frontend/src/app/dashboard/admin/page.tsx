"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UsersTable } from "@/components/admin/UsersTable";
import { ConfigTable } from "@/components/admin/ConfigTable";
import { TablesManager } from "@/components/admin/tables/TablesManager";
import { CacheManager } from "@/components/admin/cache/CacheManager";

export default function AdminPage() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <Tabs defaultValue="tables" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4 h-12">
          <TabsTrigger value="tables" className="text-lg font-semibold data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-50 data-[state=active]:to-indigo-50 transition-all duration-200">
            📊 数据表管理
          </TabsTrigger>
          <TabsTrigger value="users" className="text-lg font-semibold data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-50 data-[state=active]:to-indigo-50 transition-all duration-200">
            👥 用户管理
          </TabsTrigger>
          <TabsTrigger value="config" className="text-lg font-semibold data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-50 data-[state=active]:to-indigo-50 transition-all duration-200">
            ⚙️ 系统配置
          </TabsTrigger>
          <TabsTrigger value="cache" className="text-lg font-semibold data-[state=active]:bg-gradient-to-r data-[state=active]:from-blue-50 data-[state=active]:to-indigo-50 transition-all duration-200">
            💾 缓存管理
          </TabsTrigger>
        </TabsList>
        <TabsContent value="tables" className="space-y-4 animate-in fade-in duration-300">
          <TablesManager />
        </TabsContent>
        <TabsContent value="users" className="space-y-4 animate-in fade-in duration-300">
          <UsersTable />
        </TabsContent>
        <TabsContent value="config" className="space-y-4 animate-in fade-in duration-300">
          <ConfigTable />
        </TabsContent>
        <TabsContent value="cache" className="space-y-4 animate-in fade-in duration-300">
          <CacheManager />
        </TabsContent>
      </Tabs>
    </div>
  );
}

