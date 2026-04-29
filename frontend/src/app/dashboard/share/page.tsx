"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CopyCheck, Loader2, Plus, Trash, Users, XCircle } from "lucide-react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageIntro } from "@/components/layout/PageIntro";
import { PageSection } from "@/components/layout/PageSection";
import { BatchCopyDialog } from "@/components/share/BatchCopyDialog";
import { BatchShareDialog } from "@/components/share/BatchShareDialog";
import { ExtendShareDialog } from "@/components/share/ExtendShareDialog";
import { ShareTokenDialog } from "@/components/share/ShareTokenDialog";
import { ShareTokenSearch } from "@/components/share/ShareTokenSearch";
import { ShareTokenTable } from "@/components/share/ShareTokenTable";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAccounts } from "@/hooks/useAccounts";
import { useConfigs } from "@/hooks/useAdmin";
import api from "@/lib/api";
import { getShareDomainFromConfigs } from "@/lib/shareUtils";
import { Account, ShareToken } from "@/types";

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
    page_size: 100,
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
    },
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
    },
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
    },
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
    },
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

  const hasAccounts = accountsData.length > 0;
  const selectedCount = selectedTokens.size;

  return (
    <div className="page-enter space-y-3 md:space-y-4">
      <PageHeader
        title="分享管理"
        description="统一管理分享链接、筛选规则与批量操作。"
      />

      <PageIntro description="快速查看当前页关键上下文。">
        <div className="grid gap-2 text-xs text-[color:var(--text-soft)] sm:grid-cols-3">
          <div className="rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-2">
            账户数量：<span className="font-semibold text-foreground">{accountsData.length}</span>
          </div>
          <div className="rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-2">
            当前分享码：<span className="font-semibold text-foreground">{tokens?.length ?? 0}</span>
          </div>
          <div className="rounded-lg border border-border/70 bg-[color:var(--surface-2)]/70 px-3 py-2">
            已选记录：<span className="font-semibold text-foreground">{selectedCount}</span>
          </div>
        </div>
      </PageIntro>

      <PageSection
        title="主操作"
        description="选择邮箱后创建或批量处理分享码。"
        contentClassName="space-y-3"
      >
        <div className="flex flex-wrap items-center gap-2">
          <Select value={selectedAccount} onValueChange={setSelectedAccount}>
            <SelectTrigger className="w-full sm:w-[240px]">
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
            className="gap-2"
            size="sm"
            disabled={!hasAccounts}
          >
            <Plus className="h-4 w-4" />
            创建分享
          </Button>

          <Button
            onClick={() => setIsBatchShareDialogOpen(true)}
            variant="outline"
            className="gap-2"
            size="sm"
            disabled={!hasAccounts}
          >
            <Users className="h-4 w-4" />
            批量分享
          </Button>

          <Button
            onClick={() => setIsBatchCopyDialogOpen(true)}
            variant="outline"
            className="gap-2"
            size="sm"
            disabled={!tokens || tokens.length === 0}
          >
            <CopyCheck className="h-4 w-4" />
            批量复制
          </Button>

          <Button
            onClick={() => {
              if (window.confirm(`确定要将选中的 ${selectedCount} 个分享码设置为失效吗？`)) {
                batchDeactivate.mutate(Array.from(selectedTokens));
              }
            }}
            variant="outline"
            className="gap-2 text-orange-600 hover:text-orange-700"
            size="sm"
            disabled={selectedCount === 0}
          >
            <XCircle className="h-4 w-4" />
            批量失效 ({selectedCount})
          </Button>

          <Button
            onClick={() => {
              if (window.confirm(`确定要删除选中的 ${selectedCount} 个分享码吗？此操作不可恢复！`)) {
                batchDelete.mutate(Array.from(selectedTokens));
              }
            }}
            variant="outline"
            className="gap-2 text-red-600 hover:text-red-700"
            size="sm"
            disabled={selectedCount === 0}
          >
            <Trash className="h-4 w-4" />
            批量删除 ({selectedCount})
          </Button>
        </div>
      </PageSection>

      <ShareTokenSearch
        accountSearch={localAccountSearch}
        tokenSearch={localTokenSearch}
        onAccountSearchChange={setLocalAccountSearch}
        onTokenSearchChange={setLocalTokenSearch}
        onSearch={handleSearch}
        isLoading={isLoading}
      />

      {isLoading ? (
        <div className="panel-surface flex justify-center p-8">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
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
