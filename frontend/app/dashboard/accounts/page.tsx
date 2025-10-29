"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { Account, AccountCreateRequest } from "@/types";

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [error, setError] = useState("");

  const fetchAccounts = async () => {
    try {
      const data = await apiClient.getAccounts();
      setAccounts(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "获取账户列表失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleDeleteAccount = async (id: string) => {
    if (!confirm("确定要删除这个账户吗？")) return;

    try {
      await apiClient.deleteAccount(id);
      await fetchAccounts();
    } catch (err) {
      alert(err instanceof Error ? err.message : "删除失败");
    }
  };

  const handleRefreshToken = async (id: string) => {
    try {
      await apiClient.refreshAccountToken(id);
      alert("Token刷新成功");
      await fetchAccounts();
    } catch (err) {
      alert(err instanceof Error ? err.message : "刷新失败");
    }
  };

  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">账户管理</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          ➕ 添加账户
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-4 text-red-600">
          {error}
        </div>
      )}

      <div className="rounded-lg bg-white shadow-md">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  邮箱
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  刷新状态
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  标签
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  最后刷新
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {accounts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    暂无账户
                  </td>
                </tr>
              ) : (
                accounts.map((account) => (
                  <tr key={account.id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {account.email}
                      </div>
                      <div className="text-xs text-gray-500">
                        {account.client_id}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <StatusBadge status={account.status} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <RefreshStatusBadge status={account.refresh_status} />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-wrap gap-1">
                        {account.tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-block rounded-full bg-blue-100 px-2 py-1 text-xs text-blue-800"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                      {account.last_refresh_time
                        ? new Date(account.last_refresh_time).toLocaleString(
                            "zh-CN"
                          )
                        : "从未"}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right text-sm">
                      <button
                        onClick={() => handleRefreshToken(account.id)}
                        className="mr-2 text-blue-600 hover:text-blue-900"
                        title="刷新Token"
                      >
                        🔄
                      </button>
                      <button
                        onClick={() => handleDeleteAccount(account.id)}
                        className="text-red-600 hover:text-red-900"
                        title="删除"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showCreateModal && (
        <CreateAccountModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchAccounts();
          }}
        />
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    active: "bg-green-100 text-green-800",
    inactive: "bg-gray-100 text-gray-800",
    suspended: "bg-yellow-100 text-yellow-800",
    error: "bg-red-100 text-red-800",
  };

  return (
    <span
      className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${
        colors[status] || colors.inactive
      }`}
    >
      {status}
    </span>
  );
}

function RefreshStatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-gray-100 text-gray-800",
    success: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
    in_progress: "bg-blue-100 text-blue-800",
  };

  return (
    <span
      className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${
        colors[status] || colors.pending
      }`}
    >
      {status}
    </span>
  );
}

function CreateAccountModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState<AccountCreateRequest>({
    email: "",
    refresh_token: "",
    client_id: "",
    tags: [],
  });
  const [tagInput, setTagInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await apiClient.createAccount(formData);
      onSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setLoading(false);
    }
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags?.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...(formData.tags || []), tagInput.trim()],
      });
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    setFormData({
      ...formData,
      tags: formData.tags?.filter((t) => t !== tag) || [],
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="w-full max-w-md rounded-lg bg-white p-6">
        <h2 className="mb-4 text-xl font-bold">添加账户</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              邮箱地址
            </label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) =>
                setFormData({ ...formData, email: e.target.value })
              }
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none"
              placeholder="user@outlook.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Refresh Token
            </label>
            <textarea
              required
              value={formData.refresh_token}
              onChange={(e) =>
                setFormData({ ...formData, refresh_token: e.target.value })
              }
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none"
              rows={3}
              placeholder="从Microsoft Azure获取的refresh token"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Client ID
            </label>
            <input
              type="text"
              required
              value={formData.client_id}
              onChange={(e) =>
                setFormData({ ...formData, client_id: e.target.value })
              }
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none"
              placeholder="Azure应用程序ID"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              标签
            </label>
            <div className="mt-1 flex gap-2">
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag();
                  }
                }}
                className="block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none"
                placeholder="添加标签"
              />
              <button
                type="button"
                onClick={addTag}
                className="rounded-md bg-gray-200 px-4 py-2 hover:bg-gray-300"
              >
                添加
              </button>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              {formData.tags?.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    className="hover:text-blue-600"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? "创建中..." : "创建"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-md bg-gray-200 px-4 py-2 hover:bg-gray-300"
            >
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

