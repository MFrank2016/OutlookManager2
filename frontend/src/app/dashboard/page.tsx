"use client";

import { useState } from "react";
import { useAccounts } from "@/hooks/useAccounts";
import { AccountsTable } from "@/components/accounts/AccountsTable";
import { AddAccountDialog } from "@/components/accounts/AddAccountDialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChevronLeft, ChevronRight, Search, PackagePlus, Filter, RefreshCw } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { toast } from "sonner";
import { useQueryClient } from "@tanstack/react-query";
import { cn } from "@/lib/utils";

export default function DashboardPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [tagSearch, setTagSearch] = useState("");
  const [refreshStatus, setRefreshStatus] = useState<string | undefined>(undefined);
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [isBatchRefreshing, setIsBatchRefreshing] = useState(false);
  const queryClient = useQueryClient();
  
  const { data, isLoading } = useAccounts({ 
      page, 
      page_size: 10, 
      email_search: search,
      tag_search: tagSearch,
      refresh_status: refreshStatus
  });

  const handleBatchRefresh = async () => {
    if (selectedAccounts.length === 0) {
      toast.warning("请先选择要刷新的账户");
      return;
    }

    if (!confirm(`确定要批量刷新 ${selectedAccounts.length} 个账户的Token吗？`)) {
      return;
    }

    setIsBatchRefreshing(true);
    try {
      const response = await api.post("/accounts/batch-refresh-tokens", {
        email_ids: selectedAccounts
      });
      
      const result = response.data;
      toast.success(`批量刷新完成！成功: ${result.success_count}, 失败: ${result.failed_count}`);
      
      // 刷新账户列表
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      
      // 清空选择
      setSelectedAccounts([]);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "批量刷新失败");
    } finally {
      setIsBatchRefreshing(false);
    }
  };

  return (
    <div className="space-y-6 px-0 md:px-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">Accounts</h1>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button asChild variant="secondary" className="flex-1 sm:flex-initial min-h-[44px]">
            <Link href="/dashboard/accounts/batch">
              <PackagePlus className="mr-2 h-4 w-4" /> Batch Add
            </Link>
          </Button>
          <AddAccountDialog />
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 bg-white p-4 rounded-lg shadow-sm border">
        <div className="relative flex-1 w-full">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
            <Input 
                placeholder="Search emails..." 
                className="pl-9 min-h-[44px]" 
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                }}
            />
        </div>
        <div className="relative flex-1 w-full">
            <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
            <Input 
                placeholder="Filter by tags..." 
                className="pl-9 min-h-[44px]" 
                value={tagSearch}
                onChange={(e) => {
                    setTagSearch(e.target.value);
                    setPage(1);
                }}
            />
        </div>
        <div className="w-full sm:w-[180px]">
            <Select value={refreshStatus} onValueChange={(val) => { setRefreshStatus(val === "all" ? undefined : val); setPage(1); }}>
                <SelectTrigger className="min-h-[44px]">
                    <SelectValue placeholder="Filter Status" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="success">Success</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                </SelectContent>
            </Select>
        </div>
      </div>

      {selectedAccounts.length > 0 && (
        <div className="flex items-center justify-between bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="text-sm text-blue-900">
            已选择 <span className="font-bold">{selectedAccounts.length}</span> 个账户
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedAccounts([])}
              className="min-h-[44px]"
            >
              取消选择
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleBatchRefresh}
              disabled={isBatchRefreshing}
              className="min-h-[44px]"
            >
              <RefreshCw className={cn("mr-2 h-4 w-4", isBatchRefreshing && "animate-spin")} />
              批量刷新Token
            </Button>
          </div>
        </div>
      )}

      <AccountsTable 
        accounts={data?.accounts || []} 
        isLoading={isLoading}
        selectedAccounts={selectedAccounts}
        onSelectionChange={setSelectedAccounts}
      />

      {data && data.total_pages > 1 && (
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <div className="text-sm text-muted-foreground text-center sm:text-left">
                Total: {data.total_accounts} accounts
            </div>
            <div className="flex items-center justify-center space-x-2">
            <Button
                variant="outline"
                size="sm"
                className="min-h-[44px] min-w-[44px]"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
            >
                <ChevronLeft className="h-4 w-4" />
                <span className="hidden sm:inline ml-1">Previous</span>
            </Button>
            <div className="text-sm font-medium px-2">
                <span className="hidden sm:inline">Page </span>{page}<span className="hidden sm:inline"> of {data.total_pages}</span>
            </div>
            <Button
                variant="outline"
                size="sm"
                className="min-h-[44px] min-w-[44px]"
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
            >
                <span className="hidden sm:inline mr-1">Next</span>
                <ChevronRight className="h-4 w-4" />
            </Button>
            </div>
        </div>
      )}
    </div>
  );
}
