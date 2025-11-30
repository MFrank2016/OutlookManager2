"use client";

import { useState } from "react";
import { useAccounts } from "@/hooks/useAccounts";
import { AccountsTable } from "@/components/accounts/AccountsTable";
import { AddAccountDialog } from "@/components/accounts/AddAccountDialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ChevronLeft, ChevronRight, Search, PackagePlus, Filter } from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [tagSearch, setTagSearch] = useState("");
  const [refreshStatus, setRefreshStatus] = useState<string | undefined>(undefined);
  
  const { data, isLoading } = useAccounts({ 
      page, 
      page_size: 10, 
      email_search: search,
      tag_search: tagSearch,
      refresh_status: refreshStatus
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Accounts</h1>
        <div className="flex items-center gap-2">
          <Button asChild variant="secondary">
            <Link href="/dashboard/accounts/batch">
              <PackagePlus className="mr-2 h-4 w-4" /> Batch Add
            </Link>
          </Button>
          <AddAccountDialog />
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 bg-white p-4 rounded-lg shadow-sm border">
        <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
            <Input 
                placeholder="Search emails..." 
                className="pl-9" 
                value={search}
                onChange={(e) => {
                    setSearch(e.target.value);
                    setPage(1);
                }}
            />
        </div>
        <div className="relative flex-1 min-w-[200px]">
            <Filter className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
            <Input 
                placeholder="Filter by tags (e.g. vip, !old)" 
                className="pl-9" 
                value={tagSearch}
                onChange={(e) => {
                    setTagSearch(e.target.value);
                    setPage(1);
                }}
            />
        </div>
        <div className="w-[180px]">
            <Select value={refreshStatus} onValueChange={(val) => { setRefreshStatus(val === "all" ? undefined : val); setPage(1); }}>
                <SelectTrigger>
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

      <AccountsTable accounts={data?.accounts || []} isLoading={isLoading} />

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
                Total: {data.total_accounts} accounts
            </div>
            <div className="flex items-center space-x-2">
            <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
            >
                <ChevronLeft className="h-4 w-4" />
                Previous
            </Button>
            <div className="text-sm font-medium">
                Page {page} of {data.total_pages}
            </div>
            <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
            >
                Next
                <ChevronRight className="h-4 w-4" />
            </Button>
            </div>
        </div>
      )}
    </div>
  );
}
