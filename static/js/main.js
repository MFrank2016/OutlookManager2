// main.js - 主入口文件

// 邮件列表分页相关变量（如果还没有在其他模块中定义）
let emailCurrentPage = 1;
let emailPageSize = 10;
let emailTotalCount = 0;
let currentEmailFolder = "all";

// 侧边栏折叠状态管理
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  const isCollapsed = sidebar.classList.toggle("collapsed");

  // 保存状态到localStorage
  localStorage.setItem("sidebarCollapsed", isCollapsed ? "true" : "false");
}

// 从localStorage恢复侧边栏状态
function restoreSidebarState() {
  const sidebar = document.getElementById("sidebar");
  if (!sidebar) return;

  const isCollapsed = localStorage.getItem("sidebarCollapsed") === "true";
  if (isCollapsed) {
    sidebar.classList.add("collapsed");
  }
}

// 点击模态框外部关闭
if (document.getElementById("emailModal")) {
  document.getElementById("emailModal").addEventListener("click", function (e) {
    if (e.target === this) {
      closeEmailModal();
    }
  });
}

// 键盘快捷键
document.addEventListener("keydown", function (e) {
  // Ctrl/Cmd + R: 刷新邮件
  if ((e.ctrlKey || e.metaKey) && e.key === "r" && currentAccount) {
    e.preventDefault();
    refreshEmails();
  }

  // Escape: 关闭模态框
  if (e.key === "Escape") {
    closeEmailModal();
  }

  // Ctrl/Cmd + F: 聚焦搜索框
  if (
    (e.ctrlKey || e.metaKey) &&
    e.key === "f" &&
    document.getElementById("emailSearch")
  ) {
    e.preventDefault();
    document.getElementById("emailSearch").focus();
  }

  // Ctrl/Cmd + B: 切换侧边栏
  if ((e.ctrlKey || e.metaKey) && e.key === "b") {
    e.preventDefault();
    toggleSidebar();
  }
});

// 页面可见性变化时刷新数据
document.addEventListener("visibilitychange", function () {
  if (!document.hidden && currentAccount) {
    // 页面重新可见时，如果超过5分钟则自动刷新
    const lastUpdate = document.getElementById("lastUpdateTime")?.textContent;
    if (lastUpdate && lastUpdate !== "-") {
      const lastUpdateTime = new Date(lastUpdate);
      const now = new Date();
      const diffMinutes = (now - lastUpdateTime) / (1000 * 60);

      if (diffMinutes > 5) {
        showNotification("检测到数据可能过期，正在刷新...", "info", "", 2000);
        setTimeout(() => refreshEmails(), 1000);
      }
    }
  }
});

// 初始化用户界面权限
async function initializeUserPermissions() {
  try {
    // 获取并存储用户信息
    const userInfo = await fetchAndStoreUserInfo();

    if (!userInfo) {
      console.error("无法获取用户信息");
      return;
    }

    console.log("当前用户:", userInfo);

    // 根据角色显示/隐藏菜单项
    const isAdminUser = userInfo.role === "admin";
    console.log(
      `🔐 [权限] 用户角色: ${userInfo.role}, 是否管理员: ${isAdminUser}`
    );

    // 添加账户 - 仅管理员可见
    const addAccountNav = document.getElementById("addAccountNav");
    if (addAccountNav) {
      addAccountNav.style.display = isAdminUser ? "flex" : "none";
      console.log(`🔐 [权限] 添加账户菜单 -> ${isAdminUser ? "显示" : "隐藏"}`);
    }

    // 批量添加 - 仅管理员可见
    const batchAddNav = document.getElementById("batchAddNav");
    if (batchAddNav) {
      batchAddNav.style.display = isAdminUser ? "flex" : "none";
      console.log(`🔐 [权限] 批量添加菜单 -> ${isAdminUser ? "显示" : "隐藏"}`);
    }

    // 用户管理 - 仅管理员可见
    const userManagementNav = document.getElementById("userManagementNav");
    if (userManagementNav) {
      userManagementNav.style.display = isAdminUser ? "flex" : "none";
      console.log(`🔐 [权限] 用户管理菜单 -> ${isAdminUser ? "显示" : "隐藏"}`);
    }

    // 管理面板 - 仅管理员可见
    const adminPanelNav = document.getElementById("adminPanelNav");
    if (adminPanelNav) {
      adminPanelNav.style.display = isAdminUser ? "flex" : "none";
      console.log(`🔐 [权限] 管理面板菜单 -> ${isAdminUser ? "显示" : "隐藏"}`);
    }

    // API管理 - 仅管理员可见
    const apiDocsNav = document.getElementById("apiDocsNav");
    if (apiDocsNav) {
      apiDocsNav.style.display = isAdminUser ? "flex" : "none";
      console.log(`🔐 [权限] API管理菜单 -> ${isAdminUser ? "显示" : "隐藏"}`);
    }

    // 在侧边栏底部添加用户信息和退出按钮
    console.log("🔍 [Debug] 开始查找 sidebarFooter 元素...");

    // 尝试多种方法查找元素
    const sidebarFooter = document.getElementById("sidebarFooter");
    const sidebarFooterByQuery = document.querySelector("#sidebarFooter");
    const sidebarFooterByClass = document.querySelector(".sidebar-footer");

    console.log("🔍 [Debug] getElementById:", sidebarFooter);
    console.log("🔍 [Debug] querySelector #:", sidebarFooterByQuery);
    console.log("🔍 [Debug] querySelector .class:", sidebarFooterByClass);

    // 使用找到的任何一个
    const footer =
      sidebarFooter || sidebarFooterByQuery || sidebarFooterByClass;

    console.log("🔍 [Debug] 最终使用的 footer 元素:", footer);

    if (footer) {
      const roleText = isAdminUser ? "管理员" : "普通用户";
      const roleColor = isAdminUser ? "#10b981" : "#3b82f6";
      const roleIcon = isAdminUser ? "👑" : "👤";

      console.log(
        `🔍 [Debug] 准备添加用户信息: ${userInfo.username} (${roleText})`
      );

      // 总是更新用户信息（移除重复检查）
      footer.innerHTML = `
        <div class="user-info-card">
          <div class="user-info-main">
            <div class="user-avatar">${roleIcon}</div>
            <div class="user-details">
              <div class="user-name">${userInfo.username}</div>
              <div class="user-role" style="color: ${roleColor};">${roleText}</div>
            </div>
          </div>
          <button class="logout-btn" onclick="logout()" title="退出登录">
            <span class="logout-icon">🚪</span>
            <span class="logout-text">退出登录</span>
          </button>
        </div>
      `;
      console.log("✅ [Success] 用户信息已添加到侧边栏");
    } else {
      console.error("❌ [Error] 找不到 sidebarFooter 元素");
      console.error("❌ [Error] document.body:", document.body);
      console.error(
        "❌ [Error] 所有带 id 的元素:",
        document.querySelectorAll("[id]")
      );
    }
  } catch (error) {
    console.error("初始化用户权限失败:", error);
  }
}

// 初始化 - 使用 DOMContentLoaded 确保 DOM 已准备好
document.addEventListener("DOMContentLoaded", async function () {
  console.log("🔄 [Main] DOM 已加载，开始初始化...");

  // 调试：立即检查 sidebarFooter
  console.log(
    "🔍 [Debug] 立即检查 sidebarFooter:",
    document.getElementById("sidebarFooter")
  );
  console.log(
    "🔍 [Debug] 立即检查 sidebar:",
    document.getElementById("sidebar")
  );

  // 调试：检查 sidebar 结构
  const sidebar = document.getElementById("sidebar");
  console.log("🔍 [Debug] sidebar 元素:", sidebar);
  if (sidebar) {
    console.log("🔍 [Debug] sidebar 的子元素数量:", sidebar.children.length);
    console.log(
      "🔍 [Debug] sidebar 的子元素:",
      Array.from(sidebar.children).map((el) => ({
        tag: el.tagName,
        id: el.id,
        class: el.className,
      }))
    );
  }

  // 恢复侧边栏状态
  restoreSidebarState();

  // 初始化用户权限和界面
  await initializeUserPermissions();

  // 处理URL路由
  handleUrlRouting();

  // 如果没有路由匹配，显示默认页面
  if (!window.location.hash || window.location.hash === "#") {
    showPage("accounts");
  }

  // 显示欢迎消息
  setTimeout(() => {
    showNotification("欢迎使用邮件管理系统！", "info", "欢迎", 3000);
  }, 500);

  console.log("✅ [Main] 邮件管理系统初始化完成");
});

// 监听浏览器返回按钮
window.addEventListener("popstate", function () {
  handleUrlRouting();
});

// 刷新邮件（兼容函数）
function refreshEmails() {
  if (typeof loadEmails === "function") {
    loadEmails(true);
  }
}

// 关闭邮件模态框（兼容函数）
function closeEmailModal() {
  const modal = document.getElementById("emailModal");
  if (modal) {
    modal.classList.add("hidden");
  }
}
