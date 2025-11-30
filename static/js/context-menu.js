// context-menu.js - 右键菜单模块

// 右键菜单相关变量
let contextMenuTarget = null;

// 显示右键菜单
function showAccountContextMenu(event, emailId) {
  event.preventDefault();
  event.stopPropagation();

  contextMenuTarget = emailId;
  const contextMenu = document.getElementById("contextMenu");

  if (!contextMenu) return;

  // 设置菜单位置
  contextMenu.style.left = event.pageX + "px";
  contextMenu.style.top = event.pageY + "px";
  contextMenu.style.display = "block";

  // 点击其他地方隐藏菜单
  setTimeout(() => {
    document.addEventListener("click", hideContextMenu);
  }, 10);
}

// 隐藏右键菜单
function hideContextMenu() {
  const contextMenu = document.getElementById("contextMenu");
  if (contextMenu) {
    contextMenu.style.display = "none";
  }
  contextMenuTarget = null;
  document.removeEventListener("click", hideContextMenu);
}

// 在新标签页中打开
function openInNewTab() {
  if (contextMenuTarget) {
    const url = `${window.location.origin}/#/emails/${encodeURIComponent(
      contextMenuTarget
    )}`;
    window.open(url, "_blank");
  }
  hideContextMenu();
}

// 复制账户链接
function copyAccountLink() {
  if (contextMenuTarget) {
    const url = `${window.location.origin}/#/emails/${encodeURIComponent(
      contextMenuTarget
    )}`;

    if (navigator.clipboard) {
      navigator.clipboard
        .writeText(url)
        .then(() => {
          showNotification("链接已复制到剪贴板", "success");
        })
        .catch(() => {
          fallbackCopyText(url);
        });
    } else {
      fallbackCopyText(url);
    }
  }
  hideContextMenu();
}

// 从右键菜单编辑标签
function contextEditTags() {
  if (contextMenuTarget && typeof accounts !== "undefined") {
    const account = accounts.find((acc) => acc.email_id === contextMenuTarget);
    if (account && typeof editAccountTags === "function") {
      editAccountTags(contextMenuTarget);
    }
  }
  hideContextMenu();
}

// 从右键菜单删除账户
function contextDeleteAccount() {
  if (contextMenuTarget && typeof deleteAccount === "function") {
    deleteAccount(contextMenuTarget);
  }
  hideContextMenu();
}

// 邮件列表右键菜单
function showEmailsContextMenu(event) {
  if (!currentAccount) {
    return;
  }

  event.preventDefault();
  event.stopPropagation();

  const url = `${window.location.origin}/#/emails/${encodeURIComponent(
    currentAccount
  )}`;
  window.open(url, "_blank");
}

console.log("✅ [Context Menu] 右键菜单模块加载完成");
