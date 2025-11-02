// emails.js - 邮件管理模块

// 邮件相关全局变量
let allEmails = [];
let filteredEmails = [];
let searchTimeout = null;
let autoRefreshTimer = null;
let isLoadingEmails = false;

// 启动自动刷新定时器
function startAutoRefresh() {
  stopAutoRefresh();
  autoRefreshTimer = setInterval(() => {
    if (
      currentAccount &&
      document.getElementById("emailsPage") &&
      !document.getElementById("emailsPage").classList.contains("hidden")
    ) {
      console.log("[自动刷新] 正在检查新邮件...");
      // 自动刷新时保持当前搜索条件，不显示加载动画
      loadEmails(true, false);
    }
  }, 10000);
  console.log("[自动刷新] 定时器已启动（每10秒从服务器检查新邮件）");
}

// 停止自动刷新定时器
function stopAutoRefresh() {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer);
    autoRefreshTimer = null;
    console.log("[自动刷新] 定时器已停止");
  }
}

// 查看账户邮件
function viewAccountEmails(emailId) {
  currentAccount = emailId;
  document.getElementById("currentAccountEmail").textContent = emailId;
  document.getElementById("emailsNav").style.display = "block";

  emailCurrentPage = 1;
  emailPageSize = 100;

  const senderSearch = document.getElementById("senderSearch");
  const subjectSearch = document.getElementById("subjectSearch");
  const folderFilter = document.getElementById("folderFilter");
  const sortOrder = document.getElementById("sortOrder");

  if (senderSearch) senderSearch.value = "";
  if (subjectSearch) subjectSearch.value = "";
  if (folderFilter) folderFilter.value = "all";
  if (sortOrder) sortOrder.value = "desc";

  startAutoRefresh();
  showPage("emails");
  loadEmails(true, true);
}

// 返回账户列表
function backToAccounts() {
  currentAccount = null;
  stopAutoRefresh();
  document.getElementById("emailsNav").style.display = "none";
  showPage("accounts");
}

// 加载邮件列表
async function loadEmails(forceRefresh = false, showLoading = true) {
  if (!currentAccount || isLoadingEmails) return;

  const emailsList = document.getElementById("emailsList");
  const refreshBtn = document.getElementById("refreshBtn");

  const oldEmails = [...allEmails];
  const oldEmailIds = new Set(oldEmails.map((e) => e.message_id));

  const senderSearch = document.getElementById("senderSearch")?.value || "";
  const subjectSearch = document.getElementById("subjectSearch")?.value || "";
  const sortOrder = document.getElementById("sortOrder")?.value || "desc";
  const folder = document.getElementById("folderFilter")?.value || "all";
  
  // 检查是否有搜索条件
  const hasSearchCondition = senderSearch || subjectSearch;

  isLoadingEmails = true;

  if (showLoading && allEmails.length === 0) {
    emailsList.innerHTML =
      '<tr><td colspan="4" style="padding: 40px; text-align: center;"><div class="loading"><div class="loading-spinner"></div>正在加载邮件...</div></td></tr>';
  }

  if (refreshBtn) {
    refreshBtn.disabled = true;
    refreshBtn.innerHTML =
      '<span style="display:inline-block;animation:spin 1s linear infinite;">🔄</span><span class="btn-text">加载中...</span>';
    refreshBtn.style.opacity = "0.6";
  }

  try {
    let url = `/emails/${currentAccount}?folder=${folder}&page=${emailCurrentPage}&page_size=${emailPageSize}&sort_order=${sortOrder}`;

    if (forceRefresh) url += "&refresh=true";
    if (senderSearch)
      url += `&sender_search=${encodeURIComponent(senderSearch)}`;
    if (subjectSearch)
      url += `&subject_search=${encodeURIComponent(subjectSearch)}`;

    const data = await apiRequest(url);

    const newEmails = data.emails || [];
    const newEmailTotalCount = data.total_emails || 0;

    // 检测新邮件（仅在没有搜索条件时检测）
    if (oldEmails.length > 0 && !hasSearchCondition && !forceRefresh) {
      const newEmailsList = newEmails.filter(
        (email) => !oldEmailIds.has(email.message_id)
      );
      if (newEmailsList.length > 0) {
        const newCount = newEmailsList.length;
        const emailsWithCode = newEmailsList.filter((e) =>
          detectVerificationCode(e.subject || "", "")
        );
        const hasVerificationCode = emailsWithCode.length > 0;

        if (hasVerificationCode) {
          const firstCode = detectVerificationCode(
            emailsWithCode[0].subject || "",
            ""
          );
          if (firstCode) {
            try {
              if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(firstCode);
                console.log(`✅ [自动复制] 验证码已复制到剪切板: ${firstCode}`);
              }
            } catch (err) {
              console.error("❌ [自动复制] 复制失败:", err);
            }
          }
        }

        const vCodeMsg = hasVerificationCode
          ? ` (验证码: ${detectVerificationCode(
              emailsWithCode[0].subject || "",
              ""
            )} 已复制🔑)`
          : "";
        showNotification(
          `收到 ${newCount} 封新邮件${vCodeMsg}`,
          "success",
          "📬 新邮件提醒",
          hasVerificationCode ? 8000 : 5000
        );
      }
    }

    allEmails = newEmails;
    emailTotalCount = newEmailTotalCount;

    renderEmails(allEmails);
    updateEmailStats(allEmails);
    updateEmailPagination();
    
    // 显示缓存信息
    displayCacheInfo(data.from_cache, data.fetch_time_ms);

    if (document.getElementById("lastUpdateTime")) {
      document.getElementById("lastUpdateTime").textContent =
        new Date().toLocaleString();
    }

    if (forceRefresh && showLoading) {
      showNotification("邮件列表已刷新", "success", "✅ 刷新成功", 2000);
    }
  } catch (error) {
    console.error("加载邮件失败:", error);
    if (allEmails.length === 0) {
      emailsList.innerHTML =
        '<tr><td colspan="4" style="padding: 40px; text-align: center;"><div class="error">❌ 加载失败: ' +
        error.message +
        "</div></td></tr>";
    }
    showNotification(
      "加载邮件失败: " + error.message,
      "error",
      "❌ 错误",
      3000
    );
  } finally {
    isLoadingEmails = false;

    if (refreshBtn) {
      refreshBtn.disabled = false;
      refreshBtn.innerHTML = '<span>🔄</span><span class="btn-text">刷新</span>';
      refreshBtn.style.opacity = "1";
    }
  }
}

// 渲染邮件列表
function renderEmails(emails) {
  const emailsList = document.getElementById("emailsList");

  if (!emails || emails.length === 0) {
    // 检查是否有搜索条件
    const senderSearch = document.getElementById("senderSearch")?.value || "";
    const subjectSearch = document.getElementById("subjectSearch")?.value || "";
    const hasSearchCondition = senderSearch || subjectSearch;
    
    const emptyMessage = hasSearchCondition 
      ? '没有找到符合搜索条件的邮件' 
      : '暂无邮件';
    
    emailsList.innerHTML =
      `<tr><td colspan="4" style="padding: 40px; text-align: center; color: #64748b;">${emptyMessage}</td></tr>`;
    return;
  }

  emailsList.innerHTML = emails
    .map((email) => createEmailTableRow(email))
    .join("");
}

// 创建邮件表格行
function createEmailTableRow(email) {
  const unreadClass = email.is_read ? "" : "unread";
  const attachmentIcon = email.has_attachments
    ? '<span title="包含附件">📎</span>'
    : "";

  const verificationCode = detectVerificationCode(email.subject || "", "");
  const vCodeIcon = verificationCode
    ? `<span title="验证码: ${verificationCode}">🔑</span>`
    : "";

  const verificationCodeBtn = verificationCode
    ? `<button class="btn-verification-code" onclick="copyVerificationCode('${verificationCode}')" title="复制验证码">
            🔑
        </button>`
    : "";

  // 提取发件人名称（邮箱@前的部分）
  const senderName = email.from_email.split("@")[0];
  const senderDomain = "@" + (email.from_email.split("@")[1] || "");

  // 未读标记
  const unreadBadge = !email.is_read
    ? '<span class="email-unread-badge" title="未读邮件"></span>'
    : "";

  return `
        <tr class="clickable ${unreadClass}">
            <td onclick="showEmailDetail('${email.message_id}')">
                <div class="email-sender-cell">
                    <div class="email-sender-avatar">${
                      email.sender_initial
                    }</div>
                    <div class="email-sender-info">
                        <span class="email-sender-name" title="${
                          email.from_email
                        }">${senderName}</span>
                        <span class="email-sender-email" title="${
                          email.from_email
                        }">${senderDomain}</span>
                    </div>
                </div>
            </td>
            <td onclick="showEmailDetail('${email.message_id}')">
                <div class="email-subject-cell">
                    ${unreadBadge}
                    <span class="email-subject" title="${
                      email.subject || "(无主题)"
                    }">${email.subject || "(无主题)"}</span>
                    <div class="email-icons">
                        ${attachmentIcon}
                        ${vCodeIcon}
                    </div>
                </div>
            </td>
            <td onclick="showEmailDetail('${email.message_id}')">
                <span class="email-date" title="${new Date(
                  email.date
                ).toLocaleString()}">${formatEmailDate(email.date)}</span>
            </td>
            <td>
                <div class="email-actions-cell">
                    <button class="btn btn-primary btn-sm" onclick="showEmailDetail('${
                      email.message_id
                    }')" title="查看邮件">
                        👁️
                    </button>
                    ${verificationCodeBtn}
                </div>
            </td>
        </tr>
    `;
}

// 显示邮件详情
async function showEmailDetail(messageId) {
  const modal = document.getElementById("emailModal");
  const modalTitle = document.getElementById("emailModalTitle");
  const modalContent = document.getElementById("emailModalContent");

  if (!modal || !modalTitle || !modalContent) return;

  modal.classList.remove("hidden");
  modalTitle.textContent = "邮件详情";

  const cachedEmail = allEmails.find((e) => e.message_id === messageId);

  if (cachedEmail) {
    console.log("✅ [缓存命中] 使用缓存数据快速显示邮件详情");

    modalTitle.textContent = cachedEmail.subject || "(无主题)";
    modalContent.innerHTML = `
            <div style="background: #f0f9ff; padding: 8px 12px; border-radius: 4px; margin-bottom: 10px; font-size: 0.85em; color: #0369a1;">
                ⚡ 快速预览模式 · 正在加载完整内容...
            </div>
            <div class="email-detail-meta">
                <p><strong>发件人:</strong> ${cachedEmail.from_email}</p>
                <p><strong>日期:</strong> ${formatEmailDate(
                  cachedEmail.date
                )} (${new Date(cachedEmail.date).toLocaleString()})</p>
                <p><strong>邮件ID:</strong> ${cachedEmail.message_id}</p>
            </div>
            <div style="padding: 20px; text-align: center; color: #64748b;">
                <div class="loading-spinner"></div>
                <p style="margin-top: 10px;">正在加载邮件正文...</p>
            </div>
        `;
  } else {
    modalContent.innerHTML =
      '<div class="loading"><div class="loading-spinner"></div>正在加载邮件详情...</div>';
  }

  try {
    const data = await apiRequest(`/emails/${currentAccount}/${messageId}`);

    const bodyText = data.body_plain || data.body_html || "";
    const verificationCode = detectVerificationCode(
      data.subject || "",
      bodyText
    );

    const verificationCodeHtml = verificationCode
      ? `
            <div style="background: #dcfce7; border-left: 4px solid #10b981; padding: 12px; margin: 10px 0; border-radius: 4px;">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div>
                        <strong style="color: #059669;">🔑 检测到验证码:</strong>
                        <code style="background: #fff; padding: 4px 8px; border-radius: 4px; margin: 0 8px; font-size: 1.1em; font-weight: bold; color: #047857;">${verificationCode}</code>
                    </div>
                    <button class="btn-verification-code" onclick="copyVerificationCode('${verificationCode}')">
                        📋 复制
                    </button>
                </div>
            </div>
        `
      : "";

    modalTitle.textContent = data.subject || "(无主题)";
    modalContent.innerHTML = `
            ${verificationCodeHtml}
            <div class="email-detail-meta">
                <p><strong>发件人:</strong> ${data.from_email}</p>
                <p><strong>收件人:</strong> ${data.to_email}</p>
                <p><strong>日期:</strong> ${formatEmailDate(
                  data.date
                )} (${new Date(data.date).toLocaleString()})</p>
                <p><strong>邮件ID:</strong> ${data.message_id}</p>
            </div>
            ${renderEmailContent(data)}
        `;
  } catch (error) {
    console.error("❌ [加载失败]", error);
    modalContent.innerHTML =
      '<div class="error">❌ 加载失败: ' + error.message + "</div>";
  }
}

// 渲染邮件内容
function renderEmailContent(email) {
  const hasHtml = email.body_html && email.body_html.trim();
  const hasPlain = email.body_plain && email.body_plain.trim();

  if (!hasHtml && !hasPlain) {
    return '<p style="color: #9ca3af; font-style: italic;">此邮件无内容</p>';
  }

  if (hasHtml) {
    const wrappedHtml = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    * { box-sizing: border-box; }
                    body {
                        margin: 0;
                        padding: 16px;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        font-size: 14px;
                        line-height: 1.6;
                        color: #334155;
                        background: #ffffff;
                        overflow-wrap: break-word;
                        word-wrap: break-word;
                    }
                    img { max-width: 100%; height: auto; }
                    table { max-width: 100%; border-collapse: collapse; }
                    pre { white-space: pre-wrap; word-wrap: break-word; overflow-x: auto; }
                </style>
            </head>
            <body>
                ${email.body_html}
            </body>
            </html>
        `;

    const sanitizedHtml = wrappedHtml.replace(/"/g, "&quot;");

    return `
            <div class="email-content-tabs">
                <button class="content-tab active" onclick="showEmailContentTab('html', this)">HTML视图</button>
                ${
                  hasPlain
                    ? '<button class="content-tab" onclick="showEmailContentTab(\'plain\', this)">纯文本</button>'
                    : ""
                }
                <button class="content-tab" onclick="showEmailContentTab('raw', this)">源码</button>
            </div>

            <div class="email-content-body">
                <div id="htmlContent">
                    <iframe 
                        srcdoc="${sanitizedHtml}" 
                        style="width: 100%; min-height: 500px; max-height: 800px; border: 1px solid #e2e8f0; border-radius: 6px; background: white;" 
                        sandbox="allow-same-origin allow-popups"
                        onload="this.style.height = (this.contentWindow.document.body.scrollHeight + 40) + 'px'">
                    </iframe>
                </div>
                ${
                  hasPlain
                    ? `<div id="plainContent" class="hidden"><pre style="background: #f8fafc; padding: 16px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;">${email.body_plain}</pre></div>`
                    : ""
                }
                <div id="rawContent" class="hidden"><pre style="background: #1e293b; color: #e2e8f0; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 12px; white-space: pre-wrap; word-wrap: break-word;">${email.body_html
                  .replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;")}</pre></div>
            </div>
        `;
  } else {
    return `<div class="email-content-body"><pre style="background: #f8fafc; padding: 16px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;">${email.body_plain}</pre></div>`;
  }
}

// 切换邮件内容标签
function showEmailContentTab(type, targetElement = null) {
  document
    .querySelectorAll(".content-tab")
    .forEach((tab) => tab.classList.remove("active"));

  if (targetElement) {
    targetElement.classList.add("active");
  }

  document
    .querySelectorAll("#htmlContent, #plainContent, #rawContent")
    .forEach((content) => {
      content.classList.add("hidden");
    });

  const contentElement = document.getElementById(type + "Content");
  if (contentElement) {
    contentElement.classList.remove("hidden");
  }
}

// 邮件分页函数
function changeEmailPageSize() {
  const pageSizeElement = document.getElementById("emailPageSize");
  if (pageSizeElement) {
    emailPageSize = parseInt(pageSizeElement.value);
    emailCurrentPage = 1;
    loadEmails();
  }
}

function emailNextPage() {
  const totalPages = Math.ceil(emailTotalCount / emailPageSize);
  if (emailCurrentPage < totalPages) {
    emailCurrentPage++;
    loadEmails();
  }
}

function emailPrevPage() {
  if (emailCurrentPage > 1) {
    emailCurrentPage--;
    loadEmails();
  }
}

function updateEmailPagination() {
  const totalPages = Math.ceil(emailTotalCount / emailPageSize);
  const displayElement = document.getElementById("emailCurrentPageDisplay");
  const infoElement = document.getElementById("emailTotalInfo");
  const prevBtn = document.getElementById("emailPrevBtn");
  const nextBtn = document.getElementById("emailNextBtn");

  if (displayElement) displayElement.textContent = emailCurrentPage;
  if (infoElement)
    infoElement.textContent = `/ 共 ${totalPages} 页 (总计 ${emailTotalCount} 封)`;
  if (prevBtn) prevBtn.disabled = emailCurrentPage === 1;
  if (nextBtn) nextBtn.disabled = emailCurrentPage >= totalPages;
}

function updateEmailStats(emails) {
  const total = emailTotalCount || emails.length;
  const unread = emails.filter((email) => !email.is_read).length;
  const today = emails.filter((email) => {
    const emailDate = new Date(email.date);
    const todayDate = new Date();
    return emailDate.toDateString() === todayDate.toDateString();
  }).length;
  const withAttachments = emails.filter(
    (email) => email.has_attachments
  ).length;

  const totalElement = document.getElementById("totalEmailCount");
  const unreadElement = document.getElementById("unreadEmailCount");
  const todayElement = document.getElementById("todayEmailCount");
  const attachElement = document.getElementById("attachmentEmailCount");

  if (totalElement) totalElement.textContent = total;
  if (unreadElement) unreadElement.textContent = unread;
  if (todayElement) todayElement.textContent = today;
  if (attachElement) attachElement.textContent = withAttachments;
}

// 搜索和过滤
function searchAndLoadEmails() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    emailCurrentPage = 1;
    loadEmails();
  }, 500);
}

function clearSearchFilters() {
  const senderSearch = document.getElementById("senderSearch");
  const subjectSearch = document.getElementById("subjectSearch");
  const folderFilter = document.getElementById("folderFilter");
  const sortOrder = document.getElementById("sortOrder");

  if (senderSearch) senderSearch.value = "";
  if (subjectSearch) subjectSearch.value = "";
  if (folderFilter) folderFilter.value = "all";
  if (sortOrder) sortOrder.value = "desc";

  emailCurrentPage = 1;
  loadEmails();
}

/**
 * 显示缓存信息
 */
function displayCacheInfo(fromCache, fetchTimeMs) {
  // 查找或创建缓存信息容器
  let cacheInfoContainer = document.getElementById("cacheInfoContainer");
  
  if (!cacheInfoContainer) {
    // 在邮件列表上方创建缓存信息容器
    const emailsTable = document.querySelector(".emails-table");
    if (!emailsTable) return;
    
    cacheInfoContainer = document.createElement("div");
    cacheInfoContainer.id = "cacheInfoContainer";
    cacheInfoContainer.className = "cache-info-container";
    emailsTable.parentNode.insertBefore(cacheInfoContainer, emailsTable);
  }
  
  // 构建缓存信息HTML
  const cacheSource = fromCache ? "📦 缓存" : "🌐 实时";
  const cacheClass = fromCache ? "from-cache" : "from-server";
  const timeDisplay = fetchTimeMs !== null && fetchTimeMs !== undefined ? `⏱️ ${fetchTimeMs}ms` : "";
  
  cacheInfoContainer.innerHTML = `
    <div class="cache-info">
      <span class="cache-badge ${cacheClass}">${cacheSource}</span>
      ${timeDisplay ? `<span class="fetch-time">${timeDisplay}</span>` : ""}
    </div>
  `;
}

console.log("✅ [Emails] 邮件管理模块加载完成");
