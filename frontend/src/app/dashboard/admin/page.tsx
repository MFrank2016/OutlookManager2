"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { UsersTable } from "@/components/admin/UsersTable";
import { ConfigTable } from "@/components/admin/ConfigTable";
import { TablesManager } from "@/components/admin/tables/TablesManager";
import { CacheManager } from "@/components/admin/cache/CacheManager";

export default function AdminPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Admin Panel</h1>
      
      <Tabs defaultValue="tables" className="space-y-4">
        <TabsList>
          <TabsTrigger value="tables">Tables</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="config">Config</TabsTrigger>
          <TabsTrigger value="cache">Cache</TabsTrigger>
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

