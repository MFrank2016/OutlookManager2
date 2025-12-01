"use client";

import { useState, useEffect } from "react";
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
  const [includeTags, setIncludeTags] = useState("");
  const [excludeTags, setExcludeTags] = useState("");
  const [refreshStatus, setRefreshStatus] = useState<string | undefined>(undefined);
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [isBatchRefreshing, setIsBatchRefreshing] = useState(false);
  const [queryParams, setQueryParams] = useState({
    page: 1,
    page_size: 10,
    email_search: "",
    include_tags: "",
    exclude_tags: "",
    refresh_status: undefined as string | undefined,
  });
  const [shouldQuery, setShouldQuery] = useState(true); // 初始为 true，页面加载时自动请求
  const queryClient = useQueryClient();
  
  const { data, isLoading, refetch } = useAccounts({ 
      page: queryParams.page, 
      page_size: queryParams.page_size, 
      email_search: queryParams.email_search,
      include_tags: queryParams.include_tags || undefined,
      exclude_tags: queryParams.exclude_tags || undefined,
      refresh_status: queryParams.refresh_status
  }, {
    enabled: shouldQuery,
  });

  const handleSearch = () => {
    const newParams = {
      page: 1,
      page_size: 10,
      email_search: search,
      include_tags: includeTags,
      exclude_tags: excludeTags,
      refresh_status: refreshStatus,
    };
    setQueryParams(newParams);
    setPage(1);
    setShouldQuery(true);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    setQueryParams(prev => ({ ...prev, page: newPage }));
    // 如果已经查询过，直接更新页码并重新请求
    if (shouldQuery) {
      refetch();
    }
  };

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
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">账户管理</h1>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button asChild variant="secondary" className="flex-1 sm:flex-initial min-h-[44px]">
            <Link href="/dashboard/accounts/batch">
              <PackagePlus className="mr-2 h-4 w-4" /> 批量添加
            </Link>
          </Button>
          <AddAccountDialog />
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 bg-white p-4 rounded-lg shadow-sm border">
        <div className="relative flex-1 w-full">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
            <Input 
                placeholder="搜索邮箱..." 
                className="pl-9 min-h-[44px]" 
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
            />
        </div>
        <div className="relative flex-1 w-full">
            <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
            <Input 
                placeholder="包含标签（多个用逗号分隔）..." 
                className="pl-9 min-h-[44px]" 
                value={includeTags}
                onChange={(e) => {
                    setIncludeTags(e.target.value);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
            />
        </div>
        <div className="relative flex-1 w-full">
            <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
            <Input 
                placeholder="排除标签（多个用逗号分隔）..." 
                className="pl-9 min-h-[44px]" 
                value={excludeTags}
                onChange={(e) => {
                    setExcludeTags(e.target.value);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
            />
        </div>
        <div className="w-full sm:w-[180px]">
            <Select value={refreshStatus} onValueChange={(val) => { setRefreshStatus(val === "all" ? undefined : val); }}>
                <SelectTrigger className="min-h-[44px]">
                    <SelectValue placeholder="筛选状态" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">全部状态</SelectItem>
                    <SelectItem value="success">成功</SelectItem>
                    <SelectItem value="failed">失败</SelectItem>
                    <SelectItem value="pending">待处理</SelectItem>
                </SelectContent>
            </Select>
        </div>
        <Button 
          onClick={handleSearch}
          disabled={isLoading}
          className="min-h-[44px] w-full sm:w-auto"
        >
          <Search className="mr-2 h-4 w-4" />
          查询
        </Button>
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
                总计: {data.total_accounts} 个账户
            </div>
            <div className="flex items-center justify-center space-x-2">
            <Button
                variant="outline"
                size="sm"
                className="min-h-[44px] min-w-[44px]"
                onClick={() => handlePageChange(Math.max(1, page - 1))}
                disabled={page === 1 || isLoading}
            >
                <ChevronLeft className="h-4 w-4" />
                <span className="hidden sm:inline ml-1">上一页</span>
            </Button>
            <div className="text-sm font-medium px-2">
                <span className="hidden sm:inline">第 </span>{page}<span className="hidden sm:inline"> 页，共 {data.total_pages} 页</span>
            </div>
            <Button
                variant="outline"
                size="sm"
                className="min-h-[44px] min-w-[44px]"
                onClick={() => handlePageChange(Math.min(data.total_pages, page + 1))}
                disabled={page === data.total_pages || isLoading}
            >
                <span className="hidden sm:inline mr-1">下一页</span>
                <ChevronRight className="h-4 w-4" />
            </Button>
            </div>
        </div>
      )}
    </div>
  );
}
