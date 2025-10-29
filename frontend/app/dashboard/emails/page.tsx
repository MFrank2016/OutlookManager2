"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { Account, Email, EmailFolder } from "@/types";

export default function EmailsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string>("");
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<EmailFolder>("INBOX");
  const [loading, setLoading] = useState(true);
  const [emailsLoading, setEmailsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchAccounts = async () => {
      try {
        const data = await apiClient.getAccounts();
        setAccounts(data.items);
        if (data.items.length > 0) {
          setSelectedAccountId(data.items[0].id);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "获取账户列表失败");
      } finally {
        setLoading(false);
      }
    };

    fetchAccounts();
  }, []);

  useEffect(() => {
    if (!selectedAccountId) return;

    const fetchEmails = async () => {
      setEmailsLoading(true);
      try {
        const data = await apiClient.getEmails(selectedAccountId, {
          folder: selectedFolder,
          limit: 50,
        });
        setEmails(data.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "获取邮件列表失败");
      } finally {
        setEmailsLoading(false);
      }
    };

    fetchEmails();
  }, [selectedAccountId, selectedFolder]);

  if (loading) {
    return <div>加载中...</div>;
  }

  if (accounts.length === 0) {
    return (
      <div className="rounded-lg bg-white p-8 text-center shadow-md">
        <p className="mb-4 text-gray-600">暂无账户，请先添加账户</p>
        <a
          href="/dashboard/accounts"
          className="inline-block rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          前往添加账户
        </a>
      </div>
    );
  }

  const folders: EmailFolder[] = ["INBOX", "SENT", "DRAFTS", "TRASH", "JUNK"];

  return (
    <div>
      <h1 className="mb-6 text-3xl font-bold text-gray-900">邮件管理</h1>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-4 text-red-600">
          {error}
        </div>
      )}

      <div className="mb-4 flex gap-4">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700">
            选择账户
          </label>
          <select
            value={selectedAccountId}
            onChange={(e) => setSelectedAccountId(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none"
          >
            {accounts.map((account) => (
              <option key={account.id} value={account.id}>
                {account.email}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700">
            选择文件夹
          </label>
          <select
            value={selectedFolder}
            onChange={(e) => setSelectedFolder(e.target.value as EmailFolder)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none"
          >
            {folders.map((folder) => (
              <option key={folder} value={folder}>
                {getFolderDisplayName(folder)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="rounded-lg bg-white shadow-md">
        {emailsLoading ? (
          <div className="p-8 text-center text-gray-600">加载邮件中...</div>
        ) : emails.length === 0 ? (
          <div className="p-8 text-center text-gray-600">
            该文件夹暂无邮件
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {emails.map((email) => (
              <EmailItem key={email.id} email={email} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function EmailItem({ email }: { email: Email }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`p-4 hover:bg-gray-50 ${
        email.status === "unread" ? "bg-blue-50" : ""
      }`}
    >
      <div
        className="cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3
                className={`text-sm ${
                  email.status === "unread" ? "font-bold" : "font-medium"
                }`}
              >
                {email.subject || "(无主题)"}
              </h3>
              {email.is_flagged && <span>⭐</span>}
              {email.has_attachments && <span>📎</span>}
            </div>
            <p className="mt-1 text-xs text-gray-600">
              发件人: {email.sender.name || email.sender.address}
            </p>
            <p className="mt-1 text-xs text-gray-500">
              {new Date(email.sent_at).toLocaleString("zh-CN")}
            </p>
          </div>
          <div className="ml-4">
            <span className="text-gray-400">{expanded ? "▼" : "▶"}</span>
          </div>
        </div>

        {expanded && (
          <div className="mt-4 border-t pt-4">
            <div className="mb-2 text-sm">
              <strong>收件人:</strong>{" "}
              {email.recipients.map((r) => r.address).join(", ")}
            </div>
            <div className="rounded bg-gray-50 p-3 text-sm">
              {email.body_preview}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function getFolderDisplayName(folder: EmailFolder): string {
  const names: Record<EmailFolder, string> = {
    INBOX: "收件箱",
    SENT: "已发送",
    DRAFTS: "草稿箱",
    TRASH: "回收站",
    JUNK: "垃圾邮件",
  };
  return names[folder];
}

