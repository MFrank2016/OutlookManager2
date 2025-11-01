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

// 初始化
window.addEventListener("load", function () {
  // 恢复侧边栏状态
  restoreSidebarState();

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

console.log("✅ [Main] 邮件管理系统初始化完成");
