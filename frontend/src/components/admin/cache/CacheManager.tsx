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

  if (isLoading) return <div>Loading statistics...</div>;
  if (!stats) return <div>No data available</div>;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">DB Size</CardTitle>
            <HardDrive className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.db_size_mb.toFixed(2)} MB</div>
            <Progress value={stats.size_usage_percent} className="mt-2 h-2" />
            <p className="text-xs text-muted-foreground mt-2">
              {stats.size_usage_percent.toFixed(1)}% of {stats.max_size_mb} MB limit
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cache Hit Rate</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.hit_rate || 0}%</div>
            <p className="text-xs text-muted-foreground">Efficiency</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Email Lists</CardTitle>
            <div className="text-sm text-muted-foreground">Count</div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.emails_cache.count}</div>
            <p className="text-xs text-muted-foreground">Cached lists</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Email Details</CardTitle>
            <div className="text-sm text-muted-foreground">Count</div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.details_cache.count}</div>
            <p className="text-xs text-muted-foreground">Cached details</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-4">
        <Button 
            variant="destructive" 
            onClick={() => {
                if (confirm("Are you sure you want to clear ALL cache? This cannot be undone.")) {
                    clearAllCache.mutate();
                }
            }}
            disabled={clearAllCache.isPending}
        >
            <Trash2 className="mr-2 h-4 w-4" />
            {clearAllCache.isPending ? "Clearing..." : "Clear All Cache"}
        </Button>
        <Button 
            variant="secondary"
            onClick={() => triggerLruCleanup.mutate()}
            disabled={triggerLruCleanup.isPending}
        >
            <RefreshCw className="mr-2 h-4 w-4" />
            {triggerLruCleanup.isPending ? "Cleaning..." : "Trigger LRU Cleanup"}
        </Button>
      </div>
    </div>
  );
}

