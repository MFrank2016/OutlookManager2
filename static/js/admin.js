// admin.js - 管理面板模块

// 管理面板全局变量
let currentTable = null;
let currentTableData = [];
let currentTableColumns = [];
let currentEditRecord = null;

// 切换管理面板标签
function switchAdminTab(tabName, tabElement) {
  // 切换标签激活状态
  document
    .querySelectorAll(".tab")
    .forEach((tab) => tab.classList.remove("active"));
  if (tabElement) {
    tabElement.classList.add("active");
  }

  // 切换面板显示
  const tablesPanel = document.getElementById("tablesPanel");
  const usersPanel = document.getElementById("usersPanel");
  const configPanel = document.getElementById("configPanel");
  const cachePanel = document.getElementById("cachePanel");
  
  if (tabName === "tables") {
    if (tablesPanel) tablesPanel.classList.remove("hidden");
    if (usersPanel) usersPanel.classList.add("hidden");
    if (configPanel) configPanel.classList.add("hidden");
    if (cachePanel) cachePanel.classList.add("hidden");
    loadTablesList();
  } else if (tabName === "users") {
    if (tablesPanel) tablesPanel.classList.add("hidden");
    if (usersPanel) usersPanel.classList.remove("hidden");
    if (configPanel) configPanel.classList.add("hidden");
    if (cachePanel) cachePanel.classList.add("hidden");
    // 用户管理标签页内容在 HTML 中已定义，无需加载
  } else if (tabName === "config") {
    if (tablesPanel) tablesPanel.classList.add("hidden");
    if (usersPanel) usersPanel.classList.add("hidden");
    if (configPanel) configPanel.classList.remove("hidden");
    if (cachePanel) cachePanel.classList.add("hidden");
    loadSystemConfigs();
  } else if (tabName === "cache") {
    if (tablesPanel) tablesPanel.classList.add("hidden");
    if (usersPanel) usersPanel.classList.add("hidden");
    if (configPanel) configPanel.classList.add("hidden");
    if (cachePanel) cachePanel.classList.remove("hidden");
    loadCacheStatistics();
  }
}

// 加载数据表列表
async function loadTablesList() {
  const tablesList = document.getElementById("tablesList");
  if (!tablesList) return;

  tablesList.innerHTML = '<div class="loading">正在加载表列表...</div>';

  try {
    const tables = [
      { 
        name: "accounts", 
        description: "邮箱账户信息表 (含API方法字段)", 
        count: "?",
        fields: "id, email, refresh_token, client_id, tags, last_refresh_time, next_refresh_time, refresh_status, refresh_error, created_at, updated_at, access_token, token_expires_at, api_method"
      },
      { 
        name: "users", 
        description: "用户账户表 (含角色和权限)", 
        count: "?",
        fields: "id, username, password_hash, email, role, bound_accounts, permissions, is_active, created_at, last_login"
      },
      { 
        name: "system_config", 
        description: "系统配置表", 
        count: "?",
        fields: "id, key, value, description, updated_at"
      },
      { 
        name: "emails_cache", 
        description: "邮件列表缓存表 (含LRU字段)", 
        count: "?",
        fields: "id, email_account, message_id, folder, subject, from_email, date, is_read, has_attachments, sender_initial, created_at, verification_code, access_count, last_accessed_at, cache_size"
      },
      {
        name: "email_details_cache",
        description: "邮件详情缓存表 (含LRU字段)",
        count: "?",
        fields: "id, email_account, message_id, subject, from_email, to_email, date, body_plain, body_html, created_at, verification_code, access_count, last_accessed_at, body_size"
      },
    ];

    // 获取每个表的记录数
    for (let table of tables) {
      try {
        const data = await apiRequest(`/admin/tables/${table.name}/count`);
        table.count = data.count || 0;
      } catch (error) {
        table.count = "N/A";
      }
    }

    // 生成表格HTML
    const iconMap = {
      accounts: "👥",
      users: "🔐",
      system_config: "⚙️",
      emails_cache: "📧",
      email_details_cache: "📨",
    };

    let html = `
            <div class="table-responsive">
                <table class="admin-data-table">
                    <thead>
                        <tr>
                            <th style="width: 60px; text-align: center;">图标</th>
                            <th style="width: 200px;">表名</th>
                            <th>描述</th>
                            <th style="width: 120px; text-align: center;">记录数</th>
                            <th style="width: 150px; text-align: center;">操作</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

    tables.forEach((table) => {
      const icon = iconMap[table.name] || "📊";
      const fieldsTooltip = table.fields ? `字段: ${table.fields}` : '';
      const fieldCount = table.fields ? table.fields.split(',').length : 0;
      html += `
                <tr onclick="loadTableData('${table.name}')" style="cursor: pointer;" title="${fieldsTooltip}">
                    <td style="text-align: center; font-size: 1.5rem;">${icon}</td>
                    <td><strong>${table.name}</strong></td>
                    <td>
                        ${table.description}
                        ${fieldCount > 0 ? `<br><small style="color: #64748b; font-size: 0.75rem;">字段数: ${fieldCount}</small>` : ''}
                    </td>
                    <td style="text-align: center;">
                        <span class="count-badge">${table.count}</span>
                    </td>
                    <td style="text-align: center;" onclick="event.stopPropagation()">
                        <button class="btn btn-primary btn-sm" onclick="loadTableData('${table.name}')">
                            <span>📋</span> 查看数据
                        </button>
                    </td>
                </tr>
            `;
    });

    html += `
                    </tbody>
                </table>
            </div>
        `;

    tablesList.innerHTML = html;
  } catch (error) {
    tablesList.innerHTML = `<div class="alert alert-error">加载表列表失败: ${error.message}</div>`;
  }
}

// 加载表数据
async function loadTableData(tableName) {
  currentTable = tableName;

  const currentTableNameElement = document.getElementById("currentTableName");
  if (currentTableNameElement) {
    currentTableNameElement.textContent = tableName;
  }

  const tablesListParent = document.getElementById("tablesList")?.parentElement;
  const tableDataPanel = document.getElementById("tableDataPanel");

  if (tablesListParent) tablesListParent.style.display = "none";
  if (tableDataPanel) tableDataPanel.classList.remove("hidden");

  const contentDiv = document.getElementById("tableDataContent");
  if (!contentDiv) return;

  contentDiv.innerHTML = '<div class="loading">正在加载数据...</div>';

  try {
    const data = await apiRequest(`/admin/tables/${tableName}`);
    currentTableData = data.records || [];
    renderTableData();
  } catch (error) {
    contentDiv.innerHTML = `<div class="alert alert-error">加载数据失败: ${error.message}</div>`;
  }
}

// 渲染表数据
function renderTableData() {
  const contentDiv = document.getElementById("tableDataContent");
  if (!contentDiv) return;

  if (currentTableData.length === 0) {
    contentDiv.innerHTML = '<div class="alert alert-info">暂无数据</div>';
    return;
  }

  const columns = Object.keys(currentTableData[0]);

  // 智能检测列类型
  function detectColumnType(col, value) {
    if (value === null || value === undefined) return 'null';
    if (col.toLowerCase().includes('date') || col.toLowerCase().includes('time') || col.toLowerCase().includes('at')) return 'date';
    if (col.toLowerCase().includes('count') || col.toLowerCase().includes('size') || col.toLowerCase().includes('id')) return 'number';
    if (typeof value === 'number') return 'number';
    return 'text';
  }

  let html = '<div class="table-responsive"><table class="admin-data-table">';
  html += "<thead><tr>";
  columns.forEach((col) => {
    // 格式化列名显示
    let displayName = col.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    html += `<th title="${col}">${displayName}</th>`;
  });
  html += "<th>操作</th></tr></thead><tbody>";

  currentTableData.forEach((row, index) => {
    html += "<tr>";
    columns.forEach((col) => {
      let value = row[col];
      let dataType = detectColumnType(col, value);
      let displayValue = value;
      
      if (value === null || value === undefined) {
        displayValue = '<span style="color: #94a3b8; font-style: italic;">NULL</span>';
        dataType = 'null';
      } else if (col.includes("password") || col.includes("token")) {
        displayValue = "••••••••";
      } else if (dataType === 'date') {
        // 格式化日期显示
        try {
          const date = new Date(value);
          if (!isNaN(date.getTime())) {
            displayValue = date.toLocaleString('zh-CN', { 
              year: 'numeric', 
              month: '2-digit', 
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            });
          }
        } catch (e) {
          // 保持原值
        }
      } else if (typeof value === "string" && value.length > 100) {
        displayValue = `<span title="${value.replace(/"/g, '&quot;')}">${value.substring(0, 100)}...</span>`;
      } else if (dataType === 'number') {
        // 数字格式化（添加千分位）
        if (typeof value === 'number' && value > 999) {
          displayValue = value.toLocaleString('zh-CN');
        }
      }
      
      html += `<td data-type="${dataType}" title="${value !== null && value !== undefined ? String(value).replace(/"/g, '&quot;') : 'NULL'}">${displayValue}</td>`;
    });
    html += `<td class="data-table-actions" style="white-space: nowrap;">
            <button class="btn btn-sm btn-secondary" onclick="editTableRow(${index})" style="margin-right: 4px;">✏️</button>
            <button class="btn btn-sm btn-danger" onclick="deleteTableRow(${index})">🗑️</button>
        </td>`;
    html += "</tr>";
  });

  html += "</tbody></table></div>";
  contentDiv.innerHTML = html;
}

// 返回表列表
function backToTablesList() {
  const tableDataPanel = document.getElementById("tableDataPanel");
  const tablesListParent = document.getElementById("tablesList")?.parentElement;

  if (tableDataPanel) tableDataPanel.classList.add("hidden");
  if (tablesListParent) tablesListParent.style.display = "block";

  currentTable = null;
  currentTableData = [];
}

// 刷新表数据
function refreshTableData() {
  if (currentTable) {
    loadTableData(currentTable);
  }
}

// 搜索表数据
function searchTableData() {
  const searchTerm = document
    .getElementById("tableSearch")
    ?.value.toLowerCase();

  if (!searchTerm) {
    renderTableData();
    return;
  }

  const filteredData = currentTableData.filter((row) => {
    return Object.values(row).some((value) => {
      return value && value.toString().toLowerCase().includes(searchTerm);
    });
  });

  const backup = currentTableData;
  currentTableData = filteredData;
  renderTableData();
  currentTableData = backup;
}

// 打开添加记录模态框
async function openAddRecordModal() {
  if (!currentTable) {
    showNotification("请先选择一个表", "error");
    return;
  }

  try {
    // 获取表结构
    const schema = await apiRequest(`/admin/tables/${currentTable}/schema`);
    currentTableColumns = schema.columns;

    // 设置模态框标题
    const modalTitle = document.getElementById("recordModalTitle");
    if (modalTitle) {
      modalTitle.textContent = `添加记录 - ${currentTable}`;
    }

    // 生成空白表单
    generateRecordForm(schema.columns, null);

    // 清空当前编辑记录
    currentEditRecord = null;

    // 显示模态框
    const modal = document.getElementById("recordModal");
    if (modal) {
      modal.classList.remove("hidden");
    }
  } catch (error) {
    showNotification(`获取表结构失败: ${error.message}`, "error");
  }
}

// 编辑表行
async function editTableRow(index) {
  const row = currentTableData[index];

  if (!row || !row.id) {
    showNotification("无法编辑：找不到记录ID", "error");
    return;
  }

  try {
    // 获取表结构
    const schema = await apiRequest(`/admin/tables/${currentTable}/schema`);
    currentTableColumns = schema.columns;

    // 设置模态框标题
    const modalTitle = document.getElementById("recordModalTitle");
    if (modalTitle) {
      modalTitle.textContent = `编辑记录 - ${currentTable} (ID: ${row.id})`;
    }

    // 生成预填充的表单
    generateRecordForm(schema.columns, row);

    // 保存当前编辑记录
    currentEditRecord = row;

    // 显示模态框
    const modal = document.getElementById("recordModal");
    if (modal) {
      modal.classList.remove("hidden");
    }
  } catch (error) {
    showNotification(`获取表结构失败: ${error.message}`, "error");
  }
}

// 生成记录表单
function generateRecordForm(columns, data) {
  const formContent = document.getElementById("recordFormContent");
  if (!formContent) return;

  let html = "";

  columns.forEach((col) => {
    const value = data ? (data[col.name] !== null ? data[col.name] : "") : "";
    const isId = col.name === "id";
    const isPrimaryKey = col.pk === 1;
    const isPassword = col.name.includes("password");
    const isJson =
      col.name === "tags" || col.type.toLowerCase().includes("json");
    const isDateTime = col.name.includes("_at") || col.name.includes("date");

    // 如果是自增主键且在添加模式下，跳过
    if (isPrimaryKey && !data) {
      return;
    }

    html += '<div class="form-group">';
    html += `<label for="field_${col.name}">${col.name}`;
    if (col.notnull === 1 && !isPrimaryKey) {
      html += ' <span style="color: red;">*</span>';
    }
    html += `</label>`;

    // 显示字段类型信息
    html += `<div style="font-size: 0.75rem; color: #64748b; margin-bottom: 4px;">类型: ${col.type}`;
    if (col.dflt_value !== null) {
      html += ` | 默认值: ${col.dflt_value}`;
    }
    html += "</div>";

    // 根据字段类型生成不同的输入控件
    if (isPrimaryKey && data) {
      // 主键只读
      html += `<input type="text" id="field_${col.name}" class="form-control" value="${value}" readonly style="background-color: #f1f5f9;">`;
    } else if (isPassword) {
      // 密码字段
      html += `<input type="password" id="field_${
        col.name
      }" class="form-control" value="${value}" ${
        col.notnull === 1 ? "required" : ""
      }>`;
      html +=
        '<div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">编辑时留空表示不修改密码</div>';
    } else if (isJson) {
      // JSON字段
      const jsonValue = value
        ? typeof value === "string"
          ? value
          : JSON.stringify(value, null, 2)
        : "[]";
      html += `<textarea id="field_${col.name}" class="form-control" rows="4" ${
        col.notnull === 1 ? "required" : ""
      }>${jsonValue}</textarea>`;
      html +=
        '<div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">请输入有效的JSON格式</div>';
    } else if (col.type.toLowerCase().includes("text")) {
      // 文本区域
      html += `<textarea id="field_${col.name}" class="form-control" rows="3" ${
        col.notnull === 1 ? "required" : ""
      }>${value}</textarea>`;
    } else if (col.type.toLowerCase().includes("int")) {
      // 数字
      html += `<input type="number" id="field_${
        col.name
      }" class="form-control" value="${value}" ${
        col.notnull === 1 ? "required" : ""
      }>`;
    } else {
      // 默认文本输入
      html += `<input type="text" id="field_${
        col.name
      }" class="form-control" value="${value}" ${
        col.notnull === 1 ? "required" : ""
      }>`;
    }

    html += "</div>";
  });

  formContent.innerHTML = html;
}

// 保存表记录
async function saveTableRecord() {
  if (!currentTable) {
    showNotification("未知错误：没有选择表", "error");
    return;
  }

  // 收集表单数据
  const formData = {};
  let hasError = false;

  currentTableColumns.forEach((col) => {
    const fieldElement = document.getElementById(`field_${col.name}`);
    if (!fieldElement) return;

    // 跳过只读的主键字段（编辑模式）
    if (col.pk === 1 && currentEditRecord) {
      return;
    }

    let value = fieldElement.value.trim();

    // 检查必填字段
    if (col.notnull === 1 && !value && col.pk !== 1) {
      showNotification(`字段 ${col.name} 是必填的`, "error");
      hasError = true;
      return;
    }

    // 处理空值
    if (value === "" && col.notnull === 0) {
      formData[col.name] = null;
      return;
    }

    // 跳过密码字段（如果为空且在编辑模式）
    if (col.name.includes("password") && !value && currentEditRecord) {
      return;
    }

    // 处理JSON字段
    if (col.name === "tags" || col.type.toLowerCase().includes("json")) {
      try {
        formData[col.name] = value ? JSON.parse(value) : null;
      } catch (e) {
        showNotification(`字段 ${col.name} 的JSON格式无效`, "error");
        hasError = true;
        return;
      }
    }
    // 处理数字字段
    else if (col.type.toLowerCase().includes("int")) {
      formData[col.name] = value ? parseInt(value) : null;
    }
    // 处理其他字段
    else {
      formData[col.name] = value;
    }
  });

  if (hasError) {
    return;
  }

  try {
    if (currentEditRecord) {
      // 更新记录
      await apiRequest(
        `/admin/tables/${currentTable}/${currentEditRecord.id}`,
        {
          method: "PUT",
          body: JSON.stringify({ data: formData }),
        }
      );
      showNotification("记录更新成功", "success");
    } else {
      // 创建记录
      await apiRequest(`/admin/tables/${currentTable}`, {
        method: "POST",
        body: JSON.stringify({ data: formData }),
      });
      showNotification("记录创建成功", "success");
    }

    // 关闭模态框
    closeRecordModal();

    // 刷新表数据
    refreshTableData();
  } catch (error) {
    showNotification(`保存失败: ${error.message}`, "error");
  }
}

// 关闭记录模态框
function closeRecordModal() {
  const modal = document.getElementById("recordModal");
  const formContent = document.getElementById("recordFormContent");

  if (modal) modal.classList.add("hidden");
  if (formContent) formContent.innerHTML = "";

  currentEditRecord = null;
  currentTableColumns = [];
}

// 删除表行
async function deleteTableRow(index) {
  const row = currentTableData[index];
  const id = row.id;

  if (!id) {
    showNotification("无法删除：找不到记录ID", "error");
    return;
  }

  if (!confirm(`确定要删除这条记录吗？ (ID: ${id})`)) {
    return;
  }

  try {
    await apiRequest(`/admin/tables/${currentTable}/${id}`, {
      method: "DELETE",
    });
    showNotification("删除成功", "success");
    refreshTableData();
  } catch (error) {
    showNotification(`删除失败: ${error.message}`, "error");
  }
}

// 加载系统配置
async function loadSystemConfigs() {
  const configsList = document.getElementById("configsList");
  if (!configsList) return;

  configsList.innerHTML = '<div class="loading">正在加载配置...</div>';

  try {
    const data = await apiRequest("/admin/config");
    const configs = data.configs || [];

    if (configs.length === 0) {
      configsList.innerHTML = '<div class="alert alert-info">暂无配置项</div>';
      return;
    }

    // 生成表格HTML
    const iconMap = {
      imap_server: "🌐",
      imap_port: "🔌",
      imap_use_ssl: "🔒",
      max_connections: "🔗",
      cache_timeout: "⏱️",
      token_refresh_interval: "🔄",
    };

    let html = `
            <div class="table-responsive">
                <table class="admin-config-table">
                    <thead>
                        <tr>
                            <th style="width: 60px; text-align: center;">图标</th>
                            <th style="width: 200px;">配置键</th>
                            <th style="width: 200px;">当前值</th>
                            <th>描述</th>
                            <th style="width: 150px; text-align: center;">更新时间</th>
                            <th style="width: 120px; text-align: center;">操作</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

    configs.forEach((config) => {
      const icon = iconMap[config.key] || "⚙️";
      const updateTime = config.updated_at
        ? typeof formatRefreshTime === "function"
          ? formatRefreshTime(config.updated_at)
          : config.updated_at
        : "N/A";
      const description = config.description || "-";

      // 转义特殊字符以避免JavaScript错误
      const escapedKey = config.key.replace(/'/g, "\\'");
      const escapedValue = config.value.replace(/'/g, "\\'");
      const escapedDesc = description.replace(/'/g, "\\'");

      html += `
                <tr onclick="openConfigEditModal('${escapedKey}', '${escapedValue}', '${escapedDesc}', ${config.id})" style="cursor: pointer;">
                    <td style="text-align: center; font-size: 1.5rem;">${icon}</td>
                    <td><strong>${config.key}</strong></td>
                    <td><code class="config-value-cell">${config.value}</code></td>
                    <td>${description}</td>
                    <td style="text-align: center; font-size: 0.875rem; color: #64748b;">${updateTime}</td>
                    <td style="text-align: center;" onclick="event.stopPropagation()">
                        <button class="btn btn-secondary btn-sm" onclick="openConfigEditModal('${escapedKey}', '${escapedValue}', '${escapedDesc}', ${config.id})">
                            <span>✏️</span> 编辑
                        </button>
                    </td>
                </tr>
            `;
    });

    html += `
                    </tbody>
                </table>
            </div>
        `;

    configsList.innerHTML = html;
  } catch (error) {
    configsList.innerHTML = `<div class="alert alert-error">加载配置失败: ${error.message}</div>`;
  }
}

// 全局变量存储当前编辑的配置
let currentEditingConfigKey = null;

// 打开配置编辑模态框
function openConfigEditModal(key, value, description, configId) {
  currentEditingConfigKey = key;

  // 设置表单值
  document.getElementById("configKey").value = key;
  document.getElementById("configValue").value = value;
  document.getElementById("configDescription").value =
    description !== "-" ? description : "";

  // 显示模态框
  const modal = document.getElementById("configEditModal");
  if (modal) {
    modal.classList.remove("hidden");
  }
}

// 关闭配置编辑模态框
function closeConfigEditModal() {
  const modal = document.getElementById("configEditModal");
  if (modal) {
    modal.classList.add("hidden");
  }

  // 清空表单
  document.getElementById("configKey").value = "";
  document.getElementById("configValue").value = "";
  document.getElementById("configDescription").value = "";

  currentEditingConfigKey = null;
}

// 保存配置编辑
async function saveConfigEdit() {
  if (!currentEditingConfigKey) {
    showNotification("未知错误：没有选择配置项", "error");
    return;
  }

  const key = currentEditingConfigKey;
  const value = document.getElementById("configValue").value.trim();
  const description = document.getElementById("configDescription").value.trim();

  if (!value) {
    showNotification("配置值不能为空", "error");
    return;
  }

  try {
    await apiRequest("/admin/config", {
      method: "POST",
      body: JSON.stringify({
        key: key,
        value: value,
        description: description || null,
      }),
    });

    showNotification("配置更新成功", "success");
    closeConfigEditModal();
    loadSystemConfigs();
  } catch (error) {
    showNotification(`更新配置失败: ${error.message}`, "error");
  }
}

// 编辑配置（保留旧函数以兼容）
async function editConfig(key, currentValue) {
  // 直接调用新的模态框函数
  openConfigEditModal(key, currentValue, "", null);
}

// ============================================================================
// 缓存统计管理
// ============================================================================

/**
 * 加载缓存统计信息
 */
async function loadCacheStatistics() {
  const cacheStatistics = document.getElementById("cacheStatistics");
  if (!cacheStatistics) return;

  cacheStatistics.innerHTML = '<div class="loading">正在加载缓存统计...</div>';

  try {
    const stats = await apiRequest("/admin/cache/statistics");

    // 渲染缓存统计卡片
    cacheStatistics.innerHTML = `
      <div class="cache-stats-grid">
        <!-- 总体统计 -->
        <div class="cache-stat-card">
          <div class="stat-header">
            <span class="stat-icon">💾</span>
            <h4>数据库大小</h4>
          </div>
          <div class="stat-value">${stats.db_size_mb} MB</div>
          <div class="stat-detail">
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${stats.size_usage_percent}%"></div>
            </div>
            <span class="text-sm" style="color: #64748b">
              ${stats.size_usage_percent}% / ${stats.max_size_mb} MB
            </span>
          </div>
        </div>

        <!-- 缓存命中率 -->
        <div class="cache-stat-card">
          <div class="stat-header">
            <span class="stat-icon">🎯</span>
            <h4>缓存命中率</h4>
          </div>
          <div class="stat-value">${stats.hit_rate}%</div>
          <div class="stat-detail">
            <div class="progress-bar">
              <div class="progress-fill ${stats.hit_rate > 70 ? 'success' : 'warning'}" 
                   style="width: ${stats.hit_rate}%"></div>
            </div>
            <span class="text-sm" style="color: #64748b">
              ${stats.hit_rate > 70 ? '✅ 良好' : '⚠️ 需优化'}
            </span>
          </div>
        </div>

        <!-- 邮件列表缓存 -->
        <div class="cache-stat-card">
          <div class="stat-header">
            <span class="stat-icon">📧</span>
            <h4>邮件列表缓存</h4>
          </div>
          <div class="stat-value">${stats.emails_cache.count}</div>
          <div class="stat-detail">
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${stats.emails_cache.usage_percent}%"></div>
            </div>
            <span class="text-sm" style="color: #64748b">
              ${stats.emails_cache.usage_percent}% / ${stats.emails_cache.max_count} 条
            </span>
          </div>
          <div class="stat-meta">
            <span>大小: ${(stats.emails_cache.size_bytes / 1024).toFixed(2)} KB</span>
          </div>
        </div>

        <!-- 邮件详情缓存 -->
        <div class="cache-stat-card">
          <div class="stat-header">
            <span class="stat-icon">📨</span>
            <h4>邮件详情缓存</h4>
          </div>
          <div class="stat-value">${stats.details_cache.count}</div>
          <div class="stat-detail">
            <div class="progress-bar">
              <div class="progress-fill" style="width: ${stats.details_cache.usage_percent}%"></div>
            </div>
            <span class="text-sm" style="color: #64748b">
              ${stats.details_cache.usage_percent}% / ${stats.details_cache.max_count} 条
            </span>
          </div>
          <div class="stat-meta">
            <span>大小: ${(stats.details_cache.size_bytes / 1024).toFixed(2)} KB</span>
          </div>
        </div>
      </div>
    `;
  } catch (error) {
    console.error("加载缓存统计失败:", error);
    cacheStatistics.innerHTML = `
      <div class="error">
        ❌ 加载失败: ${error.message}
      </div>
    `;
  }
}

/**
 * 触发LRU清理
 */
async function triggerLRUCleanup() {
  if (!confirm("确定要执行LRU缓存清理吗？\n\n这将删除最少访问的缓存记录。")) {
    return;
  }

  try {
    const result = await apiRequest("/admin/cache/cleanup", { method: "POST" });
    showNotification(
      `${result.message}\n删除了 ${result.deleted_count} 条记录`,
      "success",
      "✅ 清理完成"
    );
    loadCacheStatistics();
  } catch (error) {
    console.error("LRU清理失败:", error);
    showNotification("LRU清理失败: " + error.message, "error", "❌ 错误");
  }
}

/**
 * 清除所有缓存
 */
async function clearAllCache() {
  if (!confirm("⚠️ 确定要清除所有缓存吗？\n\n这将删除所有邮件列表和详情缓存！")) {
    return;
  }

  try {
    const result = await apiRequest("/admin/cache", { method: "DELETE" });
    showNotification(
      `${result.message}\n删除了 ${result.deleted_count} 条记录`,
      "success",
      "✅ 清除完成"
    );
    loadCacheStatistics();
  } catch (error) {
    console.error("清除缓存失败:", error);
    showNotification("清除缓存失败: " + error.message, "error", "❌ 错误");
  }
}

console.log("✅ [Admin] 管理面板模块加载完成");
