// 账户管理模块
let currentAccount = null;
let accounts = [];
let accountsLoaded = false;
let accountsCache = null;
let accountsCacheTime = 0;
const ACCOUNTS_CACHE_DURATION = 30000;

let accountsCurrentPage = 1;
let accountsPageSize = 10;
let accountsTotalPages = 0;
let accountsTotalCount = 0;
let currentEmailSearch = "";
let currentTagSearch = "";
let currentRefreshStatusFilter = "all";
let currentRefreshStartDate = "";
let currentRefreshEndDate = "";

// 全局变量，用于存储当前编辑的账户信息
let currentEditAccount = null;
let currentEditTags = [];

// 智能加载账户：优先使用缓存
async function loadAccountsSmart(forceRefresh = false) {
  const now = Date.now();
  const cacheValid =
    accountsCache && now - accountsCacheTime < ACCOUNTS_CACHE_DURATION;

  if (!forceRefresh && cacheValid && accountsLoaded) {
    console.log("✅ [账户列表] 使用缓存数据，秒开！");
    renderAccountsFromCache();
    return;
  }

  console.log("🔄 [账户列表] 从服务器加载数据");
  await loadAccounts(accountsCurrentPage, false, true);
}

function renderAccountsFromCache() {
  if (!accountsCache) return;

  const accountsList = document.getElementById("accountsList");
  const accountsPagination = document.getElementById("accountsPagination");

  accountsList.innerHTML = accountsCache.html;
  accountsPagination.style.display = "block";
  updateAccountsPagination();
  updateAccountsStats();
}

async function loadAccounts(page = 1, resetSearch = false, showLoading = true) {
  if (resetSearch) {
    currentEmailSearch = "";
    currentTagSearch = "";
    currentRefreshStatusFilter = "all";
    document.getElementById("emailSearch").value = "";
    document.getElementById("tagSearch").value = "";
    document.getElementById("refreshStatusFilter").value = "all";
    page = 1;
    accountsCache = null;
    accountsLoaded = false;
  }

  accountsCurrentPage = page;

  const accountsList = document.getElementById("accountsList");
  const accountsStats = document.getElementById("accountsStats");
  const accountsPagination = document.getElementById("accountsPagination");

  if (showLoading) {
    accountsList.innerHTML = `
            <div class="accounts-table-container">
                <div class="loading">
                    <div class="loading-spinner"></div>
                    正在加载账户列表...
                </div>
            </div>
        `;
  }
  accountsStats.style.display = "none";
  accountsPagination.style.display = "none";

  try {
    const params = new URLSearchParams({
      page: accountsCurrentPage,
      page_size: accountsPageSize,
    });

    if (currentEmailSearch) params.append("email_search", currentEmailSearch);
    if (currentTagSearch) params.append("tag_search", currentTagSearch);

    if (
      currentRefreshStatusFilter &&
      currentRefreshStatusFilter !== "all" &&
      currentRefreshStatusFilter !== "custom"
    ) {
      params.append("refresh_status", currentRefreshStatusFilter);
    }

    if (
      currentRefreshStatusFilter === "custom" &&
      currentRefreshStartDate &&
      currentRefreshEndDate
    ) {
      params.append("refresh_start_date", currentRefreshStartDate);
      params.append("refresh_end_date", currentRefreshEndDate);
    }

    const data = await apiRequest(`/accounts?${params.toString()}`);

    accounts = data.accounts || [];
    accountsTotalCount = data.total_accounts || 0;
    accountsLoaded = true;
    accountsTotalPages = data.total_pages || 0;

    updateAccountsStats();

    if (accounts.length === 0) {
      accountsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <div class="empty-state-text">暂无符合条件的账户</div>
                    <div class="empty-state-hint">尝试添加新账户或调整筛选条件</div>
                </div>
            `;
      return;
    }

    const accountsRows = accounts
      .map((account) => {
        // 标签HTML
        const tagsHtml =
          account.tags && account.tags.length > 0
            ? `<div class="account-tags">${account.tags
                .map((tag) => `<span class="account-tag">${tag}</span>`)
                .join("")}</div>`
            : '<div class="account-tags empty">无标签</div>';

        // 刷新状态
        const refreshStatus = account.refresh_status || "pending";
        const refreshStatusIcon =
          refreshStatus === "success"
            ? "✅"
            : refreshStatus === "failed"
            ? "❌"
            : "⏳";
        const refreshStatusText =
          refreshStatus === "success"
            ? "成功"
            : refreshStatus === "failed"
            ? "失败"
            : "待刷新";
        const refreshTime = formatRefreshTime(account.last_refresh_time);

        // 账户状态
        const statusClass = account.status === "active" ? "active" : "inactive";
        const statusText = account.status === "active" ? "正常" : "异常";

        // Client ID截取（显示前8位）
        const clientIdShort = account.client_id
          ? account.client_id.length > 12
            ? account.client_id.substring(0, 12) + "..."
            : account.client_id
          : "N/A";

        // 检查是否已选中
        const isChecked = selectedAccounts.has(account.email_id);

        // 检查是否支持 Graph API（发送邮件需要）
        const supportsGraphApi = account.api_method === "graph_api";

        return `
                <tr class="clickable" onclick="viewAccountEmails('${
                  account.email_id
                }')" oncontextmenu="showAccountContextMenu(event, '${
          account.email_id
        }')">
                    <td>
                        <div class="account-cell-with-checkbox">
                            <input type="checkbox" class="account-checkbox" 
                                   data-email-id="${account.email_id}"
                                   ${isChecked ? "checked" : ""}
                                   onclick="event.stopPropagation()"
                                   onchange="toggleAccountSelection('${
                                     account.email_id
                                   }')" />
                        <div class="account-cell">
                            <div class="account-avatar">${account.email_id
                              .charAt(0)
                              .toUpperCase()}</div>
                            <div class="account-email-info">
                                <span class="account-email" title="${
                                  account.email_id
                                }">${account.email_id}</span>
                                <span class="account-client-id" title="${
                                  account.client_id
                                }">ID: ${clientIdShort}</span>
                                </div>
                            </div>
                        </div>
                    </td>
                    <td>
                        ${tagsHtml}
                    </td>
                    <td>
                        <span class="status-badge ${statusClass}">
                            <span class="status-indicator"></span>
                            ${statusText}
                        </span>
                    </td>
                    <td>
                        <div class="refresh-status-cell">
                            <span class="refresh-status-icon ${refreshStatus}">${refreshStatusIcon}</span>
                            <div class="refresh-time-info">
                                <span class="refresh-time">${refreshTime}</span>
                                <span class="refresh-status-text">${refreshStatusText}</span>
                            </div>
                        </div>
                    </td>
                    <td onclick="event.stopPropagation()">
                        <div class="account-actions">
                            <button class="btn btn-primary btn-sm" onclick="viewAccountEmails('${
                              account.email_id
                            }')" title="查看邮件">
                                <span>📧</span>
                            </button>
                            ${
                              supportsGraphApi
                                ? `<button class="btn btn-success btn-sm" onclick="openSendEmailModal('${account.email_id}')" title="发送邮件">
                                    <span>✉️</span>
                                </button>`
                                : `<button class="btn btn-secondary btn-sm" onclick="showGraphApiRequiredNotice('${account.email_id}')" title="发送邮件需要Graph API" style="opacity: 0.6;">
                                    <span>✉️</span>
                                </button>`
                            }
                            <button class="btn btn-secondary btn-sm" onclick="editAccountTags('${
                              account.email_id
                            }')" title="管理标签">
                                <span>🏷️</span>
                            </button>
                            <button class="btn btn-info btn-sm" onclick="refreshAccountToken('${
                              account.email_id
                            }')" title="刷新Token">
                                <span>🔄</span>
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="deleteAccount('${
                              account.email_id
                            }')" title="删除账户">
                                <span>🗑️</span>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
      })
      .join("");

    accountsList.innerHTML = `
            <div class="accounts-table-container">
                <table class="accounts-table">
                    <thead>
                        <tr>
                            <th style="width: 30%;">账户信息</th>
                            <th style="width: 20%;">标签</th>
                            <th style="width: 12%;">状态</th>
                            <th style="width: 18%;">刷新状态</th>
                            <th style="width: 20%;">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${accountsRows}
                    </tbody>
                </table>
            </div>
        `;
    accountsCache = {
      html: accountsList.innerHTML,
      data: accounts,
      totalCount: accountsTotalCount,
    };
    accountsCacheTime = Date.now();

    updateAccountsPagination();
  } catch (error) {
    accountsList.innerHTML = `
            <div class="accounts-table-container">
                <div class="empty-state">
                    <div class="empty-state-icon">⚠️</div>
                    <div class="empty-state-text">加载失败</div>
                    <div class="empty-state-hint">${error.message}</div>
                </div>
            </div>
        `;
  }
}

async function addAccount() {
  const email = document.getElementById("email").value.trim();
  const refreshToken = document.getElementById("refreshToken").value.trim();
  const clientId = document.getElementById("clientId").value.trim();
  const tagsInput = document.getElementById("accountTags").value.trim();

  const tags = tagsInput
    ? tagsInput
        .split(",")
        .map((tag) => tag.trim())
        .filter((tag) => tag)
    : [];

  if (!email || !refreshToken || !clientId) {
    showNotification("请填写所有必填字段", "warning");
    return;
  }

  const addBtn = document.getElementById("addAccountBtn");
  addBtn.disabled = true;
  addBtn.innerHTML = "<span>⏳</span> 添加中...";

  try {
    const response = await apiRequest("/accounts", {
      method: "POST",
      body: JSON.stringify({
        email,
        refresh_token: refreshToken,
        client_id: clientId,
        tags: tags,
      }),
    });

    showSuccess("账户添加成功");
    clearAddAccountForm();
    showPage("accounts");
    loadAccounts();
  } catch (error) {
    showNotification("添加账户失败: " + error.message, "error");
  } finally {
    addBtn.disabled = false;
    addBtn.innerHTML = "<span>➕</span> 添加账户";
  }
}

async function deleteAccount(emailId) {
  if (!confirm(`确定要删除账户 ${emailId} 吗？`)) {
    return;
  }

  try {
    await apiRequest(`/accounts/${emailId}`, { method: "DELETE" });
    showSuccess("账户删除成功");
    loadAccounts(accountsCurrentPage);
  } catch (error) {
    showError("删除账户失败: " + error.message);
  }
}

async function refreshAccountToken(emailId) {
  if (!confirm(`确定要手动刷新账户 ${emailId} 的Token吗？`)) {
    return;
  }

  try {
    showNotification("正在刷新Token，请稍候...", "info");

    const response = await apiRequest(`/accounts/${emailId}/refresh-token`, {
      method: "POST",
    });

    showNotification("Token刷新成功！", "success");
    loadAccounts(accountsCurrentPage);
  } catch (error) {
    showNotification(`Token刷新失败: ${error.message}`, "error");
  }
}

// 批量刷新Token功能
async function showBatchRefreshDialog() {
  try {
    // 获取当前筛选条件下的账户数量
    const params = new URLSearchParams({
      page: 1,
      page_size: 1,
    });

    if (currentEmailSearch) {
      params.append("email_search", currentEmailSearch);
    }

    if (currentTagSearch) {
      params.append("tag_search", currentTagSearch);
    }

    if (
      currentRefreshStatusFilter &&
      currentRefreshStatusFilter !== "all" &&
      currentRefreshStatusFilter !== "custom"
    ) {
      params.append("refresh_status", currentRefreshStatusFilter);
    }

    // 添加自定义日期范围参数
    if (
      currentRefreshStatusFilter === "custom" &&
      currentRefreshStartDate &&
      currentRefreshEndDate
    ) {
      params.append("refresh_start_date", currentRefreshStartDate);
      params.append("refresh_end_date", currentRefreshEndDate);
    }

    const data = await apiRequest(`/accounts?${params.toString()}`);
    const totalAccounts = data.total_accounts || 0;

    if (totalAccounts === 0) {
      showNotification("当前筛选条件下没有账户需要刷新", "warning");
      return;
    }

    // 构建筛选条件说明
    let filterDesc = [];
    if (currentEmailSearch) {
      filterDesc.push(`邮箱包含"${currentEmailSearch}"`);
    }
    if (currentTagSearch) {
      filterDesc.push(`标签包含"${currentTagSearch}"`);
    }
    if (currentRefreshStatusFilter && currentRefreshStatusFilter !== "all") {
      if (currentRefreshStatusFilter === "custom") {
        const startDate = new Date(currentRefreshStartDate);
        const endDate = new Date(currentRefreshEndDate);
        filterDesc.push(
          `刷新时间在 ${startDate.toLocaleString(
            "zh-CN"
          )} 至 ${endDate.toLocaleString("zh-CN")} 之间`
        );
      } else {
        const statusMap = {
          never_refreshed: "从未刷新",
          success: "刷新成功",
          failed: "刷新失败",
          pending: "待刷新",
        };
        filterDesc.push(`状态为"${statusMap[currentRefreshStatusFilter]}"`);
      }
    }

    const filterText =
      filterDesc.length > 0
        ? `当前筛选条件：${filterDesc.join("、")}\n`
        : "当前筛选条件：全部账户\n";

    if (
      !confirm(
        `${filterText}将刷新 ${totalAccounts} 个账户的Token，确定继续吗？\n\n此操作可能需要较长时间，请耐心等待。`
      )
    ) {
      return;
    }

    await batchRefreshTokens();
  } catch (error) {
    showNotification(`获取账户信息失败: ${error.message}`, "error");
  }
}

async function batchRefreshTokens() {
  try {
    // 构建请求参数
    const params = new URLSearchParams();

    if (currentEmailSearch) {
      params.append("email_search", currentEmailSearch);
    }

    if (currentTagSearch) {
      params.append("tag_search", currentTagSearch);
    }

    if (
      currentRefreshStatusFilter &&
      currentRefreshStatusFilter !== "all" &&
      currentRefreshStatusFilter !== "custom"
    ) {
      params.append("refresh_status", currentRefreshStatusFilter);
    }

    // 添加自定义日期范围参数
    if (
      currentRefreshStatusFilter === "custom" &&
      currentRefreshStartDate &&
      currentRefreshEndDate
    ) {
      params.append("refresh_start_date", currentRefreshStartDate);
      params.append("refresh_end_date", currentRefreshEndDate);
    }

    showNotification("正在批量刷新Token，请稍候...", "info");

    const result = await apiRequest(
      `/accounts/batch-refresh-tokens?${params.toString()}`,
      {
        method: "POST",
      }
    );

    // 显示结果
    const successMsg = `批量刷新完成！\n总计: ${result.total_processed} 个账户\n成功: ${result.success_count} 个\n失败: ${result.failed_count} 个`;

    if (result.failed_count === 0) {
      showNotification(successMsg, "success");
    } else {
      // 如果有失败的，显示详细信息
      let detailMsg = successMsg + "\n\n失败账户：\n";
      result.details
        .filter((d) => d.status === "failed")
        .forEach((detail) => {
          detailMsg += `- ${detail.email}: ${detail.message}\n`;
        });
      showNotification(detailMsg, "warning");
    }

    // 刷新账户列表
    loadAccounts(accountsCurrentPage);
  } catch (error) {
    showNotification(`批量刷新失败: ${error.message}`, "error");
  }
}

// 更多账户管理函数...
function updateAccountsStats() {
  const accountsStats = document.getElementById("accountsStats");
  if (!accountsStats) return;

  const totalAccountsEl = document.getElementById("totalAccounts");
  const currentPageEl = document.getElementById("currentPage");

  if (totalAccountsEl) {
    totalAccountsEl.textContent = accountsTotalCount;
  }
  if (currentPageEl) {
    currentPageEl.textContent = accountsCurrentPage;
  }

  // 更新分页大小选择器
  const pageSizeSelect = document.getElementById("pageSizeSelect");
  if (pageSizeSelect) {
    pageSizeSelect.value = accountsPageSize.toString();
  }

  accountsStats.style.display = accountsTotalCount > 0 ? "flex" : "none";
}

function updateAccountsPagination() {
  const accountsPagination = document.getElementById("accountsPagination");
  if (!accountsPagination) return;

  const prevBtn = document.getElementById("prevPageBtn");
  const nextBtn = document.getElementById("nextPageBtn");
  const pageNumbers = document.getElementById("pageNumbers");

  if (accountsTotalPages <= 1) {
    accountsPagination.style.display = "none";
    return;
  }

  accountsPagination.style.display = "flex";

  if (prevBtn) {
    prevBtn.disabled = accountsCurrentPage <= 1;
  }
  if (nextBtn) {
    nextBtn.disabled = accountsCurrentPage >= accountsTotalPages;
  }
  if (pageNumbers) {
    pageNumbers.innerHTML = generatePageNumbers();
  }
}

function generatePageNumbers() {
  const maxVisiblePages = 5;
  let startPage = Math.max(
    1,
    accountsCurrentPage - Math.floor(maxVisiblePages / 2)
  );
  let endPage = Math.min(accountsTotalPages, startPage + maxVisiblePages - 1);

  if (endPage - startPage < maxVisiblePages - 1) {
    startPage = Math.max(1, endPage - maxVisiblePages + 1);
  }

  let html = "";

  if (startPage > 1) {
    html += `<span class="page-number" onclick="changePage(1)">1</span>`;
    if (startPage > 2) {
      html += `<span class="page-number disabled">...</span>`;
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    const activeClass = i === accountsCurrentPage ? "active" : "";
    html += `<span class="page-number ${activeClass}" onclick="changePage(${i})">${i}</span>`;
  }

  if (endPage < accountsTotalPages) {
    if (endPage < accountsTotalPages - 1) {
      html += `<span class="page-number disabled">...</span>`;
    }
    html += `<span class="page-number" onclick="changePage(${accountsTotalPages})">${accountsTotalPages}</span>`;
  }

  return html;
}

function changePage(direction) {
  let newPage;
  if (direction === "prev") {
    newPage = Math.max(1, accountsCurrentPage - 1);
  } else if (direction === "next") {
    newPage = Math.min(accountsTotalPages, accountsCurrentPage + 1);
  } else {
    newPage = parseInt(direction);
  }

  if (
    newPage !== accountsCurrentPage &&
    newPage >= 1 &&
    newPage <= accountsTotalPages
  ) {
    loadAccounts(newPage);
  }
}

function searchAccounts() {
  accountsCache = null;
  accountsLoaded = false;

  currentEmailSearch = document.getElementById("emailSearch").value.trim();
  currentTagSearch = document.getElementById("tagSearch").value.trim();
  currentRefreshStatusFilter = document.getElementById(
    "refreshStatusFilter"
  ).value;

  if (currentRefreshStatusFilter === "custom") {
    const startDateInput = document.getElementById("refreshStartDate").value;
    const endDateInput = document.getElementById("refreshEndDate").value;

    if (startDateInput && endDateInput) {
      const startDate = new Date(startDateInput);
      const endDate = new Date(endDateInput);

      if (startDate <= endDate) {
        currentRefreshStartDate = startDate.toISOString();
        currentRefreshEndDate = endDate.toISOString();
      } else {
        alert("起始时间不能晚于截止时间");
        return;
      }
    } else {
      alert("请选择起始时间和截止时间");
      return;
    }
  } else {
    currentRefreshStartDate = "";
    currentRefreshEndDate = "";
  }

  loadAccounts(1);
}

function clearSearch() {
  accountsCache = null;
  accountsLoaded = false;

  document.getElementById("emailSearch").value = "";
  document.getElementById("tagSearch").value = "";
  document.getElementById("refreshStatusFilter").value = "all";
  document.getElementById("refreshStartDate").value = "";
  document.getElementById("refreshEndDate").value = "";
  document.getElementById("customDateRangeContainer").style.display = "none";
  currentEmailSearch = "";
  currentTagSearch = "";
  currentRefreshStatusFilter = "all";
  currentRefreshStartDate = "";
  currentRefreshEndDate = "";
  loadAccounts(1);
}

// ============================================================================
// 批量操作功能
// ============================================================================

let selectedAccounts = new Set();

// 切换全选
function toggleSelectAll() {
  const selectAllCheckbox = document.getElementById("selectAllAccounts");
  const checkboxes = document.querySelectorAll(".account-checkbox");

  checkboxes.forEach((checkbox) => {
    checkbox.checked = selectAllCheckbox.checked;
    const emailId = checkbox.dataset.emailId;
    if (selectAllCheckbox.checked) {
      selectedAccounts.add(emailId);
    } else {
      selectedAccounts.delete(emailId);
    }
  });

  updateBatchDeleteButton();
}

// 切换单个账户选择
function toggleAccountSelection(emailId) {
  const checkbox = document.querySelector(
    `.account-checkbox[data-email-id="${emailId}"]`
  );
  if (checkbox.checked) {
    selectedAccounts.add(emailId);
  } else {
    selectedAccounts.delete(emailId);
  }

  // 更新全选复选框状态
  const selectAllCheckbox = document.getElementById("selectAllAccounts");
  const checkboxes = document.querySelectorAll(".account-checkbox");
  const allChecked = Array.from(checkboxes).every((cb) => cb.checked);
  selectAllCheckbox.checked = allChecked && checkboxes.length > 0;

  updateBatchDeleteButton();
}

// 更新批量删除按钮显示状态
function updateBatchDeleteButton() {
  const batchDeleteBtn = document.getElementById("batchDeleteBtn");
  const selectedCountContainer = document.getElementById(
    "selectedCountContainer"
  );
  const selectedCountSpan = document.getElementById("selectedCount");

  if (selectedAccounts.size > 0) {
    batchDeleteBtn.style.display = "inline-flex";
    selectedCountContainer.style.display = "inline";
    selectedCountSpan.textContent = selectedAccounts.size;
  } else {
    batchDeleteBtn.style.display = "none";
    selectedCountContainer.style.display = "none";
  }
}

// 批量删除账户
async function batchDeleteAccounts() {
  if (selectedAccounts.size === 0) {
    showNotification("请先选择要删除的账户", "warning");
    return;
  }

  const emailIds = Array.from(selectedAccounts);
  const confirmMsg = `确定要删除选中的 ${
    emailIds.length
  } 个账户吗？\n\n${emailIds.slice(0, 5).join("\n")}${
    emailIds.length > 5 ? "\n..." : ""
  }`;

  if (!confirm(confirmMsg)) {
    return;
  }

  const batchDeleteBtn = document.getElementById("batchDeleteBtn");
  const originalText = batchDeleteBtn.innerHTML;
  batchDeleteBtn.disabled = true;
  batchDeleteBtn.innerHTML =
    "<span>⏳</span> <span class='btn-text'>删除中...</span>";

  try {
    showNotification(`正在批量删除 ${emailIds.length} 个账户...`, "info");

    const response = await apiRequest("/accounts/batch-delete", {
      method: "POST",
      body: JSON.stringify({ email_ids: emailIds }),
    });

    const successCount = response.success_count || 0;
    const failedCount = response.failed_count || 0;

    if (failedCount > 0) {
      showNotification(
        `批量删除完成：成功 ${successCount} 个，失败 ${failedCount} 个`,
        "warning"
      );
    } else {
      showSuccess(`成功删除 ${successCount} 个账户`);
    }

    // 清空选择
    selectedAccounts.clear();
    document.getElementById("selectAllAccounts").checked = false;
    updateBatchDeleteButton();

    // 刷新列表
    loadAccounts(accountsCurrentPage);
  } catch (error) {
    showError("批量删除失败: " + error.message);
  } finally {
    batchDeleteBtn.disabled = false;
    batchDeleteBtn.innerHTML = originalText;
  }
}

// ============================================================================
// 分页大小切换功能
// ============================================================================

// 切换分页大小
function changePageSize() {
  const pageSizeSelect = document.getElementById("pageSizeSelect");
  const newPageSize = parseInt(pageSizeSelect.value);

  if (newPageSize !== accountsPageSize) {
    accountsPageSize = newPageSize;
    accountsCache = null;
    accountsLoaded = false;

    // 清空选择
    selectedAccounts.clear();
    document.getElementById("selectAllAccounts").checked = false;
    updateBatchDeleteButton();

    // 重新加载第一页
    loadAccounts(1);
  }
}

// ============================================================================
// Graph API 提示功能
// ============================================================================

/**
 * 显示需要 Graph API 的提示
 */
function showGraphApiRequiredNotice(emailId) {
  const message = `
    <div style="margin-bottom: 12px;">
      <strong>发送邮件功能需要 Graph API 支持</strong>
    </div>
    <div style="margin-bottom: 12px; color: #64748b; font-size: 0.875rem;">
      当前账户 <strong>${emailId}</strong> 使用的是 IMAP 方式，不支持发送邮件。
    </div>
    <div style="margin-bottom: 12px; color: #64748b; font-size: 0.875rem;">
      要使用发送邮件功能，需要：
    </div>
    <ul style="margin: 8px 0 12px 20px; color: #64748b; font-size: 0.875rem;">
      <li>确保该账户具有 Graph API 权限（Mail.ReadWrite、Mail.Send）</li>
      <li>点击下方按钮检测并启用 Graph API</li>
    </ul>
    <div style="margin-top: 16px;">
      <button class="btn btn-primary" onclick="detectAndEnableGraphApi('${emailId}')">
        <span>🔍</span> 检测并启用 Graph API
      </button>
    </div>
  `;

  showNotification(message, "warning", 10000);
}

/**
 * 检测并启用 Graph API
 */
async function detectAndEnableGraphApi(emailId) {
  try {
    showNotification("正在检测 Graph API 可用性...", "info");

    const response = await apiRequest(
      `/accounts/${emailId}/detect-api-method`,
      {
        method: "POST",
      }
    );

    if (response.api_method === "graph_api") {
      showSuccess(
        `账户 ${emailId} 已成功启用 Graph API！现在可以使用发送邮件功能了。`
      );
      // 刷新账户列表以更新按钮状态
      loadAccounts(accountsCurrentPage);
    } else {
      showNotification(
        `该账户不支持 Graph API。请检查账户权限配置，确保具有 Mail.ReadWrite 和 Mail.Send 权限。`,
        "warning",
        8000
      );
    }
  } catch (error) {
    showError(`检测失败: ${error.message}`);
  }
}
