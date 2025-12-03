"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Copy, Loader2, Plus, CopyCheck, Users, XCircle, Trash } from "lucide-react";
import { toast } from "sonner";
import { ShareTokenDialog } from "@/components/share/ShareTokenDialog";
import { BatchShareDialog } from "@/components/share/BatchShareDialog";
import { BatchCopyDialog } from "@/components/share/BatchCopyDialog";
import { ExtendShareDialog } from "@/components/share/ExtendShareDialog";
import { ShareTokenTable } from "@/components/share/ShareTokenTable";
import { ShareTokenSearch } from "@/components/share/ShareTokenSearch";
import { ShareToken, Account } from "@/types";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAccounts } from "@/hooks/useAccounts";
import { useConfigs } from "@/hooks/useAdmin";
import { getShareDomainFromConfigs } from "@/lib/shareUtils";

export default function ShareManagementPage() {
  const queryClient = useQueryClient();
  const [page] = useState(1);
  const [editToken, setEditToken] = useState<ShareToken | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isBatchShareDialogOpen, setIsBatchShareDialogOpen] = useState(false);
  const [isBatchCopyDialogOpen, setIsBatchCopyDialogOpen] = useState(false);
  const [isExtendDialogOpen, setIsExtendDialogOpen] = useState(false);
  const [extendToken, setExtendToken] = useState<ShareToken | null>(null);
  const [selectedAccount, setSelectedAccount] = useState<string>("");
  const [selectedTokens, setSelectedTokens] = useState<Set<number>>(new Set());
  
  // 本地查询条件状态（用于输入，不立即触发查询）
  const [localAccountSearch, setLocalAccountSearch] = useState("");
  const [localTokenSearch, setLocalTokenSearch] = useState("");
  
  // 实际查询条件状态（用于真正发起查询）
  const [accountSearch, setAccountSearch] = useState<string | undefined>(undefined);
  const [tokenSearch, setTokenSearch] = useState<string | undefined>(undefined);

  // 获取账户列表（使用现有的hook）
  const { data: accountsResponse } = useAccounts({
    page: 1,
    page_size: 100
  });
  
  const accountsData = accountsResponse?.accounts || [];

  // 获取系统配置（用于分享页域名）
  const { data: configsData } = useConfigs();
  const shareDomain = getShareDomainFromConfigs(configsData?.configs);

  const { data: tokens, isLoading } = useQuery({
    queryKey: ["share-tokens", page, accountSearch, tokenSearch],
    queryFn: async () => {
      const params: Record<string, unknown> = { page, page_size: 50 };
      if (accountSearch && accountSearch.trim()) {
        params.account_search = accountSearch.trim();
      }
      if (tokenSearch && tokenSearch.trim()) {
        params.token_search = tokenSearch.trim();
      }
      const res = await api.get<ShareToken[]>("/share/tokens", { params });
      return res.data;
    }
  });
  
  // 处理查询按钮点击
  const handleSearch = () => {
    setAccountSearch(localAccountSearch.trim() || undefined);
    setTokenSearch(localTokenSearch.trim() || undefined);
  };

  const deleteToken = useMutation({
    mutationFn: async (token: string) => {
      await api.delete(`/share/tokens/by-token/${token}`);
    },
    onSuccess: () => {
      toast.success("分享码已删除");
      queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || "删除失败");
    }
  });

  const batchDeactivate = useMutation({
    mutationFn: async (tokenIds: number[]) => {
      await api.post("/share/tokens/batch-deactivate", { token_ids: tokenIds });
    },
    onSuccess: () => {
      toast.success("批量失效成功");
      queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
      setSelectedTokens(new Set());
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || "批量失效失败");
    }
  });

  const batchDelete = useMutation({
    mutationFn: async (tokenIds: number[]) => {
      await api.post("/share/tokens/batch-delete", { token_ids: tokenIds });
    },
    onSuccess: () => {
      toast.success("批量删除成功");
      queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
      setSelectedTokens(new Set());
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      toast.error(error.response?.data?.detail || "批量删除失败");
    }
  });

  // 处理表格选择
  const handleToggleSelect = (tokenId: number, checked: boolean) => {
    const newSelected = new Set(selectedTokens);
    if (checked) {
      newSelected.add(tokenId);
    } else {
      newSelected.delete(tokenId);
    }
    setSelectedTokens(newSelected);
  };

  const handleToggleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedTokens(new Set(tokens?.map((t) => t.id) || []));
    } else {
      setSelectedTokens(new Set());
    }
  };

  return (
    <div className="space-y-3 md:space-y-6 px-0 md:px-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 md:gap-0">
        <h1 className="hidden md:block text-2xl font-bold tracking-tight">分享管理</h1>
        <div className="flex gap-1.5 md:gap-2 flex-wrap md:flex-nowrap w-full md:w-auto">
          {accountsData && accountsData.length > 0 && (
            <>
              <Select value={selectedAccount} onValueChange={setSelectedAccount}>
                <SelectTrigger className="w-full md:w-[200px]">
                  <SelectValue placeholder="选择邮箱账户" />
                </SelectTrigger>
                <SelectContent>
                  {accountsData.map((account: Account, index: number) => (
                    <SelectItem key={account.email_id || `account-${index}`} value={account.email_id}>
                      {account.email_id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                onClick={() => {
                  if (!selectedAccount) {
                    toast.error("请先选择邮箱账户");
                    return;
                  }
                  setIsCreateDialogOpen(true);
                }}
                className="gap-2 text-xs md:text-sm"
                size="sm"
              >
                <Plus className="h-3.5 w-3.5 md:h-4 md:w-4" />
                <span className="hidden sm:inline">创建分享</span>
                <span className="sm:hidden">创建</span>
              </Button>
              <Button
                onClick={() => setIsBatchShareDialogOpen(true)}
                variant="outline"
                className="gap-2 text-xs md:text-sm"
                size="sm"
              >
                <Users className="h-3.5 w-3.5 md:h-4 md:w-4" />
                <span className="hidden sm:inline">批量分享</span>
                <span className="sm:hidden">分享</span>
              </Button>
              {tokens && tokens.length > 0 && (
                <>
                  <Button
                    onClick={() => setIsBatchCopyDialogOpen(true)}
                    variant="outline"
                    className="gap-2 text-xs md:text-sm"
                    size="sm"
                  >
                    <CopyCheck className="h-3.5 w-3.5 md:h-4 md:w-4" />
                    <span className="hidden sm:inline">批量复制</span>
                    <span className="sm:hidden">复制</span>
                  </Button>
                  {selectedTokens.size > 0 && (
                    <>
                      <Button
                        onClick={() => {
                          if (window.confirm(`确定要将选中的 ${selectedTokens.size} 个分享码设置为失效吗？`)) {
                            batchDeactivate.mutate(Array.from(selectedTokens));
                          }
                        }}
                        variant="outline"
                        className="gap-2 text-orange-600 hover:text-orange-700 text-xs md:text-sm"
                        size="sm"
                      >
                        <XCircle className="h-3.5 w-3.5 md:h-4 md:w-4" />
                        <span className="hidden sm:inline">批量失效 ({selectedTokens.size})</span>
                        <span className="sm:hidden">失效 ({selectedTokens.size})</span>
                      </Button>
                      <Button
                        onClick={() => {
                          if (window.confirm(`确定要删除选中的 ${selectedTokens.size} 个分享码吗？此操作不可恢复！`)) {
                            batchDelete.mutate(Array.from(selectedTokens));
                          }
                        }}
                        variant="outline"
                        className="gap-2 text-red-600 hover:text-red-700 text-xs md:text-sm"
                        size="sm"
                      >
                        <Trash className="h-3.5 w-3.5 md:h-4 md:w-4" />
                        <span className="hidden sm:inline">批量删除 ({selectedTokens.size})</span>
                        <span className="sm:hidden">删除 ({selectedTokens.size})</span>
                      </Button>
                    </>
                  )}
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* 查询区域 */}
      <ShareTokenSearch
        accountSearch={localAccountSearch}
        tokenSearch={localTokenSearch}
        onAccountSearchChange={setLocalAccountSearch}
        onTokenSearchChange={setLocalTokenSearch}
        onSearch={handleSearch}
        isLoading={isLoading}
      />

      {isLoading ? (
        <div className="flex justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : (
        <ShareTokenTable
          tokens={tokens}
          selectedTokens={selectedTokens}
          onToggleSelect={handleToggleSelect}
          onToggleSelectAll={handleToggleSelectAll}
          onEdit={(token) => {
            setEditToken(token);
            setIsEditDialogOpen(true);
          }}
          onExtend={(token) => {
            setExtendToken(token);
            setIsExtendDialogOpen(true);
          }}
          onDelete={(token) => deleteToken.mutate(token)}
          shareDomain={shareDomain || undefined}
        />
      )}

      <ShareTokenDialog
        open={isEditDialogOpen}
        onOpenChange={(open) => {
            setIsEditDialogOpen(open);
            if (!open) setEditToken(null);
        }}
        tokenToEdit={editToken || undefined}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
          setEditToken(null);
        }}
      />
      
      <ShareTokenDialog
        open={isCreateDialogOpen}
        onOpenChange={(open) => {
            setIsCreateDialogOpen(open);
            if (!open) setSelectedAccount("");
        }}
        emailAccount={selectedAccount}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
          setIsCreateDialogOpen(false);
          setSelectedAccount("");
        }}
      />

      <BatchShareDialog
        open={isBatchShareDialogOpen}
        onOpenChange={setIsBatchShareDialogOpen}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
        }}
      />

      <BatchCopyDialog
        open={isBatchCopyDialogOpen}
        onOpenChange={setIsBatchCopyDialogOpen}
        tokens={tokens || []}
        selectedTokens={tokens?.filter((t) => selectedTokens.has(t.id)) || []}
      />

      {extendToken && (
        <ExtendShareDialog
          open={isExtendDialogOpen}
          onOpenChange={(open) => {
            setIsExtendDialogOpen(open);
            if (!open) setExtendToken(null);
          }}
          token={extendToken}
          onSuccess={() => {
            queryClient.invalidateQueries({ queryKey: ["share-tokens"] });
            setExtendToken(null);
          }}
        />
      )}
    </div>
  );
}

