// API请求模块
const API_BASE = "";

// 获取当前用户信息
function getCurrentUser() {
  const userInfoStr = localStorage.getItem("user_info");
  if (userInfoStr) {
    try {
      return JSON.parse(userInfoStr);
    } catch (e) {
      console.error("解析用户信息失败:", e);
      return null;
    }
  }
  return null;
}

// 检查用户是否是管理员
function isAdmin() {
  const user = getCurrentUser();
  return user && user.role === "admin";
}

// 检查用户是否有特定权限
function hasPermission(permission) {
  const user = getCurrentUser();
  if (!user) return false;
  
  // 管理员拥有所有权限
  if (user.role === "admin") return true;
  
  // 检查用户权限列表
  return user.permissions && user.permissions.includes(permission);
}

// 获取用户可访问的账户列表
function getAccessibleAccounts() {
  const user = getCurrentUser();
  if (!user) return [];
  
  // 管理员可以访问所有账户
  if (user.role === "admin") return null; // null 表示所有账户
  
  // 普通用户返回绑定的账户
  return user.bound_accounts || [];
}

// API请求（支持JWT认证）
async function apiRequest(url, options = {}) {
  try {
    // 获取JWT token
    const token = localStorage.getItem("auth_token");

    // 如果没有token，跳转到登录页面
    if (!token && url !== "/auth/login" && url !== "/api") {
      showNotification("请先登录", "warning");
      setTimeout(() => {
        window.location.href = "/static/login.html";
      }, 1000);
      return;
    }

    const response = await fetch(API_BASE + url, {
      headers: {
        "Content-Type": "application/json",
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    });

    // 如果返回401，说明token无效或过期
    if (response.status === 401) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: "Unauthorized" }));
      
      // 检查是否是添加账户时的凭证验证失败
      // 如果是 POST /accounts 请求且有详细错误信息，很可能是账户凭证问题
      const isAddAccountRequest = options.method === "POST" && url.includes("/accounts");
      const hasDetailedError = errorData.detail && errorData.detail !== "Unauthorized";
      
      // 如果是添加账户请求且有具体错误信息，不要清除用户登录状态
      if (isAddAccountRequest && hasDetailedError) {
        console.log("账户凭证验证失败，但用户登录状态保持:", errorData.detail);
        throw new Error(errorData.detail || "账户凭证验证失败");
      }
      
      // 否则是用户token过期，需要重新登录
      if (!window._isHandlingAuthExpired) {
        window._isHandlingAuthExpired = true;
        showNotification("登录已过期，请重新登录", "warning");
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        setTimeout(() => {
          window.location.href = "/static/login.html";
        }, 1500);
      }
      throw new Error("登录已过期");
    }

    if (!response.ok) {
      const errorData = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      throw new Error(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`
      );
    }

    return await response.json();
  } catch (error) {
    console.error("API请求失败:", error);
    throw error;
  }
}

// 登录后获取并存储用户信息
async function fetchAndStoreUserInfo() {
  try {
    const userInfo = await apiRequest("/auth/me");
    if (userInfo) {
      localStorage.setItem("user_info", JSON.stringify(userInfo));
      console.log("用户信息已更新:", userInfo);
      return userInfo;
    }
  } catch (error) {
    console.error("获取用户信息失败:", error);
    return null;
  }
}

// 退出登录
function logout() {
  localStorage.removeItem("auth_token");
  localStorage.removeItem("user_info");
  showNotification("已退出登录", "info");
  setTimeout(() => {
    window.location.href = "/static/login.html";
  }, 500);
}

// API 配置已移至 apitest.js 模块
