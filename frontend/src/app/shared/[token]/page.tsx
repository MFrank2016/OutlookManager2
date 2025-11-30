"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Loader2, Mail, ChevronLeft, ChevronRight } from "lucide-react";
import { format } from "date-fns";
import Link from "next/link";

interface EmailItem {
  message_id: string;
  subject: string;
  from_email: string;
  date: string;
  folder: string;
  sender_initial: string;
}

export default function SharedEmailPage() {
  const params = useParams();
  const token = params.token as string;
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const { data, isLoading, error } = useQuery({
    queryKey: ["shared-emails", token, page],
    queryFn: async () => {
      // 使用公共API，不需要认证token
      const response = await fetch(`/share/${token}/emails?page=${page}&page_size=${pageSize}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Failed to fetch" }));
        throw new Error(errorData.detail || "Failed to fetch emails");
      }
      return response.json();
    },
    enabled: !!token,
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="bg-white rounded-lg shadow-md p-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">访问失败</h1>
            <p className="text-gray-600 mb-6">
              {error instanceof Error ? error.message : "无法加载分享的邮件"}
            </p>
            <p className="text-sm text-gray-500">
              可能的原因：分享链接已过期、无效或已被禁用
            </p>
          </div>
        </div>
      </div>
    );
  }

  const emails: EmailItem[] = data?.emails || [];
  const total = data?.total_emails || 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">共享邮件</h1>
                <p className="text-sm text-gray-500 mt-1">
                  共 {total} 封邮件
                </p>
              </div>
            </div>
          </div>

          {emails.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <Mail className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">暂无邮件</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-slate-50">
                      <TableHead>发件人</TableHead>
                      <TableHead>主题</TableHead>
                      <TableHead>时间</TableHead>
                      <TableHead>文件夹</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {emails.map((email) => (
                      <TableRow key={email.message_id} className="hover:bg-gray-50">
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-medium">
                              {email.sender_initial}
                            </div>
                            <span className="text-sm">{email.from_email}</span>
                          </div>
                        </TableCell>
                        <TableCell className="font-medium">{email.subject || "(无主题)"}</TableCell>
                        <TableCell className="text-sm text-gray-600">
                          {format(new Date(email.date), "yyyy-MM-dd HH:mm")}
                        </TableCell>
                        <TableCell>
                          <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
                            {email.folder}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    第 {page} 页，共 {totalPages} 页
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4 mr-1" />
                      上一页
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      下一页
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
