"use client";

import { useCacheStats, useClearAllCache, useTriggerLruCleanup } from "@/hooks/useAdmin";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Trash2, RefreshCw, Database, HardDrive } from "lucide-react";

export function CacheManager() {
  const { data: stats, isLoading } = useCacheStats();
  const clearAllCache = useClearAllCache();
  const triggerLruCleanup = useTriggerLruCleanup();

  if (isLoading) return <div>加载统计信息中...</div>;
  if (!stats) return <div>无可用数据</div>;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">数据库大小</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.db_size_mb.toFixed(2)} MB</div>
            <Progress value={stats.size_usage_percent} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-2">
              已使用 {stats.size_usage_percent.toFixed(1)}% / {stats.max_size_mb} MB 限制
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">缓存命中率</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.hit_rate || 0}%</div>
            <p className="text-xs text-muted-foreground">效率</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">邮件列表</CardTitle>
            <div className="text-sm text-muted-foreground">数量</div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.emails_cache.count}</div>
            <p className="text-xs text-muted-foreground">已缓存列表</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">邮件详情</CardTitle>
            <div className="text-sm text-muted-foreground">数量</div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.details_cache.count}</div>
            <p className="text-xs text-muted-foreground">已缓存详情</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-4">
        <Button 
            variant="destructive" 
            onClick={() => {
                if (confirm("确定要清空所有缓存吗？此操作无法撤销。")) {
                    clearAllCache.mutate();
                }
            }}
            disabled={clearAllCache.isPending}
        >
            <Trash2 className="mr-2 h-4 w-4" />
            {clearAllCache.isPending ? "清空中..." : "清空所有缓存"}
        </Button>
        <Button 
            variant="secondary"
            onClick={() => triggerLruCleanup.mutate()}
            disabled={triggerLruCleanup.isPending}
        >
            <RefreshCw className="mr-2 h-4 w-4" />
            {triggerLruCleanup.isPending ? "清理中..." : "触发LRU清理"}
        </Button>
      </div>
    </div>
  );
}

