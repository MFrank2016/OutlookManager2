"use client";

import { useEffect, useRef } from "react";
import { toast } from "sonner";
import { copyToClipboard } from "@/lib/clipboard";

interface EmailLike {
  message_id: string;
  verification_code?: string | null;
  subject?: string;
}

interface UseVerificationCodeAutoCopyOptions {
  emails: EmailLike[];
  resetKey: string;
  enabled?: boolean;
  toastTitle?: string;
}

export function useVerificationCodeAutoCopy({
  emails,
  resetKey,
  enabled = true,
  toastTitle = "检测到新验证码",
}: UseVerificationCodeAutoCopyOptions) {
  const seenCodesRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    seenCodesRef.current = new Set();
  }, [resetKey]);

  useEffect(() => {
    if (!enabled || emails.length === 0) return;

    const next = emails.find((email) => {
      if (!email.verification_code) return false;
      const key = `${email.message_id}:${email.verification_code}`;
      return !seenCodesRef.current.has(key);
    });

    if (!next?.verification_code) return;

    const key = `${next.message_id}:${next.verification_code}`;
    seenCodesRef.current.add(key);

    void (async () => {
      const copied = await copyToClipboard(next.verification_code!);
      if (copied) {
        toast.success(`${toastTitle}：${next.verification_code}，已复制到剪贴板`, {
          description: next.subject || undefined,
        });
      } else {
        toast.warning(`${toastTitle}：${next.verification_code}，但自动复制失败`, {
          description: next.subject || undefined,
        });
      }
    })();
  }, [emails, enabled, toastTitle]);
}
