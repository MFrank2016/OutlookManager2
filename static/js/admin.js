// admin.js - 管理面板模块

// 管理面板全局变量
let currentTable = null;
let currentTableData = [];
let currentTableColumns = [];
let currentEditRecord = null;

// 切换管理面板标签
function switchAdminTab(tabName, tabElement) {
    // 切换标签激活状态
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    if (tabElement) {
        tabElement.classList.add('active');
    }
    
    // 切换面板显示
    if (tabName === 'tables') {
        const tablesPanel = document.getElementById('tablesPanel');
        const configPanel = document.getElementById('configPanel');
        if (tablesPanel) tablesPanel.classList.remove('hidden');
        if (configPanel) configPanel.classList.add('hidden');
        loadTablesList();
    } else if (tabName === 'config') {
        const tablesPanel = document.getElementById('tablesPanel');
        const configPanel = document.getElementById('configPanel');
        if (tablesPanel) tablesPanel.classList.add('hidden');
        if (configPanel) configPanel.classList.remove('hidden');
        loadSystemConfigs();
    }
}

// 加载数据表列表
async function loadTablesList() {
    const tablesList = document.getElementById('tablesList');
    if (!tablesList) return;
    
    tablesList.innerHTML = '<div class="loading">正在加载表列表...</div>';
    
    try {
        const tables = [
            { name: 'accounts', description: '邮箱账户信息表', count: '?' },
            { name: 'admins', description: '管理员账户表', count: '?' },
            { name: 'system_config', description: '系统配置表', count: '?' }
        ];
        
        // 获取每个表的记录数
        for (let table of tables) {
            try {
                const data = await apiRequest(`/admin/tables/${table.name}/count`);
                table.count = data.count || 0;
            } catch (error) {
                table.count = 'N/A';
            }
        }
        
        tablesList.innerHTML = tables.map(table => {
            const iconMap = {
                'accounts': '👥',
                'admins': '🔐',
                'system_config': '⚙️'
            };
            const icon = iconMap[table.name] || '📊';
            
            return `
                <div class="table-item" onclick="loadTableData('${table.name}')">
                    <div class="table-info">
                        <div class="table-icon">${icon}</div>
                        <div class="table-details">
                            <h5>${table.name}</h5>
                            <p>${table.description}</p>
                            <div class="table-meta">
                                <div class="table-count">
                                    <span>记录数:</span>
                                    <span class="count-badge">${table.count}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="table-actions" onclick="event.stopPropagation()">
                        <button class="btn btn-primary btn-sm" onclick="loadTableData('${table.name}')">
                            <span>📋</span>
                            查看数据
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        tablesList.innerHTML = `<div class="alert alert-error">加载表列表失败: ${error.message}</div>`;
    }
}

// 加载表数据
async function loadTableData(tableName) {
    currentTable = tableName;
    
    const currentTableNameElement = document.getElementById('currentTableName');
    if (currentTableNameElement) {
        currentTableNameElement.textContent = tableName;
    }
    
    const tablesListParent = document.getElementById('tablesList')?.parentElement;
    const tableDataPanel = document.getElementById('tableDataPanel');
    
    if (tablesListParent) tablesListParent.style.display = 'none';
    if (tableDataPanel) tableDataPanel.classList.remove('hidden');
    
    const contentDiv = document.getElementById('tableDataContent');
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
    const contentDiv = document.getElementById('tableDataContent');
    if (!contentDiv) return;
    
    if (currentTableData.length === 0) {
        contentDiv.innerHTML = '<div class="alert alert-info">暂无数据</div>';
        return;
    }
    
    const columns = Object.keys(currentTableData[0]);
    
    let html = '<div class="table-responsive"><table class="data-table">';
    html += '<thead><tr>';
    columns.forEach(col => {
        html += `<th>${col}</th>`;
    });
    html += '<th>操作</th></tr></thead><tbody>';
    
    currentTableData.forEach((row, index) => {
        html += '<tr>';
        columns.forEach(col => {
            let value = row[col];
            if (value === null || value === undefined) {
                value = '<span style="color: #cbd5e1;">NULL</span>';
            } else if (col.includes('password')) {
                value = '********';
            } else if (typeof value === 'string' && value.length > 50) {
                value = value.substring(0, 50) + '...';
            }
            html += `<td>${value}</td>`;
        });
        html += `<td class="data-table-actions">
            <button class="btn btn-sm btn-secondary" onclick="editTableRow(${index})">✏️ 编辑</button>
            <button class="btn btn-sm btn-danger" onclick="deleteTableRow(${index})">🗑️ 删除</button>
        </td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    contentDiv.innerHTML = html;
}

// 返回表列表
function backToTablesList() {
    const tableDataPanel = document.getElementById('tableDataPanel');
    const tablesListParent = document.getElementById('tablesList')?.parentElement;
    
    if (tableDataPanel) tableDataPanel.classList.add('hidden');
    if (tablesListParent) tablesListParent.style.display = 'block';
    
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
    const searchTerm = document.getElementById('tableSearch')?.value.toLowerCase();
    
    if (!searchTerm) {
        renderTableData();
        return;
    }
    
    const filteredData = currentTableData.filter(row => {
        return Object.values(row).some(value => {
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
        showNotification('请先选择一个表', 'error');
        return;
    }
    
    try {
        // 获取表结构
        const schema = await apiRequest(`/admin/tables/${currentTable}/schema`);
        currentTableColumns = schema.columns;
        
        // 设置模态框标题
        const modalTitle = document.getElementById('recordModalTitle');
        if (modalTitle) {
            modalTitle.textContent = `添加记录 - ${currentTable}`;
        }
        
        // 生成空白表单
        generateRecordForm(schema.columns, null);
        
        // 清空当前编辑记录
        currentEditRecord = null;
        
        // 显示模态框
        const modal = document.getElementById('recordModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    } catch (error) {
        showNotification(`获取表结构失败: ${error.message}`, 'error');
    }
}

// 编辑表行
async function editTableRow(index) {
    const row = currentTableData[index];
    
    if (!row || !row.id) {
        showNotification('无法编辑：找不到记录ID', 'error');
        return;
    }
    
    try {
        // 获取表结构
        const schema = await apiRequest(`/admin/tables/${currentTable}/schema`);
        currentTableColumns = schema.columns;
        
        // 设置模态框标题
        const modalTitle = document.getElementById('recordModalTitle');
        if (modalTitle) {
            modalTitle.textContent = `编辑记录 - ${currentTable} (ID: ${row.id})`;
        }
        
        // 生成预填充的表单
        generateRecordForm(schema.columns, row);
        
        // 保存当前编辑记录
        currentEditRecord = row;
        
        // 显示模态框
        const modal = document.getElementById('recordModal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    } catch (error) {
        showNotification(`获取表结构失败: ${error.message}`, 'error');
    }
}

// 生成记录表单
function generateRecordForm(columns, data) {
    const formContent = document.getElementById('recordFormContent');
    if (!formContent) return;
    
    let html = '';
    
    columns.forEach(col => {
        const value = data ? (data[col.name] !== null ? data[col.name] : '') : '';
        const isId = col.name === 'id';
        const isPrimaryKey = col.pk === 1;
        const isPassword = col.name.includes('password');
        const isJson = col.name === 'tags' || col.type.toLowerCase().includes('json');
        const isDateTime = col.name.includes('_at') || col.name.includes('date');
        
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
        html += '</div>';
        
        // 根据字段类型生成不同的输入控件
        if (isPrimaryKey && data) {
            // 主键只读
            html += `<input type="text" id="field_${col.name}" class="form-control" value="${value}" readonly style="background-color: #f1f5f9;">`;
        } else if (isPassword) {
            // 密码字段
            html += `<input type="password" id="field_${col.name}" class="form-control" value="${value}" ${col.notnull === 1 ? 'required' : ''}>`;
            html += '<div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">编辑时留空表示不修改密码</div>';
        } else if (isJson) {
            // JSON字段
            const jsonValue = value ? (typeof value === 'string' ? value : JSON.stringify(value, null, 2)) : '[]';
            html += `<textarea id="field_${col.name}" class="form-control" rows="4" ${col.notnull === 1 ? 'required' : ''}>${jsonValue}</textarea>`;
            html += '<div style="font-size: 0.75rem; color: #64748b; margin-top: 4px;">请输入有效的JSON格式</div>';
        } else if (col.type.toLowerCase().includes('text')) {
            // 文本区域
            html += `<textarea id="field_${col.name}" class="form-control" rows="3" ${col.notnull === 1 ? 'required' : ''}>${value}</textarea>`;
        } else if (col.type.toLowerCase().includes('int')) {
            // 数字
            html += `<input type="number" id="field_${col.name}" class="form-control" value="${value}" ${col.notnull === 1 ? 'required' : ''}>`;
        } else {
            // 默认文本输入
            html += `<input type="text" id="field_${col.name}" class="form-control" value="${value}" ${col.notnull === 1 ? 'required' : ''}>`;
        }
        
        html += '</div>';
    });
    
    formContent.innerHTML = html;
}

// 保存表记录
async function saveTableRecord() {
    if (!currentTable) {
        showNotification('未知错误：没有选择表', 'error');
        return;
    }
    
    // 收集表单数据
    const formData = {};
    let hasError = false;
    
    currentTableColumns.forEach(col => {
        const fieldElement = document.getElementById(`field_${col.name}`);
        if (!fieldElement) return;
        
        // 跳过只读的主键字段（编辑模式）
        if (col.pk === 1 && currentEditRecord) {
            return;
        }
        
        let value = fieldElement.value.trim();
        
        // 检查必填字段
        if (col.notnull === 1 && !value && col.pk !== 1) {
            showNotification(`字段 ${col.name} 是必填的`, 'error');
            hasError = true;
            return;
        }
        
        // 处理空值
        if (value === '' && col.notnull === 0) {
            formData[col.name] = null;
            return;
        }
        
        // 跳过密码字段（如果为空且在编辑模式）
        if (col.name.includes('password') && !value && currentEditRecord) {
            return;
        }
        
        // 处理JSON字段
        if (col.name === 'tags' || col.type.toLowerCase().includes('json')) {
            try {
                formData[col.name] = value ? JSON.parse(value) : null;
            } catch (e) {
                showNotification(`字段 ${col.name} 的JSON格式无效`, 'error');
                hasError = true;
                return;
            }
        }
        // 处理数字字段
        else if (col.type.toLowerCase().includes('int')) {
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
            await apiRequest(`/admin/tables/${currentTable}/${currentEditRecord.id}`, {
                method: 'PUT',
                body: JSON.stringify({ data: formData })
            });
            showNotification('记录更新成功', 'success');
        } else {
            // 创建记录
            await apiRequest(`/admin/tables/${currentTable}`, {
                method: 'POST',
                body: JSON.stringify({ data: formData })
            });
            showNotification('记录创建成功', 'success');
        }
        
        // 关闭模态框
        closeRecordModal();
        
        // 刷新表数据
        refreshTableData();
    } catch (error) {
        showNotification(`保存失败: ${error.message}`, 'error');
    }
}

// 关闭记录模态框
function closeRecordModal() {
    const modal = document.getElementById('recordModal');
    const formContent = document.getElementById('recordFormContent');
    
    if (modal) modal.classList.add('hidden');
    if (formContent) formContent.innerHTML = '';
    
    currentEditRecord = null;
    currentTableColumns = [];
}

// 删除表行
async function deleteTableRow(index) {
    const row = currentTableData[index];
    const id = row.id;
    
    if (!id) {
        showNotification('无法删除：找不到记录ID', 'error');
        return;
    }
    
    if (!confirm(`确定要删除这条记录吗？ (ID: ${id})`)) {
        return;
    }
    
    try {
        await apiRequest(`/admin/tables/${currentTable}/${id}`, { method: 'DELETE' });
        showNotification('删除成功', 'success');
        refreshTableData();
    } catch (error) {
        showNotification(`删除失败: ${error.message}`, 'error');
    }
}

// 加载系统配置
async function loadSystemConfigs() {
    const configsList = document.getElementById('configsList');
    if (!configsList) return;
    
    configsList.innerHTML = '<div class="loading">正在加载配置...</div>';
    
    try {
        const data = await apiRequest('/admin/config');
        const configs = data.configs || [];
        
        if (configs.length === 0) {
            configsList.innerHTML = '<div class="alert alert-info">暂无配置项</div>';
            return;
        }
        
        configsList.innerHTML = configs.map(config => {
            const iconMap = {
                'imap_server': '🌐',
                'imap_port': '🔌',
                'imap_use_ssl': '🔒',
                'max_connections': '🔗',
                'cache_timeout': '⏱️',
                'token_refresh_interval': '🔄'
            };
            const icon = iconMap[config.key] || '⚙️';
            
            // 格式化更新时间
            const updateTime = config.updated_at ? (typeof formatRefreshTime === 'function' ? formatRefreshTime(config.updated_at) : config.updated_at) : 'N/A';
            
            return `
                <div class="config-item">
                    <div class="config-info">
                        <div class="config-icon">${icon}</div>
                        <div class="config-details">
                            <h5 class="config-key">${config.key}</h5>
                            <div class="config-value">${config.value}</div>
                            <div class="config-meta">
                                ${config.description ? `<span class="config-description">${config.description}</span>` : ''}
                                <span class="config-updated">更新: ${updateTime}</span>
                            </div>
                        </div>
                    </div>
                    <div class="config-actions">
                        <button class="btn btn-secondary btn-sm" onclick="editConfig('${config.key}', '${config.value}')">
                            <span>✏️</span>
                            编辑
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        configsList.innerHTML = `<div class="alert alert-error">加载配置失败: ${error.message}</div>`;
    }
}

// 编辑配置
async function editConfig(key, currentValue) {
    const newValue = prompt(`修改配置项: ${key}\n当前值: ${currentValue}\n\n请输入新值:`, currentValue);
    
    if (newValue === null || newValue === currentValue) {
        return;
    }
    
    try {
        await apiRequest('/admin/config', {
            method: 'POST',
            body: JSON.stringify({
                key: key,
                value: newValue
            })
        });
        showNotification('配置更新成功', 'success');
        loadSystemConfigs();
    } catch (error) {
        showNotification(`更新配置失败: ${error.message}`, 'error');
    }
}

console.log('✅ [Admin] 管理面板模块加载完成');
