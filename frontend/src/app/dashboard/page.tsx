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
  const [jumpPage, setJumpPage] = useState("");
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
    console.log('[账户管理] 查询按钮被点击', {
      timestamp: new Date().toISOString(),
      search,
      includeTags,
      excludeTags,
      refreshStatus
    });
    
    const newParams = {
      page: 1,
      page_size: queryParams.page_size,
      email_search: search,
      include_tags: includeTags,
      exclude_tags: excludeTags,
      refresh_status: refreshStatus,
    };
    
    console.log('[账户管理] 更新查询参数', {
      timestamp: new Date().toISOString(),
      newParams
    });
    
    setQueryParams(newParams);
    setPage(1);
    setShouldQuery(true);
    
    // 使用 setTimeout 确保状态更新后再触发 refetch
    setTimeout(() => {
      console.log('[账户管理] 触发 refetch', {
        timestamp: new Date().toISOString()
      });
      refetch();
    }, 0);
  };

  const handlePageChange = (newPage: number) => {
    setPage(newPage);
    setQueryParams(prev => ({ ...prev, page: newPage }));
    // 如果已经查询过，直接更新页码并重新请求
    if (shouldQuery) {
      // refetch(); // param change will trigger query
    }
  };

  const handlePageSizeChange = (newPageSize: string) => {
    const size = parseInt(newPageSize);
    setQueryParams(prev => ({ ...prev, page_size: size, page: 1 }));
    setPage(1);
  };

  const handleJumpPage = () => {
      const pageNum = parseInt(jumpPage);
      if (!data) return;
      
      if (!isNaN(pageNum) && pageNum >= 1 && pageNum <= data.total_pages) {
          handlePageChange(pageNum);
          setJumpPage("");
      } else {
          toast.error(`请输入有效的页码 (1-${data.total_pages})`);
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
    <div className="space-y-2 md:space-y-4 px-0 md:px-4">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 md:gap-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight">账户管理</h1>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button asChild variant="secondary" className="flex-1 sm:flex-initial h-9">
            <Link href="/dashboard/accounts/batch">
              <PackagePlus className="mr-2 h-4 w-4" /> 批量添加
            </Link>
          </Button>
          <AddAccountDialog />
        </div>
      </div>

      <div className="flex flex-col gap-2 bg-white p-3 md:p-4 rounded-lg shadow-sm border">
        {/* 第一行：搜索邮箱 */}
        <div className="relative flex-1 w-full">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
            <Input 
                placeholder="搜索邮箱..." 
                className="pl-9 h-9" 
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value);
                }}
                debounce={true}
                debounceMs={500}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSearch();
                  }
                }}
            />
        </div>

        {/* 第二行：包含标签 + 排除标签 */}
        <div className="flex items-center gap-2">
            <div className="relative flex-1">
                <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                <Input 
                    placeholder="包含标签（多个用逗号分隔）..." 
                    className="pl-9 h-9 text-xs md:text-sm" 
                    value={includeTags}
                    onChange={(e) => {
                        setIncludeTags(e.target.value);
                    }}
                    debounce={true}
                    debounceMs={500}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleSearch();
                      }
                    }}
                />
            </div>
            <div className="relative flex-1">
                <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
                <Input 
                    placeholder="排除标签（多个用逗号分隔）..." 
                    className="pl-9 h-9 text-xs md:text-sm" 
                    value={excludeTags}
                    onChange={(e) => {
                        setExcludeTags(e.target.value);
                    }}
                    debounce={true}
                    debounceMs={500}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        handleSearch();
                      }
                    }}
                />
            </div>
        </div>

        {/* 第三行：筛选状态 + 查询按钮 */}
        <div className="flex items-center gap-2">
            <Select value={refreshStatus} onValueChange={(val) => { setRefreshStatus(val === "all" ? undefined : val); }}>
                <SelectTrigger className="flex-1 h-9 text-xs md:text-sm">
                    <SelectValue placeholder="筛选状态" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">全部状态</SelectItem>
                    <SelectItem value="success">成功</SelectItem>
                    <SelectItem value="failed">失败</SelectItem>
                    <SelectItem value="pending">待处理</SelectItem>
                </SelectContent>
            </Select>
            <Button 
              onClick={handleSearch}
              disabled={isLoading}
              throttle={true}
              throttleMs={300}
              className="h-9 px-4"
            >
              <Search className="mr-2 h-4 w-4" />
              查询
            </Button>
        </div>
      </div>

      {selectedAccounts.length > 0 && (
        <div className="flex items-center justify-between bg-blue-50 p-2 md:p-4 rounded-lg border border-blue-200">
          <div className="text-xs md:text-sm text-blue-900">
            已选择 <span className="font-bold">{selectedAccounts.length}</span> 个账户
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedAccounts([])}
              className="h-8 px-2 text-xs md:text-sm"
            >
              取消选择
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={handleBatchRefresh}
              disabled={isBatchRefreshing}
              throttle={true}
              throttleMs={300}
              className="h-8 px-2 text-xs md:text-sm"
            >
              <RefreshCw className={cn("mr-1.5 h-3.5 w-3.5", isBatchRefreshing && "animate-spin")} />
              批量刷新Token
            </Button>
          </div>
        </div>
      )}

      <div className="mb-2 md:mb-4">
        <AccountsTable 
          accounts={data?.accounts || []} 
          isLoading={isLoading}
          selectedAccounts={selectedAccounts}
          onSelectionChange={setSelectedAccounts}
        />
      </div>

      {data && data.total_accounts > 0 && (
        <div className="flex items-center justify-between gap-2 bg-white p-2 rounded-lg shadow-sm border shrink-0 text-xs md:text-sm">
            {/* 左侧：总计 + 每页 */}
            <div className="flex items-center gap-2">
                <span className="text-muted-foreground whitespace-nowrap">
                    共 {data.total_accounts} 个
                </span>
                <div className="flex items-center gap-1.5">
                    <span className="text-muted-foreground whitespace-nowrap">每页</span>
                    <Select 
                        value={queryParams.page_size.toString()} 
                        onValueChange={handlePageSizeChange}
                    >
                        <SelectTrigger className="w-[60px] md:w-[70px] h-7 md:h-8 text-xs md:text-sm">
                            <SelectValue placeholder="10" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="10">10</SelectItem>
                            <SelectItem value="20">20</SelectItem>
                            <SelectItem value="50">50</SelectItem>
                            <SelectItem value="100">100</SelectItem>
                            <SelectItem value="1000">1000</SelectItem>
                        </SelectContent>
                    </Select>
                </div>
            </div>

            {/* 中间：翻页按钮 */}
            <div className="flex items-center gap-1">
                <Button
                    variant="outline"
                    size="sm"
                    className="h-7 w-7 md:h-8 md:w-8 p-0"
                    onClick={() => handlePageChange(Math.max(1, page - 1))}
                    disabled={page === 1 || isLoading}
                >
                    <ChevronLeft className="h-3.5 w-3.5 md:h-4 md:w-4" />
                </Button>
                
                <div className="flex items-center justify-center min-w-[70px] md:min-w-[80px] text-xs md:text-sm">
                    <span>{page} / {data.total_pages}</span>
                </div>

                <Button
                    variant="outline"
                    size="sm"
                    className="h-7 w-7 md:h-8 md:w-8 p-0"
                    onClick={() => handlePageChange(Math.min(data.total_pages, page + 1))}
                    disabled={page === data.total_pages || isLoading}
                >
                    <ChevronRight className="h-3.5 w-3.5 md:h-4 md:w-4" />
                </Button>
            </div>

            {/* 右侧：跳转（桌面端） */}
            <div className="hidden sm:flex items-center gap-2">
                <Input
                    className="h-7 md:h-8 w-[50px] md:w-[60px] text-center px-1 text-xs md:text-sm"
                    placeholder="页码"
                    type="number"
                    min={1}
                    max={data.total_pages}
                    value={jumpPage}
                    onChange={(e) => setJumpPage(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            handleJumpPage();
                        }
                    }}
                />
                <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-7 md:h-8 px-2 text-xs md:text-sm"
                    onClick={handleJumpPage}
                    disabled={!jumpPage}
                >
                    跳转
                </Button>
            </div>
        </div>
      )}
    </div>
  );
}
