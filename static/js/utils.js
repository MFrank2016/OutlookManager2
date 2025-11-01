// 工具函数模块

// 格式化邮件日期
function formatEmailDate(dateString) {
  try {
    if (!dateString) return "未知时间";

    let date = new Date(dateString);

    if (isNaN(date.getTime())) {
      if (
        dateString.includes("T") &&
        !dateString.includes("Z") &&
        !dateString.includes("+")
      ) {
        date = new Date(dateString + "Z");
      }
      if (isNaN(date.getTime())) {
        return "日期格式错误";
      }
    }

    // 显示完整的日期+时间
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");

    return `${year}年${month}月${day}日 ${hours}:${minutes}`;
  } catch (error) {
    console.error("Date formatting error:", error);
    return "时间解析失败";
  }
}

// 格式化刷新时间
function formatRefreshTime(timeString) {
  if (!timeString) return "未刷新";
  try {
    const date = new Date(timeString);
    if (isNaN(date.getTime())) return "未刷新";
    return date.toLocaleString("zh-CN");
  } catch (error) {
    return "未刷新";
  }
}

// 格式化日期时间为datetime-local格式
function formatDateTimeLocal(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// 前端验证码检测函数
function detectVerificationCode(subject = "", body = "") {
  // 关键词列表
  const keywords = [
    "verification code",
    "security code",
    "OTP",
    "one-time password",
    "验证码",
    "安全码",
    "一次性密码",
    "激活码",
    "校验码",
    "动态码",
    "código de verificación",
    "code de vérification",
    "verificatiecode",
  ];

  // 检查是否包含关键词
  const text = `${subject} ${body}`.toLowerCase();
  const hasKeyword = keywords.some((keyword) =>
    text.includes(keyword.toLowerCase())
  );

  if (!hasKeyword) {
    return null;
  }

  // 验证码正则表达式（按优先级排序）
  const patterns = [
    // 明确标识的验证码
    /(?:code|Code|CODE|验证码|驗證碼|verification code)[:\s是：]+([A-Z0-9]{4,8})/i,
    /(?:OTP|otp)[:\s]+(\d{4,8})/i,

    // HTML中的验证码
    /<(?:b|strong|span)[^>]*>([A-Z0-9]{4,8})<\/(?:b|strong|span)>/i,

    // 纯数字验证码（4-8位）
    /\b(\d{4,8})\b/,

    // 字母数字组合
    /\b([A-Z]{2,4}[0-9]{2,6})\b/i,
    /\b([0-9]{2,4}[A-Z]{2,4})\b/i,
    /\b([A-Z0-9]{6})\b/i,

    // 带分隔符的验证码
    /(\d{3}[-\s]\d{3})/,
    /(\d{2}[-\s]\d{2}[-\s]\d{2})/,
  ];

  // 排除的常见词
  const excludeList = [
    "your",
    "code",
    "the",
    "this",
    "that",
    "from",
    "email",
    "mail",
    "click",
    "here",
    "link",
    "button",
    "verify",
    "account",
    "please",
    "邮件",
    "点击",
    "链接",
    "账户",
    "账号",
    "请",
    "您的",
  ];

  // 尝试匹配
  for (const pattern of patterns) {
    const searchText = body || subject;
    const match = searchText.match(pattern);
    if (match && match[1]) {
      const code = match[1].trim();

      // 验证码有效性检查
      if (code.length < 4 || code.length > 8) continue;
      if (excludeList.includes(code.toLowerCase())) continue;
      if (/^(.)\1+$/.test(code)) continue; // 排除全是重复字符
      if (/^[a-zA-Z]+$/.test(code) && code.length < 6) continue; // 纯字母且太短

      return code;
    }
  }

  return null;
}

// 复制验证码到剪切板
async function copyVerificationCode(code) {
  try {
    // 使用现代剪切板API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(code);
      showNotification(`验证码已复制: ${code}`, "success", "✅ 复制成功", 3000);
    } else {
      // 降级方案：使用传统方法
      const textArea = document.createElement("textarea");
      textArea.value = code;
      textArea.style.position = "fixed";
      textArea.style.left = "-9999px";
      document.body.appendChild(textArea);
      textArea.focus();
      textArea.select();

      try {
        document.execCommand("copy");
        showNotification(
          `验证码已复制: ${code}`,
          "success",
          "✅ 复制成功",
          3000
        );
      } catch (err) {
        console.error("复制失败:", err);
        showNotification("复制失败，请手动复制", "error", "❌ 错误", 3000);
      }

      document.body.removeChild(textArea);
    }
  } catch (err) {
    console.error("复制验证码失败:", err);
    showNotification("复制失败: " + err.message, "error", "❌ 错误", 3000);
  }
}

// 复制邮箱地址
function copyEmailAddress(emailAddress) {
  // 清理邮箱地址（去除可能的空格和特殊字符）
  const cleanEmail = emailAddress.trim();

  if (!cleanEmail) {
    showNotification("邮箱地址为空", "error");
    return;
  }

  // 复制到剪贴板
  navigator.clipboard
    .writeText(cleanEmail)
    .then(() => {
      // 显示成功通知
      showNotification(`邮箱地址已复制: ${cleanEmail}`, "success");

      // 添加视觉反馈
      const emailElement = document.getElementById("currentAccountEmail");
      if (emailElement) {
        emailElement.classList.add("copy-success");
        setTimeout(() => {
          emailElement.classList.remove("copy-success");
        }, 300);
      }
    })
    .catch((error) => {
      console.error("复制失败:", error);

      // 降级方案：尝试使用旧的复制方法
      try {
        const textArea = document.createElement("textarea");
        textArea.value = cleanEmail;
        textArea.style.position = "fixed";
        textArea.style.opacity = "0";
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand("copy");
        document.body.removeChild(textArea);

        showNotification(`邮箱地址已复制: ${cleanEmail}`, "success");
      } catch (fallbackError) {
        console.error("降级复制方案也失败:", fallbackError);
        showNotification("复制失败，请手动复制邮箱地址", "error");

        // 选中文本以便用户手动复制
        const emailElement = document.getElementById("currentAccountEmail");
        if (emailElement && window.getSelection) {
          const selection = window.getSelection();
          const range = document.createRange();
          range.selectNodeContents(emailElement);
          selection.removeAllRanges();
          selection.addRange(range);
        }
      }
    });
}

// 后备复制方法
function fallbackCopyText(text) {
  const textArea = document.createElement("textarea");
  textArea.value = text;
  document.body.appendChild(textArea);
  textArea.select();
  try {
    document.execCommand("copy");
    showNotification("链接已复制到剪贴板", "success");
  } catch (err) {
    showNotification("复制失败，请手动复制", "error");
  }
  document.body.removeChild(textArea);
}

// 下载CSV
function downloadCSV(content, filename) {
  const blob = new Blob(["\uFEFF" + content], {
    type: "text/csv;charset=utf-8;",
  });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", filename);
  link.style.visibility = "hidden";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

// 生成邮件CSV
function generateEmailCSV(emails) {
  const headers = [
    "主题",
    "发件人",
    "日期",
    "文件夹",
    "是否已读",
    "是否有附件",
  ];
  const rows = emails.map((email) => [
    `"${(email.subject || "").replace(/"/g, '""')}"`,
    `"${email.from_email.replace(/"/g, '""')}"`,
    `"${email.date}"`,
    `"${email.folder}"`,
    email.is_read ? "已读" : "未读",
    email.has_attachments ? "有附件" : "无附件",
  ]);

  return [headers, ...rows].map((row) => row.join(",")).join("\n");
}
