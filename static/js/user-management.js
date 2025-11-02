// user-management.js - 用户管理页面脚本

// 全局变量
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;
let editingUserId = null;
let allAccounts = [];
let filteredAccounts = [];
let displayedAccounts = [];
let selectedAccountsSet = new Set(); // 存储所有选中的账户ID
let accountsCurrentPage = 1;
let accountsPageSize = 20;
let accountsTotalPages = 1;
let searchTimeout = null;

// 权限定义
const PERMISSIONS = {
  view_emails: "查看邮件",
  send_emails: "发送邮件",
  delete_emails: "删除邮件",
  manage_accounts: "管理账户",
  view_admin_panel: "访问管理面板",
  manage_users: "管理用户",
  manage_cache: "管理缓存",
  manage_config: "管理系统配置",
};

// ============================================================================
// 初始化
// ============================================================================

window.addEventListener("load", async function () {
  // 检查用户是否是管理员
  if (!isAdmin()) {
    showNotification("您没有权限访问此页面", "error");
    setTimeout(() => {
      window.location.href = "/";
    }, 2000);
    return;
  }

  await loadAccounts();
  await loadUsers();
});

// ============================================================================
// 通知函数
// ============================================================================

function showNotification(message, type = "info") {
  const notification = document.getElementById("notification");
  if (!notification) return;

  notification.textContent = message;
  notification.className = `notification ${type} show`;

  setTimeout(() => {
    notification.classList.remove("show");
  }, 3000);
}

// ============================================================================
// 加载数据
// ============================================================================

// 加载所有账户（用于绑定）
async function loadAccounts() {
  try {
    let page = 1;
    let hasMore = true;
    allAccounts = [];

    while (hasMore) {
      const response = await apiRequest(`/accounts?page=${page}&page_size=100`);
      if (response && response.accounts) {
        allAccounts = allAccounts.concat(response.accounts);

        if (
          response.accounts.length < 100 ||
          allAccounts.length >= response.total_accounts
        ) {
          hasMore = false;
        } else {
          page++;
        }
      } else {
        hasMore = false;
      }
    }
  } catch (error) {
    console.error("Failed to load accounts:", error);
  }
}

// 加载用户列表
async function loadUsers() {
  try {
    const roleFilter = document.getElementById("roleFilter").value;
    const searchInput = document.getElementById("searchInput").value;

    let url = `/admin/users?page=${currentPage}&page_size=${pageSize}`;
    if (roleFilter) url += `&role_filter=${roleFilter}`;
    if (searchInput) url += `&search=${encodeURIComponent(searchInput)}`;

    const response = await apiRequest(url);

    if (response) {
      displayUsers(response.users);
      updatePagination(response.page, response.total_pages);
    }
  } catch (error) {
    showNotification("加载用户列表失败: " + error.message, "error");
  }
}

// ============================================================================
// 显示数据
// ============================================================================

// 在表格中显示用户
function displayUsers(users) {
  const tbody = document.getElementById("usersTableBody");

  if (!users || users.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" class="empty-state">
          <div>暂无用户数据</div>
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = users
    .map(
      (user) => `
    <tr>
      <td>${user.id}</td>
      <td><strong>${user.username}</strong></td>
      <td>${user.email || "-"}</td>
      <td>
        <span class="role-badge role-${user.role}">
          ${user.role === "admin" ? "管理员" : "普通用户"}
        </span>
      </td>
      <td>${user.bound_accounts ? user.bound_accounts.length : 0}</td>
      <td>
        <span class="status-badge status-${
          user.is_active ? "active" : "inactive"
        }">
          ${user.is_active ? "启用" : "禁用"}
        </span>
      </td>
      <td>${new Date(user.created_at).toLocaleString("zh-CN")}</td>
      <td>
        <div class="actions">
          <button class="btn btn-sm btn-primary" onclick="editUser('${
            user.username
          }')">
            编辑
          </button>
          <button class="btn btn-sm btn-secondary" onclick="changePassword('${
            user.username
          }')">
            改密码
          </button>
          <button class="btn btn-sm btn-danger" onclick="deleteUser('${
            user.username
          }')">
            删除
          </button>
        </div>
      </td>
    </tr>
  `
    )
    .join("");
}

// 更新分页信息
function updatePagination(page, total) {
  currentPage = page;
  totalPages = total;

  document.getElementById(
    "pageInfo"
  ).textContent = `第 ${page} 页 / 共 ${total} 页`;
  document.getElementById("prevBtn").disabled = page <= 1;
  document.getElementById("nextBtn").disabled = page >= total;
}

// ============================================================================
// 分页控制
// ============================================================================

function previousPage() {
  if (currentPage > 1) {
    currentPage--;
    loadUsers();
  }
}

function nextPage() {
  if (currentPage < totalPages) {
    currentPage++;
    loadUsers();
  }
}

// ============================================================================
// 搜索和筛选
// ============================================================================

// 搜索（带防抖）
function handleSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    currentPage = 1;
    loadUsers();
  }, 500);
}

// 重置筛选
function resetFilters() {
  document.getElementById("searchInput").value = "";
  document.getElementById("roleFilter").value = "";
  currentPage = 1;
  loadUsers();
}

// ============================================================================
// 用户模态框操作
// ============================================================================

// 显示创建用户模态框
function showCreateUserModal() {
  editingUserId = null;
  document.getElementById("modalTitle").textContent = "创建用户";
  document.getElementById("submitBtn").textContent = "创建用户";
  document.getElementById("userForm").reset();
  document.getElementById("passwordGroup").style.display = "block";
  document.getElementById("password").required = true;

  // 隐藏修改密码区域（新建用户时）
  document.getElementById("changePasswordGroup").style.display = "none";

  loadPermissionsGrid();
  loadAccountsCheckboxes();

  document.getElementById("userModal").classList.add("show");
}

// 编辑用户
async function editUser(username) {
  try {
    const response = await apiRequest(`/admin/users/${username}`);

    if (response) {
      editingUserId = username;
      document.getElementById("modalTitle").textContent = "编辑用户";
      document.getElementById("submitBtn").textContent = "保存更改";

      document.getElementById("username").value = response.username;
      document.getElementById("username").readOnly = true;
      document.getElementById("email").value = response.email || "";
      document.getElementById("role").value = response.role;
      document.getElementById("isActive").checked = response.is_active;

      // 隐藏密码字段，显示修改密码选项
      document.getElementById("passwordGroup").style.display = "none";
      document.getElementById("password").required = false;
      document.getElementById("changePasswordGroup").style.display = "block";

      // 重置密码修改字段
      document.getElementById("changePasswordCheckbox").checked = false;
      document.getElementById("newPasswordFields").style.display = "none";
      document.getElementById("newPassword").value = "";
      document.getElementById("confirmNewPassword").value = "";
      document.getElementById("newPassword").required = false;
      document.getElementById("confirmNewPassword").required = false;

      loadPermissionsGrid(response.permissions);
      loadAccountsCheckboxes(response.bound_accounts);

      handleRoleChange();

      document.getElementById("userModal").classList.add("show");
    }
  } catch (error) {
    showNotification("加载用户信息失败: " + error.message, "error");
  }
}

// 切换密码字段显示
function togglePasswordFields() {
  const checkbox = document.getElementById("changePasswordCheckbox");
  const fields = document.getElementById("newPasswordFields");
  const newPasswordInput = document.getElementById("newPassword");
  const confirmPasswordInput = document.getElementById("confirmNewPassword");

  if (checkbox.checked) {
    fields.style.display = "block";
    newPasswordInput.required = true;
    confirmPasswordInput.required = true;
  } else {
    fields.style.display = "none";
    newPasswordInput.required = false;
    confirmPasswordInput.required = false;
    newPasswordInput.value = "";
    confirmPasswordInput.value = "";
  }
}

// 加载权限网格
function loadPermissionsGrid(selectedPermissions = []) {
  const grid = document.getElementById("permissionsGrid");
  grid.innerHTML = Object.entries(PERMISSIONS)
    .map(
      ([key, label]) => `
    <div class="permission-item">
      <input 
        type="checkbox" 
        id="perm_${key}" 
        value="${key}"
        ${selectedPermissions.includes(key) ? "checked" : ""}
      />
      <label for="perm_${key}">${label}</label>
    </div>
  `
    )
    .join("");
}

// 加载账户复选框（带搜索和分页）
function loadAccountsCheckboxes(selectedAccounts = []) {
  // 重置状态
  accountsCurrentPage = 1;
  filteredAccounts = [...allAccounts];
  selectedAccountsSet = new Set(selectedAccounts); // 初始化选中集合
  
  // 清空搜索框
  const searchInput = document.getElementById("accountsSearchInput");
  if (searchInput) {
    searchInput.value = "";
  }
  
  // 渲染账户列表
  renderAccountsList();
}

// 渲染账户列表
function renderAccountsList() {
  const list = document.getElementById("accountsList");
  
  if (filteredAccounts.length === 0) {
    list.innerHTML = '<div class="accounts-list-empty">暂无可绑定的账户</div>';
    updateAccountsStats();
    updateAccountsPagination();
    return;
  }
  
  // 计算分页
  accountsTotalPages = Math.ceil(filteredAccounts.length / accountsPageSize);
  const startIdx = (accountsCurrentPage - 1) * accountsPageSize;
  const endIdx = startIdx + accountsPageSize;
  displayedAccounts = filteredAccounts.slice(startIdx, endIdx);
  
  // 渲染账户项
  list.innerHTML = displayedAccounts
    .map((account) => {
      const isChecked = selectedAccountsSet.has(account.email_id);
      return `
        <div class="account-item ${isChecked ? 'selected' : ''}" onclick="toggleAccountCheckbox('${account.email_id}')">
          <input 
            type="checkbox" 
            id="account_${account.email_id}" 
            value="${account.email_id}"
            ${isChecked ? "checked" : ""}
            onclick="event.stopPropagation()"
            onchange="handleAccountCheckboxChange('${account.email_id}')"
          />
          <label for="account_${account.email_id}">${account.email_id}</label>
        </div>
      `;
    })
    .join("");
  
  // 更新统计和分页
  updateAccountsStats();
  updateAccountsPagination();
}

// 处理账户复选框变化
function handleAccountCheckboxChange(emailId) {
  const checkbox = document.getElementById(`account_${emailId}`);
  if (checkbox) {
    if (checkbox.checked) {
      selectedAccountsSet.add(emailId);
    } else {
      selectedAccountsSet.delete(emailId);
    }
    
    // 更新样式
    const item = checkbox.closest('.account-item');
    if (item) {
      if (checkbox.checked) {
        item.classList.add('selected');
      } else {
        item.classList.remove('selected');
      }
    }
    
    updateAccountsStats();
  }
}

// 切换账户复选框
function toggleAccountCheckbox(emailId) {
  const checkbox = document.getElementById(`account_${emailId}`);
  if (checkbox) {
    checkbox.checked = !checkbox.checked;
    handleAccountCheckboxChange(emailId);
  }
}

// 更新账户统计信息
function updateAccountsStats() {
  const selectedCount = document.getElementById("accountsSelectedCount");
  const displayCount = document.getElementById("accountsDisplayCount");
  const totalCount = document.getElementById("accountsTotalCount");
  
  if (selectedCount) {
    selectedCount.textContent = `已选 ${selectedAccountsSet.size}`;
  }
  if (displayCount) {
    displayCount.textContent = `显示 ${filteredAccounts.length}`;
  }
  if (totalCount) {
    totalCount.textContent = `共 ${allAccounts.length}`;
  }
}

// 获取所有选中的账户（用于提交表单）
function getAllSelectedAccounts() {
  return Array.from(selectedAccountsSet);
}

// 更新账户分页控件
function updateAccountsPagination() {
  const pagination = document.getElementById("accountsPagination");
  const pageInfo = document.getElementById("accountsPageInfo");
  const prevBtn = document.getElementById("prevAccountsBtn");
  const nextBtn = document.getElementById("nextAccountsBtn");
  
  if (accountsTotalPages <= 1) {
    pagination.style.display = "none";
    return;
  }
  
  pagination.style.display = "flex";
  pageInfo.textContent = `${accountsCurrentPage} / ${accountsTotalPages}`;
  prevBtn.disabled = accountsCurrentPage === 1;
  nextBtn.disabled = accountsCurrentPage === accountsTotalPages;
}

// 筛选账户
function filterAccounts() {
  const searchInput = document.getElementById("accountsSearchInput");
  const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : "";
  
  if (searchTerm === "") {
    filteredAccounts = [...allAccounts];
  } else {
    filteredAccounts = allAccounts.filter(account => 
      account.email_id.toLowerCase().includes(searchTerm)
    );
  }
  
  // 重置到第一页
  accountsCurrentPage = 1;
  
  // 重新渲染
  renderAccountsList();
}

// 上一页
function prevAccountsPage() {
  if (accountsCurrentPage > 1) {
    accountsCurrentPage--;
    renderAccountsList();
  }
}

// 下一页
function nextAccountsPage() {
  if (accountsCurrentPage < accountsTotalPages) {
    accountsCurrentPage++;
    renderAccountsList();
  }
}

// 全选当前页
function selectAllVisibleAccounts() {
  displayedAccounts.forEach(account => {
    selectedAccountsSet.add(account.email_id);
    const checkbox = document.getElementById(`account_${account.email_id}`);
    if (checkbox) {
      checkbox.checked = true;
      const item = checkbox.closest('.account-item');
      if (item) {
        item.classList.add('selected');
      }
    }
  });
  updateAccountsStats();
}

// 清空所有选择
function deselectAllAccounts() {
  selectedAccountsSet.clear();
  const checkboxes = document.querySelectorAll('#accountsList input[type="checkbox"]');
  checkboxes.forEach(cb => {
    cb.checked = false;
    const item = cb.closest('.account-item');
    if (item) {
      item.classList.remove('selected');
    }
  });
  updateAccountsStats();
}

// 处理角色变更
function handleRoleChange() {
  const role = document.getElementById("role").value;
  const permissionsGroup = document.getElementById("permissionsGroup");
  const accountsGroup = document.getElementById("accountsGroup");

  if (role === "admin") {
    // 管理员拥有所有权限，隐藏权限选择
    permissionsGroup.style.display = "none";
    accountsGroup.style.display = "none";
  } else {
    // 普通用户可以自定义权限
    permissionsGroup.style.display = "block";
    accountsGroup.style.display = "block";
  }
}

// 处理用户表单提交
async function handleUserSubmit(event) {
  event.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const email = document.getElementById("email").value.trim();
  const role = document.getElementById("role").value;
  const isActive = document.getElementById("isActive").checked;

  // 获取选中的权限
  const permissions = [];
  if (role === "user") {
    document
      .querySelectorAll('#permissionsGrid input[type="checkbox"]:checked')
      .forEach((cb) => {
        permissions.push(cb.value);
      });
  }

  // 获取选中的账户（使用全局 Set，支持跨页选择）
  const boundAccounts = role === "user" ? getAllSelectedAccounts() : [];

  try {
    if (editingUserId) {
      // 检查是否需要修改密码
      const changePassword = document.getElementById(
        "changePasswordCheckbox"
      ).checked;

      if (changePassword) {
        const newPassword = document.getElementById("newPassword").value;
        const confirmPassword =
          document.getElementById("confirmNewPassword").value;

        // 验证密码
        if (newPassword !== confirmPassword) {
          showNotification("两次输入的密码不一致", "error");
          return;
        }

        if (newPassword.length < 6) {
          showNotification("密码长度至少为6位", "error");
          return;
        }

        // 先更新密码
        await apiRequest(`/admin/users/${editingUserId}/password`, {
          method: "PUT",
          body: JSON.stringify({
            new_password: newPassword,
          }),
        });
      }

      // 更新用户信息
      await apiRequest(`/admin/users/${editingUserId}`, {
        method: "PUT",
        body: JSON.stringify({
          email,
          role,
          is_active: isActive,
          permissions,
          bound_accounts: boundAccounts,
        }),
      });

      if (changePassword) {
        showNotification("用户信息和密码更新成功", "success");
      } else {
        showNotification("用户更新成功", "success");
      }
    } else {
      // 创建用户
      await apiRequest("/admin/users", {
        method: "POST",
        body: JSON.stringify({
          username,
          password,
          email,
          role,
          is_active: isActive,
          permissions,
          bound_accounts: boundAccounts,
        }),
      });
      showNotification("用户创建成功", "success");
    }

    closeUserModal();
    loadUsers();
  } catch (error) {
    showNotification("操作失败: " + error.message, "error");
  }
}

// 关闭用户模态框
function closeUserModal() {
  document.getElementById("userModal").classList.remove("show");
  document.getElementById("userForm").reset();
  document.getElementById("username").readOnly = false;

  // 重置密码修改字段
  document.getElementById("changePasswordGroup").style.display = "none";
  document.getElementById("changePasswordCheckbox").checked = false;
  document.getElementById("newPasswordFields").style.display = "none";
  document.getElementById("newPassword").value = "";
  document.getElementById("confirmNewPassword").value = "";

  editingUserId = null;
}

// 删除用户
async function deleteUser(username) {
  if (!confirm(`确定要删除用户 "${username}" 吗？此操作不可恢复。`)) {
    return;
  }

  try {
    await apiRequest(`/admin/users/${username}`, {
      method: "DELETE",
    });
    showNotification("用户删除成功", "success");
    loadUsers();
  } catch (error) {
    showNotification("删除失败: " + error.message, "error");
  }
}

// ============================================================================
// 密码修改模态框操作
// ============================================================================

// 打开修改密码模态框
function changePassword(username) {
  document.getElementById("passwordUsername").value = username;
  document.getElementById("newPassword").value = "";
  document.getElementById("confirmPassword").value = "";
  document.getElementById("passwordModal").classList.add("show");
}

// 关闭密码模态框
function closePasswordModal() {
  document.getElementById("passwordModal").classList.remove("show");
  document.getElementById("passwordForm").reset();
}

// 处理密码修改提交
async function handlePasswordSubmit(event) {
  event.preventDefault();

  const username = document.getElementById("passwordUsername").value;
  const newPassword = document.getElementById("newPassword").value;
  const confirmPassword = document.getElementById("confirmPassword").value;

  // 验证密码匹配
  if (newPassword !== confirmPassword) {
    showNotification("两次输入的密码不一致", "error");
    return;
  }

  // 验证密码长度
  if (newPassword.length < 6) {
    showNotification("密码长度至少为6位", "error");
    return;
  }

  try {
    await apiRequest(`/admin/users/${username}/password`, {
      method: "PUT",
      body: JSON.stringify({
        new_password: newPassword,
      }),
    });

    showNotification("密码修改成功", "success");
    closePasswordModal();
  } catch (error) {
    showNotification("修改密码失败: " + error.message, "error");
  }
}

// ============================================================================
// 事件监听
// ============================================================================

// 点击模态框外部关闭
document.getElementById("userModal").addEventListener("click", function (e) {
  if (e.target === this) {
    closeUserModal();
  }
});

document
  .getElementById("passwordModal")
  .addEventListener("click", function (e) {
    if (e.target === this) {
      closePasswordModal();
    }
  });

console.log("✅ [User Management] 用户管理模块加载完成");

