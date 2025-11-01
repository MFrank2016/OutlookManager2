// apitest.js - API测试模块

// API测试配置定义
const API_TEST_CONFIGS = {
  login: {
    method: "POST",
    endpoint: "/auth/login",
    body: { username: "admin", password: "admin123" },
    requiresAuth: false,
  },
  me: {
    method: "GET",
    endpoint: "/auth/me",
    requiresAuth: true,
  },
  changePassword: {
    method: "POST",
    endpoint: "/auth/change-password",
    body: { old_password: "", new_password: "" },
    requiresAuth: true,
  },
  accounts: {
    method: "GET",
    endpoint: "/accounts",
    query: {
      page: 1,
      page_size: 10,
      email_search: "",
      tag_search: "",
      refresh_status: "",
      time_filter: "",
      after_date: "",
    },
    requiresAuth: true,
  },
  addAccount: {
    method: "POST",
    endpoint: "/accounts",
    body: {
      email_id: "example@outlook.com",
      refresh_token: "",
      client_id: "",
      tags: [],
    },
    requiresAuth: true,
  },
  deleteAccount: {
    method: "DELETE",
    endpoint: "/accounts/{email_id}",
    path: { email_id: "example@outlook.com" },
    requiresAuth: true,
  },
  updateTags: {
    method: "PUT",
    endpoint: "/accounts/{email_id}/tags",
    path: { email_id: "example@outlook.com" },
    body: { tags: ["工作", "个人"] },
    requiresAuth: true,
  },
  addTag: {
    method: "POST",
    endpoint: "/accounts/{email_id}/tags/add",
    path: { email_id: "example@outlook.com" },
    body: { tag: "VIP" },
    requiresAuth: true,
  },
  randomAccounts: {
    method: "GET",
    endpoint: "/accounts/random",
    query: {
      include_tags: "",
      exclude_tags: "",
      page: 1,
      page_size: 5,
    },
    requiresAuth: true,
  },
  refreshToken: {
    method: "POST",
    endpoint: "/accounts/{email_id}/refresh-token",
    path: { email_id: "example@outlook.com" },
    requiresAuth: true,
  },
  singleRefreshToken: {
    method: "POST",
    endpoint: "/accounts/{email_id}/refresh-token",
    path: { email_id: "example@outlook.com" },
    requiresAuth: true,
  },
  batchRefreshTokens: {
    method: "POST",
    endpoint: "/accounts/batch-refresh-tokens",
    query: {
      email_search: "",
      tag_search: "",
      refresh_status: "",
      time_filter: "",
      after_date: "",
    },
    requiresAuth: true,
  },
  emails: {
    method: "GET",
    endpoint: "/emails/{email_id}",
    path: { email_id: "example@outlook.com" },
    query: { folder: "inbox", page: 1, page_size: 20, refresh: false },
    requiresAuth: true,
  },
  emailDetail: {
    method: "GET",
    endpoint: "/emails/{email_id}/{message_id}",
    path: { email_id: "example@outlook.com", message_id: "INBOX-1" },
    requiresAuth: true,
  },
  dualView: {
    method: "GET",
    endpoint: "/emails/{email_id}/dual-view",
    path: { email_id: "example@outlook.com" },
    query: { inbox_page: 1, junk_page: 1, page_size: 20 },
    requiresAuth: true,
  },
  clearCache: {
    method: "DELETE",
    endpoint: "/cache/{email_id}",
    path: { email_id: "example@outlook.com" },
    requiresAuth: true,
  },
  clearAllCache: {
    method: "DELETE",
    endpoint: "/cache",
    requiresAuth: true,
  },
  tableCount: {
    method: "GET",
    endpoint: "/admin/tables/{table_name}/count",
    path: { table_name: "accounts" },
    requiresAuth: true,
  },
  tableData: {
    method: "GET",
    endpoint: "/admin/tables/{table_name}",
    path: { table_name: "accounts" },
    requiresAuth: true,
  },
  deleteTableRecord: {
    method: "DELETE",
    endpoint: "/admin/tables/{table_name}/{record_id}",
    path: { table_name: "accounts", record_id: 1 },
    requiresAuth: true,
  },
  getConfig: {
    method: "GET",
    endpoint: "/admin/config",
    requiresAuth: true,
  },
  updateConfig: {
    method: "POST",
    endpoint: "/admin/config",
    body: {
      key: "imap_server",
      value: "outlook.office365.com",
      description: "IMAP服务器地址",
    },
    requiresAuth: true,
  },
  systemInfo: {
    method: "GET",
    endpoint: "/api",
    requiresAuth: false,
  },
};

// 打开API测试模态框
function openApiTest(apiKey) {
  const config = API_TEST_CONFIGS[apiKey];
  if (!config) {
    showNotification("API配置不存在", "error");
    return;
  }

  // 设置标题和基本信息
  const titleElement = document.getElementById("apiTestTitle");
  const methodElement = document.getElementById("apiTestMethod");
  const endpointElement = document.getElementById("apiTestEndpoint");

  if (titleElement) titleElement.textContent = `🚀 测试API: ${config.endpoint}`;
  if (methodElement) {
    methodElement.textContent = config.method;
    // 根据HTTP方法设置不同的颜色
    methodElement.className = "api-method-badge";
    if (config.method === "GET") {
      methodElement.style.background = "#dbeafe";
      methodElement.style.color = "#1e40af";
    } else if (config.method === "POST") {
      methodElement.style.background = "#dcfce7";
      methodElement.style.color = "#15803d";
    } else if (config.method === "PUT") {
      methodElement.style.background = "#fef3c7";
      methodElement.style.color = "#92400e";
    } else if (config.method === "DELETE") {
      methodElement.style.background = "#fee2e2";
      methodElement.style.color = "#991b1b";
    } else if (config.method === "PATCH") {
      methodElement.style.background = "#e0e7ff";
      methodElement.style.color = "#3730a3";
    }
  }
  if (endpointElement) endpointElement.textContent = config.endpoint;

  // 隐藏所有参数区域
  const pathParamsElement = document.getElementById("apiTestPathParams");
  const queryParamsElement = document.getElementById("apiTestQueryParams");
  const bodyElement = document.getElementById("apiTestBody");
  const resultSection = document.getElementById("apiTestResultSection");

  if (pathParamsElement) pathParamsElement.classList.add("hidden");
  if (queryParamsElement) queryParamsElement.classList.add("hidden");
  if (bodyElement) bodyElement.classList.add("hidden");
  if (resultSection) resultSection.classList.add("hidden");

  // 路径参数
  if (config.path) {
    const pathParamsList = document.getElementById("apiTestPathParamsList");
    if (pathParamsList) {
      pathParamsList.innerHTML = "";
      Object.entries(config.path).forEach(([key, value]) => {
        pathParamsList.innerHTML += `
                    <div class="api-test-param">
                        <label>${key}</label>
                        <input type="text" id="path_${key}" value="${value}" placeholder="${key}">
                    </div>
                `;
      });
      if (pathParamsElement) pathParamsElement.classList.remove("hidden");
    }
  }

  // 查询参数
  if (config.query) {
    const queryParamsList = document.getElementById("apiTestQueryParamsList");
    if (queryParamsList) {
      queryParamsList.innerHTML = "";
      Object.entries(config.query).forEach(([key, value]) => {
        const inputType =
          typeof value === "boolean"
            ? "checkbox"
            : typeof value === "number"
            ? "number"
            : "text";
        if (inputType === "checkbox") {
          queryParamsList.innerHTML += `
                        <div class="api-test-param">
                            <label>
                                <input type="checkbox" id="query_${key}" ${
            value ? "checked" : ""
          }>
                                ${key}
                            </label>
                        </div>
                    `;
        } else {
          queryParamsList.innerHTML += `
                        <div class="api-test-param">
                            <label>${key}</label>
                            <input type="${inputType}" id="query_${key}" value="${value}" placeholder="${key}">
                        </div>
                    `;
        }
      });
      if (queryParamsElement) queryParamsElement.classList.remove("hidden");
    }
  }

  // 请求体
  if (config.body) {
    const bodyContent = document.getElementById("apiTestBodyContent");
    if (bodyContent) {
      bodyContent.value = JSON.stringify(config.body, null, 2);
      if (bodyElement) bodyElement.classList.remove("hidden");
    }
  }

  // 存储当前API配置
  window.currentApiConfig = config;
  window.currentApiKey = apiKey;

  // 显示模态框
  const modal = document.getElementById("apiTestModal");
  if (modal) {
    modal.classList.add("show");
  }
}

// 关闭API测试模态框
function closeApiTestModal(event) {
  if (event && event.target !== event.currentTarget) return;
  const modal = document.getElementById("apiTestModal");
  if (modal) {
    modal.classList.remove("show");
  }
}

// 重置表单
function resetApiTestForm() {
  if (window.currentApiKey) {
    openApiTest(window.currentApiKey);
  }
}

// 执行API测试
async function executeApiTest() {
  const config = window.currentApiConfig;
  if (!config) return;

  try {
    // 构建URL
    let url = config.endpoint;

    // 替换路径参数
    if (config.path) {
      Object.keys(config.path).forEach((key) => {
        const element = document.getElementById(`path_${key}`);
        if (element) {
          const value = element.value;
          url = url.replace(`{${key}}`, encodeURIComponent(value));
        }
      });
    }

    // 添加查询参数
    if (config.query) {
      const queryParams = new URLSearchParams();
      Object.keys(config.query).forEach((key) => {
        const element = document.getElementById(`query_${key}`);
        if (element) {
          let value;
          if (element.type === "checkbox") {
            value = element.checked;
          } else {
            value = element.value;
          }
          if (value !== "" && value !== null && value !== undefined) {
            queryParams.append(key, value);
          }
        }
      });
      const queryString = queryParams.toString();
      if (queryString) {
        url += "?" + queryString;
      }
    }

    // 构建请求选项
    const options = {
      method: config.method,
    };

    // 添加请求体
    if (config.body) {
      try {
        const bodyContent = document.getElementById("apiTestBodyContent");
        if (bodyContent) {
          const bodyText = bodyContent.value;
          const bodyJson = JSON.parse(bodyText);
          options.body = JSON.stringify(bodyJson);
        }
      } catch (e) {
        showNotification("请求体JSON格式错误", "error");
        return;
      }
    }

    // 发送请求
    showNotification("正在发送请求...", "info");

    let response;
    if (config.requiresAuth) {
      response = await apiRequest(url, options);
    } else {
      // 不需要认证的接口直接fetch
      const fetchOptions = {
        method: options.method,
        headers: {
          "Content-Type": "application/json",
        },
      };
      if (options.body) {
        fetchOptions.body = options.body;
      }
      const API_BASE =
        typeof window.API_BASE !== "undefined" ? window.API_BASE : "";
      const res = await fetch(API_BASE + url, fetchOptions);
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      response = await res.json();
    }

    // 显示响应
    const resultSection = document.getElementById("apiTestResultSection");
    const resultDiv = document.getElementById("apiTestResult");
    const resultContent = document.getElementById("apiTestResultContent");

    if (resultSection) resultSection.classList.remove("hidden");
    if (resultDiv) resultDiv.className = "api-test-result success";
    if (resultContent)
      resultContent.textContent = JSON.stringify(response, null, 2);

    showNotification("请求成功！", "success");
  } catch (error) {
    // 显示错误
    const resultSection = document.getElementById("apiTestResultSection");
    const resultDiv = document.getElementById("apiTestResult");
    const resultContent = document.getElementById("apiTestResultContent");

    if (resultSection) resultSection.classList.remove("hidden");
    if (resultDiv) resultDiv.className = "api-test-result error";
    if (resultContent) resultContent.textContent = `错误: ${error.message}`;

    showNotification("请求失败：" + error.message, "error");
  }
}

console.log("✅ [API Test] API测试模块加载完成");
