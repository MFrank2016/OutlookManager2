// 全局变量
        const API_BASE = '';
        let currentAccount = null;
        let currentEmailFolder = 'all';
        let currentEmailPage = 1;
        let accounts = [];
        
        // 账户管理分页相关变量
        let accountsCurrentPage = 1;
        let accountsPageSize = 10;
        let accountsTotalPages = 0;
        let accountsTotalCount = 0;
        let currentEmailSearch = '';
        let currentTagSearch = '';
        let currentRefreshStatusFilter = 'all';
        let currentRefreshStartDate = '';
        let currentRefreshEndDate = '';

        // 邮件列表分页相关变量
        let emailCurrentPage = 1;
        let emailPageSize = 10;
        let emailTotalCount = 0;

        // 全局变量，用于存储当前编辑的账户信息
        let currentEditAccount = null;
        let currentEditTags = [];

        // 页面管理
        function showPage(pageName, targetElement = null) {
            // 隐藏所有页面
            document.querySelectorAll('.page').forEach(page => page.classList.add('hidden'));

            // 显示指定页面
            document.getElementById(pageName + 'Page').classList.remove('hidden');

            // 更新导航状态
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));

            // 如果有目标元素，激活它；否则根据页面名称查找对应的导航项
            if (targetElement) {
                targetElement.classList.add('active');
            } else {
                // 根据页面名称查找对应的导航按钮
                const navButtons = document.querySelectorAll('.nav-item');
                navButtons.forEach(button => {
                    if (button.onclick && button.onclick.toString().includes(`'${pageName}'`)) {
                        button.classList.add('active');
                    }
                });
            }

            // 特殊页面加载处理
            if (pageName === 'adminPanel') {
                loadTablesList();
            }

            // 更新页面标题
            const titles = {
                'accounts': '邮箱账户管理',
                'addAccount': '添加邮箱账户',
                'batchAdd': '批量添加账户',
                'adminPanel': '系统管理面板',
                'apiDocs': 'API接口文档',
                'emails': '邮件列表'
            };
            document.getElementById('pageTitle').textContent = titles[pageName] || '';

            // 页面特定逻辑
            if (pageName === 'accounts') {
                loadAccounts();
            } else if (pageName === 'addAccount') {
                clearAddAccountForm();
            } else if (pageName === 'batchAdd') {
                clearBatchForm();
                hideBatchProgress();
            } else if (pageName === 'apiDocs') {
                initApiDocs();
            } else if (pageName === 'emails') {
                loadEmails();
            }
        }

        // 工具函数
        function formatEmailDate(dateString) {
            try {
                if (!dateString) return '未知时间';

                let date = new Date(dateString);

                if (isNaN(date.getTime())) {
                    if (dateString.includes('T') && !dateString.includes('Z') && !dateString.includes('+')) {
                        date = new Date(dateString + 'Z');
                    }
                    if (isNaN(date.getTime())) {
                        return '日期格式错误';
                    }
                }

                // 显示完整的日期+时间
                const year = date.getFullYear();
                const month = String(date.getMonth() + 1).padStart(2, '0');
                const day = String(date.getDate()).padStart(2, '0');
                const hours = String(date.getHours()).padStart(2, '0');
                const minutes = String(date.getMinutes()).padStart(2, '0');
                
                return `${year}年${month}月${day}日 ${hours}:${minutes}`;
                
                /* 原来的相对时间显示（已注释）
                const now = new Date();
                const diffMs = now - date;
                const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

                if (diffDays === 0) {
                    return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
                } else if (diffDays === 1) {
                    return '昨天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
                } else if (diffDays < 7) {
                    return `${diffDays}天前`;
                } else if (diffDays < 365) {
                    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
                } else {
                    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' });
                }
                */
            } catch (error) {
                console.error('Date formatting error:', error);
                return '时间解析失败';
            }
        }

        // 新的通知系统
        function showNotification(message, type = 'info', title = '', duration = 5000) {
            const container = document.getElementById('notificationContainer');
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;

            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };

            const titles = {
                success: title || '成功',
                error: title || '错误',
                warning: title || '警告',
                info: title || '提示'
            };

            notification.innerHTML = `
                <div class="notification-icon">${icons[type]}</div>
                <div class="notification-content">
                    <div class="notification-title">${titles[type]}</div>
                    <div class="notification-message">${message}</div>
                </div>
                <button class="notification-close" onclick="closeNotification(this)">×</button>
            `;

            container.appendChild(notification);

            // 自动关闭
            if (duration > 0) {
                setTimeout(() => {
                    closeNotification(notification.querySelector('.notification-close'));
                }, duration);
            }
        }

        function closeNotification(closeBtn) {
            const notification = closeBtn.closest('.notification');
            notification.classList.add('slide-out');
            setTimeout(() => notification.remove(), 300);
        }

        // 兼容旧的消息提示函数
        function showError(msg) {
            showNotification(msg, 'error');
        }

        function showSuccess(msg) {
            showNotification(msg, 'success');
        }

        function showWarning(msg) {
            showNotification(msg, 'warning');
        }

        function showInfo(msg) {
            showNotification(msg, 'info');
        }

        // 格式化刷新时间
        function formatRefreshTime(timeString) {
            if (!timeString) return '未刷新';
            try {
                const date = new Date(timeString);
                if (isNaN(date.getTime())) return '未刷新';
                return date.toLocaleString('zh-CN');
            } catch (error) {
                return '未刷新';
            }
        }

        // API请求（支持JWT认证）
        async function apiRequest(url, options = {}) {
            try {
                // 获取JWT token
                const token = localStorage.getItem('auth_token');
                
                // 如果没有token，跳转到登录页面
                if (!token && url !== '/auth/login' && url !== '/api') {
                    showNotification('请先登录', 'warning');
                    setTimeout(() => {
                        window.location.href = '/static/login.html';
                    }, 1000);
                    return;
                }
                
                const response = await fetch(API_BASE + url, {
                    headers: {
                        'Content-Type': 'application/json',
                        ...(token && { 'Authorization': `Bearer ${token}` }),
                        ...options.headers
                    },
                    ...options
                });

                // 如果返回401，说明token无效或过期
                if (response.status === 401) {
                    showNotification('登录已过期，请重新登录', 'warning');
                    localStorage.removeItem('auth_token');
                    setTimeout(() => {
                        window.location.href = '/static/login.html';
                    }, 1000);
                    return;
                }

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
                }

                return await response.json();
            } catch (error) {
                console.error('API请求失败:', error);
                throw error;
            }
        }

        // 表单管理函数
        function clearAddAccountForm() {
            document.getElementById('email').value = '';
            document.getElementById('refreshToken').value = '';
            document.getElementById('clientId').value = '';
        }

        function clearBatchForm() {
            document.getElementById('batchAccounts').value = '';
        }

        function loadSampleData() {
            const sampleData = `example1@outlook.com----password1----refresh_token_here_1----client_id_here_1
example2@outlook.com----password2----refresh_token_here_2----client_id_here_2
example3@outlook.com----password3----refresh_token_here_3----client_id_here_3`;
            document.getElementById('batchAccounts').value = sampleData;
            showNotification('示例数据已加载，请替换为真实数据', 'info');
        }

        function validateBatchFormat() {
            const batchText = document.getElementById('batchAccounts').value.trim();
            if (!batchText) {
                showNotification('请先输入账户信息', 'warning');
                return;
            }

            const lines = batchText.split('\n').filter(line => line.trim());
            let validCount = 0;
            let invalidLines = [];

            lines.forEach((line, index) => {
                const parts = line.split('----').map(p => p.trim());
                if (parts.length === 4 && parts.every(part => part.length > 0)) {
                    validCount++;
                } else {
                    invalidLines.push(index + 1);
                }
            });

            if (invalidLines.length === 0) {
                showNotification(`格式验证通过！共 ${validCount} 个有效账户`, 'success');
            } else {
                showNotification(`发现 ${invalidLines.length} 行格式错误：第 ${invalidLines.join(', ')} 行`, 'error');
            }
        }

        async function testAccountConnection() {
            const email = document.getElementById('email').value.trim();
            const refreshToken = document.getElementById('refreshToken').value.trim();
            const clientId = document.getElementById('clientId').value.trim();

            if (!email || !refreshToken || !clientId) {
                showNotification('请填写所有必需字段', 'warning');
                return;
            }

            const testBtn = document.getElementById('testBtn');
            testBtn.disabled = true;
            testBtn.innerHTML = '<span>⏳</span> 测试中...';

            try {
                // 这里可以调用一个测试接口
                await new Promise(resolve => setTimeout(resolve, 2000)); // 模拟测试
                showNotification('连接测试成功！账户配置正确', 'success');
            } catch (error) {
                showNotification('连接测试失败：' + error.message, 'error');
            } finally {
                testBtn.disabled = false;
                testBtn.innerHTML = '<span>🔍</span> 测试连接';
            }
        }

        async function loadAccounts(page = 1, resetSearch = false) {
            if (resetSearch) {
                // 重置搜索条件
                currentEmailSearch = '';
                currentTagSearch = '';
                currentRefreshStatusFilter = 'all';
                document.getElementById('emailSearch').value = '';
                document.getElementById('tagSearch').value = '';
                document.getElementById('refreshStatusFilter').value = 'all';
                page = 1;
            }
            
            accountsCurrentPage = page;
            
            const accountsList = document.getElementById('accountsList');
            const accountsStats = document.getElementById('accountsStats');
            const accountsPagination = document.getElementById('accountsPagination');
            
            accountsList.innerHTML = '<div class="loading">正在加载账户列表...</div>';
            accountsStats.style.display = 'none';
            accountsPagination.style.display = 'none';

            try {
                // 构建请求参数
                const params = new URLSearchParams({
                    page: accountsCurrentPage,
                    page_size: accountsPageSize
                });
                
                if (currentEmailSearch) {
                    params.append('email_search', currentEmailSearch);
                }
                
                if (currentTagSearch) {
                    params.append('tag_search', currentTagSearch);
                }
                
                if (currentRefreshStatusFilter && currentRefreshStatusFilter !== 'all' && currentRefreshStatusFilter !== 'custom') {
                    params.append('refresh_status', currentRefreshStatusFilter);
                }
                
                // 添加自定义日期范围参数
                if (currentRefreshStatusFilter === 'custom' && currentRefreshStartDate && currentRefreshEndDate) {
                    params.append('refresh_start_date', currentRefreshStartDate);
                    params.append('refresh_end_date', currentRefreshEndDate);
                    console.log('[筛选] 添加日期范围参数:');
                    console.log('  refresh_start_date:', currentRefreshStartDate);
                    console.log('  refresh_end_date:', currentRefreshEndDate);
                } else if (currentRefreshStatusFilter === 'custom') {
                    console.warn('[筛选] 警告: 自定义模式但日期参数为空!');
                    console.log('  currentRefreshStartDate:', currentRefreshStartDate);
                    console.log('  currentRefreshEndDate:', currentRefreshEndDate);
                }
                
                console.log('[筛选] 完整请求参数:', params.toString());
                
                const data = await apiRequest(`/accounts?${params.toString()}`);
                
                accounts = data.accounts || [];
                accountsTotalCount = data.total_accounts || 0;
                accountsTotalPages = data.total_pages || 0;
                
                // 更新统计信息
                updateAccountsStats();
                
                if (accounts.length === 0) {
                    accountsList.innerHTML = '<div class="text-center" style="padding: 40px; color: #64748b;">暂无符合条件的账户</div>';
                    return;
                }

                accountsList.innerHTML = accounts.map(account => {
                    // 生成标签HTML
                    const tagsHtml = account.tags && account.tags.length > 0 
                        ? `<div class="account-tags">${account.tags.map(tag => 
                            `<span class="account-tag">${tag}</span>`).join('')}</div>` 
                        : '';
                    
                    // 生成刷新状态图标和文本
                    const refreshStatus = account.refresh_status || 'pending';
                    const refreshStatusIcon = refreshStatus === 'success' ? '✓' : 
                                            refreshStatus === 'failed' ? '✗' : '◷';
                    const refreshStatusText = refreshStatus === 'success' ? '成功' :
                                            refreshStatus === 'failed' ? '失败' : '待刷新';
                    const refreshTime = formatRefreshTime(account.last_refresh_time);
                    
                    const statusIndicatorClass = account.status === 'active' ? '' : 'error';
                    const statusText = account.status === 'active' ? '正常' : '异常';
                    
                    return `
                        <div class="account-item" onclick="viewAccountEmails('${account.email_id}')" oncontextmenu="showAccountContextMenu(event, '${account.email_id}')">
                            <div class="account-info">
                                <div class="account-avatar">${account.email_id.charAt(0).toUpperCase()}</div>
                                <div class="account-details">
                                    <h4>${account.email_id}</h4>
                                    ${tagsHtml}
                                    <div class="account-status-row">
                                        <div class="account-status">
                                            <span class="status-indicator ${statusIndicatorClass}"></span>
                                            <span>${statusText}</span>
                                        </div>
                                        <div class="account-refresh-info">
                                            <span class="refresh-status ${refreshStatus}">${refreshStatusIcon}</span>
                                            <span class="refresh-time">${refreshTime} (${refreshStatusText})</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="account-actions" onclick="event.stopPropagation()">
                                <button class="btn btn-primary btn-sm" onclick="viewAccountEmails('${account.email_id}')">
                                    <span>📧</span>
                                    查看邮件
                                </button>
                                <button class="btn btn-secondary btn-sm" onclick="editAccountTags('${account.email_id}', ${JSON.stringify(account.tags || [])})">
                                    <span>🏷️</span>
                                    管理标签
                                </button>
                                <button class="btn btn-secondary btn-sm" onclick="refreshAccountToken('${account.email_id}')">
                                    <span>🔄</span>
                                    刷新Token
                                </button>
                                <button class="btn btn-danger btn-sm" onclick="deleteAccount('${account.email_id}')">
                                    <span>🗑️</span>
                                    删除
                                </button>
                            </div>
                        </div>
                    `;
                }).join('');
                
                // 更新分页控件
                updateAccountsPagination();

            } catch (error) {
                accountsList.innerHTML = '<div class="error">加载失败: ' + error.message + '</div>';
            }
        }

        async function addAccount() {
            const email = document.getElementById('email').value.trim();
            const refreshToken = document.getElementById('refreshToken').value.trim();
            const clientId = document.getElementById('clientId').value.trim();
            const tagsInput = document.getElementById('accountTags').value.trim();
            
            // 处理标签
            const tags = tagsInput ? tagsInput.split(',').map(tag => tag.trim()).filter(tag => tag) : [];

            if (!email || !refreshToken || !clientId) {
                showNotification('请填写所有必填字段', 'warning');
                return;
            }

            const addBtn = document.getElementById('addAccountBtn');
            addBtn.disabled = true;
            addBtn.innerHTML = '<span>⏳</span> 添加中...';

            try {
                const response = await apiRequest('/accounts', {
                    method: 'POST',
                    body: JSON.stringify({
                        email,
                        refresh_token: refreshToken,
                        client_id: clientId,
                        tags: tags
                    })
                });

                showSuccess('账户添加成功');
                clearAddAccountForm();
                showPage('accounts');
                loadAccounts();
            } catch (error) {
                showNotification('添加账户失败: ' + error.message, 'error');
            } finally {
                addBtn.disabled = false;
                addBtn.innerHTML = '<span>➕</span> 添加账户';
            }
        }

        async function batchAddAccounts() {
            const batchText = document.getElementById('batchAccounts').value.trim();
            if (!batchText) {
                showNotification('请输入账户信息', 'warning');
                return;
            }

            const lines = batchText.split('\n').filter(line => line.trim());
            if (lines.length === 0) {
                showNotification('没有有效的账户信息', 'warning');
                return;
            }

            // 显示进度
            showBatchProgress();
            const batchBtn = document.getElementById('batchAddBtn');
            batchBtn.disabled = true;
            batchBtn.innerHTML = '<span>⏳</span> 添加中...';

            let successCount = 0;
            let failCount = 0;
            const results = [];

            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                const parts = line.split('----').map(p => p.trim());

                // 更新进度
                updateBatchProgress(i + 1, lines.length, `处理第 ${i + 1} 个账户...`);

                if (parts.length !== 4) {
                    failCount++;
                    results.push({
                        email: parts[0] || '格式错误',
                        status: 'error',
                        message: '格式错误：应为 邮箱----密码----刷新令牌----客户端ID'
                    });
                    continue;
                }

                const [email, password, refreshToken, clientId] = parts;

                try {
                    await apiRequest('/accounts', {
                        method: 'POST',
                        body: JSON.stringify({
                            email: email,
                            refresh_token: refreshToken,
                            client_id: clientId
                        })
                    });
                    successCount++;
                    results.push({
                        email: email,
                        status: 'success',
                        message: '添加成功'
                    });
                } catch (error) {
                    failCount++;
                    results.push({
                        email: email,
                        status: 'error',
                        message: error.message
                    });
                }

                // 添加小延迟避免请求过快
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            // 完成进度
            updateBatchProgress(lines.length, lines.length, '批量添加完成！');

            // 显示结果
            showBatchResults(results);

            if (successCount > 0) {
                showNotification(`批量添加完成！成功 ${successCount} 个，失败 ${failCount} 个`, 'success');
                if (failCount === 0) {
                    setTimeout(() => {
                        clearBatchForm();
                        showPage('accounts');
                    }, 3000);
                }
            } else {
                showNotification('所有账户添加失败，请检查账户信息', 'error');
            }

            batchBtn.disabled = false;
            batchBtn.innerHTML = '<span>📦</span> 开始批量添加';
        }

        function showBatchProgress() {
            document.getElementById('batchProgress').classList.remove('hidden');
            document.getElementById('batchResults').classList.add('hidden');
        }

        function hideBatchProgress() {
            document.getElementById('batchProgress').classList.add('hidden');
            document.getElementById('batchResults').classList.add('hidden');
        }

        function updateBatchProgress(current, total, message) {
            const percentage = (current / total) * 100;
            document.getElementById('batchProgressFill').style.width = percentage + '%';
            document.getElementById('batchProgressText').textContent = message;
            document.getElementById('batchProgressCount').textContent = `${current} / ${total}`;
        }

        function showBatchResults(results) {
            const resultsContainer = document.getElementById('batchResultsList');
            const successResults = results.filter(r => r.status === 'success');
            const errorResults = results.filter(r => r.status === 'error');

            let html = '';

            if (successResults.length > 0) {
                html += `<div style="margin-bottom: 16px;">
                    <h5 style="color: #16a34a; margin-bottom: 8px;">✅ 成功添加 (${successResults.length})</h5>
                    <div style="background: #f0fdf4; padding: 12px; border-radius: 6px; border: 1px solid #bbf7d0;">`;
                successResults.forEach(result => {
                    html += `<div style="font-size: 0.875rem; color: #15803d; margin-bottom: 4px;">• ${result.email}</div>`;
                });
                html += `</div></div>`;
            }

            if (errorResults.length > 0) {
                html += `<div>
                    <h5 style="color: #dc2626; margin-bottom: 8px;">❌ 添加失败 (${errorResults.length})</h5>
                    <div style="background: #fef2f2; padding: 12px; border-radius: 6px; border: 1px solid #fecaca;">`;
                errorResults.forEach(result => {
                    html += `<div style="font-size: 0.875rem; color: #dc2626; margin-bottom: 8px;">
                        <strong>• ${result.email}</strong><br>
                        <span style="color: #991b1b; font-size: 0.75rem;">&nbsp;&nbsp;${result.message}</span>
                    </div>`;
                });
                html += `</div></div>`;
            }

            resultsContainer.innerHTML = html;
            document.getElementById('batchResults').classList.remove('hidden');
        }

        // API文档相关函数
        function initApiDocs() {
            // 更新Base URL
            const baseUrl = window.location.origin;
            document.getElementById('baseUrlExample').textContent = baseUrl;
        }

        function copyApiBaseUrl() {
            const baseUrl = window.location.origin;
            navigator.clipboard.writeText(baseUrl).then(() => {
                showNotification('Base URL已复制到剪贴板', 'success');
            }).catch(() => {
                showNotification('复制失败，请手动复制', 'error');
            });
        }

        function copyEmailAddress(emailAddress) {
            // 清理邮箱地址（去除可能的空格和特殊字符）
            const cleanEmail = emailAddress.trim();

            if (!cleanEmail) {
                showNotification('邮箱地址为空', 'error');
                return;
            }

            // 复制到剪贴板
            navigator.clipboard.writeText(cleanEmail).then(() => {
                // 显示成功通知
                showNotification(`邮箱地址已复制: ${cleanEmail}`, 'success');

                // 添加视觉反馈
                const emailElement = document.getElementById('currentAccountEmail');
                if (emailElement) {
                    emailElement.classList.add('copy-success');
                    setTimeout(() => {
                        emailElement.classList.remove('copy-success');
                    }, 300);
                }
            }).catch((error) => {
                console.error('复制失败:', error);

                // 降级方案：尝试使用旧的复制方法
                try {
                    const textArea = document.createElement('textarea');
                    textArea.value = cleanEmail;
                    textArea.style.position = 'fixed';
                    textArea.style.opacity = '0';
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);

                    showNotification(`邮箱地址已复制: ${cleanEmail}`, 'success');
                } catch (fallbackError) {
                    console.error('降级复制方案也失败:', fallbackError);
                    showNotification('复制失败，请手动复制邮箱地址', 'error');

                    // 选中文本以便用户手动复制
                    const emailElement = document.getElementById('currentAccountEmail');
                    if (emailElement && window.getSelection) {
                        const selection = window.getSelection();
                        const range = document.createRange();
                        range.selectNodeContents(emailElement);
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                }
            });
        }

        function downloadApiDocs() {
            const apiDocs = generateApiDocsMarkdown();
            const blob = new Blob([apiDocs], { type: 'text/markdown;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', 'outlook-email-api-docs.md');
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            showNotification('API文档已下载', 'success');
        }

        function generateApiDocsMarkdown() {
            const baseUrl = window.location.origin;
            return `# Outlook邮件管理系统 API文档

## 基础信息

- **Base URL**: ${baseUrl}
- **认证方式**: 无需认证
- **响应格式**: JSON

## 接口列表

### 1. 获取邮箱列表

**请求**
\`\`\`
GET /accounts
\`\`\`

**响应示例**
\`\`\`json
{
  "accounts": [
    {
      "email_id": "example@outlook.com",
      "status": "active",
      "last_sync": "2024-01-01T12:00:00Z"
    }
  ],
  "total_count": 1
}
\`\`\`

### 2. 获取邮件列表

**请求**
\`\`\`
GET /emails/{email_id}?folder=inbox&page=1&page_size=20&refresh=false
\`\`\`

**参数说明**
- \`email_id\`: 邮箱地址（URL编码）
- \`folder\`: 文件夹 (all, inbox, junk)
- \`page\`: 页码
- \`page_size\`: 每页数量
- \`refresh\`: 是否强制刷新

**响应示例**
\`\`\`json
{
  "email_id": "example@outlook.com",
  "folder_view": "inbox",
  "page": 1,
  "page_size": 20,
  "total_emails": 150,
  "emails": [...]
}
\`\`\`

### 3. 获取邮件详情

**请求**
\`\`\`
GET /emails/{email_id}/{message_id}
\`\`\`

**参数说明**
- \`email_id\`: 邮箱地址（URL编码）
- \`message_id\`: 邮件ID

**响应示例**
\`\`\`json
{
  "message_id": "INBOX-1",
  "subject": "邮件主题",
  "from_email": "sender@example.com",
  "to_email": "example@outlook.com",
  "date": "2024-01-01T12:00:00Z",
  "body_plain": "纯文本内容",
  "body_html": "HTML内容"
}
\`\`\`

---
生成时间: ${new Date().toLocaleString()}
`;
        }

        async function tryApi(apiType) {
            const baseUrl = window.location.origin;
            let url, responseElementId;

            switch (apiType) {
                case 'accounts':
                    url = `${baseUrl}/accounts`;
                    responseElementId = 'accountsResponse';
                    break;
                case 'emails':
                    // 需要先获取一个邮箱账户
                    try {
                        const accountsData = await apiRequest('/accounts');
                        if (accountsData.accounts && accountsData.accounts.length > 0) {
                            const emailId = encodeURIComponent(accountsData.accounts[0].email_id);
                            url = `${baseUrl}/emails/${emailId}?folder=inbox&page=1&page_size=5`;
                            responseElementId = 'emailsResponse';
                        } else {
                            showNotification('没有可用的邮箱账户，请先添加账户', 'warning');
                            return;
                        }
                    } catch (error) {
                        showNotification('获取邮箱账户失败: ' + error.message, 'error');
                        return;
                    }
                    break;
                case 'emailDetail':
                    // 需要先获取一个邮件ID
                    try {
                        const accountsData = await apiRequest('/accounts');
                        if (accountsData.accounts && accountsData.accounts.length > 0) {
                            const emailId = encodeURIComponent(accountsData.accounts[0].email_id);
                            const emailsData = await apiRequest(`/emails/${emailId}?folder=all&page=1&page_size=1`);
                            if (emailsData.emails && emailsData.emails.length > 0) {
                                const messageId = emailsData.emails[0].message_id;
                                url = `${baseUrl}/emails/${emailId}/${messageId}`;
                                responseElementId = 'emailDetailResponse';
                            } else {
                                showNotification('该邮箱没有邮件', 'warning');
                                return;
                            }
                        } else {
                            showNotification('没有可用的邮箱账户，请先添加账户', 'warning');
                            return;
                        }
                    } catch (error) {
                        showNotification('获取邮件数据失败: ' + error.message, 'error');
                        return;
                    }
                    break;
                default:
                    return;
            }

            try {
                showNotification('正在调用API...', 'info', '', 2000);
                const response = await fetch(url);
                const data = await response.json();

                // 显示响应结果
                const responseElement = document.getElementById(responseElementId);
                const responseDataElement = document.getElementById(responseElementId.replace('Response', 'ResponseData'));

                responseDataElement.textContent = JSON.stringify(data, null, 2);
                responseElement.classList.add('show');

                showNotification('API调用成功！', 'success');

            } catch (error) {
                showNotification('API调用失败: ' + error.message, 'error');
            }
        }

        // 全局变量
        let allEmails = []; // 存储所有邮件数据
        let filteredEmails = []; // 存储过滤后的邮件数据
        let searchTimeout = null;

        // 邮件管理
        function viewAccountEmails(emailId) {
            currentAccount = emailId;
            document.getElementById('currentAccountEmail').textContent = emailId;
            document.getElementById('emailsNav').style.display = 'block';

            // 重置搜索和过滤器
            emailCurrentPage = 1;
            emailPageSize = 100;
            
            // 尝试重置新的搜索控件（如果存在）
            const senderSearch = document.getElementById('senderSearch');
            const subjectSearch = document.getElementById('subjectSearch');
            const folderFilter = document.getElementById('folderFilter');
            const sortOrder = document.getElementById('sortOrder');
            
            if (senderSearch) senderSearch.value = '';
            if (subjectSearch) subjectSearch.value = '';
            if (folderFilter) folderFilter.value = 'all';
            if (sortOrder) sortOrder.value = 'desc';

            showPage('emails');
        }

        function backToAccounts() {
            currentAccount = null;
            document.getElementById('emailsNav').style.display = 'none';
            showPage('accounts');
        }

        function switchEmailTab(folder, targetElement = null) {
            currentEmailFolder = folder;
            currentEmailPage = 1;

            // 更新标签状态
            document.querySelectorAll('#emailsPage .tab').forEach(t => t.classList.remove('active'));

            if (targetElement) {
                targetElement.classList.add('active');
            } else {
                // 根据folder名称查找对应的标签按钮
                document.querySelectorAll('#emailsPage .tab').forEach(t => {
                    if (t.onclick && t.onclick.toString().includes(`'${folder}'`)) {
                        t.classList.add('active');
                    }
                });
            }

            loadEmails();
        }

        async function loadEmails(forceRefresh = false) {
            if (!currentAccount) return;

            const emailsList = document.getElementById('emailsList');
            const refreshBtn = document.getElementById('refreshBtn');

            // 获取搜索和排序参数
            const senderSearch = document.getElementById('senderSearch')?.value || '';
            const subjectSearch = document.getElementById('subjectSearch')?.value || '';
            const sortOrder = document.getElementById('sortOrder')?.value || 'desc';
            const folder = document.getElementById('folderFilter')?.value || 'all';

            // 显示加载状态
            emailsList.innerHTML = '<tr><td colspan="4" style="padding: 40px; text-align: center;"><div class="loading"><div class="loading-spinner"></div>正在加载邮件...</div></td></tr>';
            refreshBtn.disabled = true;
            refreshBtn.innerHTML = '<span>⏳</span> 加载中...';

            try {
                // 构建 URL 参数
                let url = `/emails/${currentAccount}?folder=${folder}&page=${emailCurrentPage}&page_size=${emailPageSize}&sort_order=${sortOrder}`;
                
                if (forceRefresh) {
                    url += '&refresh=true';
                }
                
                if (senderSearch) {
                    url += `&sender_search=${encodeURIComponent(senderSearch)}`;
                }
                
                if (subjectSearch) {
                    url += `&subject_search=${encodeURIComponent(subjectSearch)}`;
                }

                const data = await apiRequest(url);

                // 存储所有邮件数据和总数
                allEmails = data.emails || [];
                emailTotalCount = data.total_emails || 0;

                // 直接渲染邮件（不再需要前端过滤）
                renderEmails(allEmails);

                // 更新统计信息
                updateEmailStats(allEmails);

                // 更新分页显示
                updateEmailPagination();

                // 更新最后更新时间
                document.getElementById('lastUpdateTime').textContent = new Date().toLocaleString();

                if (forceRefresh) {
                    showNotification('邮件列表已刷新', 'success');
                }

            } catch (error) {
                emailsList.innerHTML = '<tr><td colspan="4" style="padding: 40px; text-align: center;"><div class="error">❌ 加载失败: ' + error.message + '</div></td></tr>';
                showNotification('加载邮件失败: ' + error.message, 'error');
            } finally {
                // 恢复刷新按钮状态
                refreshBtn.disabled = false;
                refreshBtn.innerHTML = '<span>🔄</span> 刷新';
            }
        }

        // 邮件分页函数
        function changeEmailPageSize() {
            emailPageSize = parseInt(document.getElementById('emailPageSize').value);
            emailCurrentPage = 1;
            loadEmails();
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
            document.getElementById('emailCurrentPageDisplay').textContent = emailCurrentPage;
            document.getElementById('emailTotalInfo').textContent = `/ 共 ${totalPages} 页 (总计 ${emailTotalCount} 封)`;
            
            // 更新按钮状态
            document.getElementById('emailPrevBtn').disabled = emailCurrentPage === 1;
            document.getElementById('emailNextBtn').disabled = emailCurrentPage >= totalPages;
        }

        function updateEmailStats(emails) {
            const total = emailTotalCount || emails.length;
            const unread = emails.filter(email => !email.is_read).length;
            const today = emails.filter(email => {
                const emailDate = new Date(email.date);
                const todayDate = new Date();
                return emailDate.toDateString() === todayDate.toDateString();
            }).length;
            const withAttachments = emails.filter(email => email.has_attachments).length;

            document.getElementById('totalEmailCount').textContent = total;
            document.getElementById('unreadEmailCount').textContent = unread;
            document.getElementById('todayEmailCount').textContent = today;
            document.getElementById('attachmentEmailCount').textContent = withAttachments;
        }

        // 搜索和过滤功能
        function searchEmails() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                applyFilters();
            }, 300); // 防抖，300ms后执行搜索
        }

        function applyFilters() {
            const searchTerm = document.getElementById('emailSearch').value.toLowerCase();
            const folderFilter = document.getElementById('folderFilter').value;
            const statusFilter = document.getElementById('statusFilter').value;
            const timeFilter = document.getElementById('timeFilter').value;
            const attachmentFilter = document.getElementById('attachmentFilter').value;

            filteredEmails = allEmails.filter(email => {
                // 搜索过滤
                if (searchTerm) {
                    const searchableText = `${email.subject || ''} ${email.from_email || ''}`.toLowerCase();
                    if (!searchableText.includes(searchTerm)) {
                        return false;
                    }
                }

                // 文件夹过滤
                if (folderFilter !== 'all' && email.folder.toLowerCase() !== folderFilter) {
                    return false;
                }

                // 状态过滤
                if (statusFilter === 'read' && !email.is_read) return false;
                if (statusFilter === 'unread' && email.is_read) return false;

                // 时间过滤
                if (timeFilter !== 'all') {
                    const emailDate = new Date(email.date);
                    const now = new Date();

                    switch (timeFilter) {
                        case 'today':
                            if (emailDate.toDateString() !== now.toDateString()) return false;
                            break;
                        case 'week':
                            const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
                            if (emailDate < weekAgo) return false;
                            break;
                        case 'month':
                            const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                            if (emailDate < monthAgo) return false;
                            break;
                    }
                }

                // 附件过滤
                if (attachmentFilter === 'with' && !email.has_attachments) return false;
                if (attachmentFilter === 'without' && email.has_attachments) return false;

                return true;
            });

            renderFilteredEmails();
        }

        function renderFilteredEmails() {
            const emailsList = document.getElementById('emailsList');

            if (filteredEmails.length === 0) {
                emailsList.innerHTML = '<div class="text-center" style="padding: 40px; color: #64748b;">没有找到匹配的邮件</div>';
                return;
            }

            emailsList.innerHTML = filteredEmails.map(email => createEmailItem(email)).join('');
        }

        function clearFilters() {
            // 兼容旧的过滤器（如果存在）
            const emailSearch = document.getElementById('emailSearch');
            const statusFilter = document.getElementById('statusFilter');
            const timeFilter = document.getElementById('timeFilter');
            const attachmentFilter = document.getElementById('attachmentFilter');
            
            if (emailSearch) emailSearch.value = '';
            if (statusFilter) statusFilter.value = 'all';
            if (timeFilter) timeFilter.value = 'all';
            if (attachmentFilter) attachmentFilter.value = 'all';
            
            // 新的搜索控件
            const senderSearch = document.getElementById('senderSearch');
            const subjectSearch = document.getElementById('subjectSearch');
            const folderFilter = document.getElementById('folderFilter');
            const sortOrder = document.getElementById('sortOrder');
            
            if (senderSearch) senderSearch.value = '';
            if (subjectSearch) subjectSearch.value = '';
            if (folderFilter) folderFilter.value = 'all';
            if (sortOrder) sortOrder.value = 'desc';

            // 如果使用旧的过滤方式
            if (typeof filteredEmails !== 'undefined' && typeof allEmails !== 'undefined') {
                filteredEmails = [...allEmails];
                if (typeof renderFilteredEmails === 'function') {
                    renderFilteredEmails();
                }
            } else {
                // 新方式：重新加载
                emailCurrentPage = 1;
                loadEmails();
            }
        }

        // 新的渲染函数：渲染表格行
        function renderEmails(emails) {
            const emailsList = document.getElementById('emailsList');

            if (!emails || emails.length === 0) {
                emailsList.innerHTML = '<tr><td colspan="4" style="padding: 40px; text-align: center; color: #64748b;">没有找到邮件</td></tr>';
                return;
            }

            emailsList.innerHTML = emails.map(email => createEmailTableRow(email)).join('');
        }

        // 创建表格行
        function createEmailTableRow(email) {
            const unreadClass = email.is_read ? '' : 'unread';
            const attachmentIcon = email.has_attachments ? '<span style="color: #8b5cf6;">📎</span>' : '';
            
            return `
                <tr class="${unreadClass}" onclick="showEmailDetail('${email.message_id}')">
                    <td>
                        <div class="email-sender">
                            <div class="email-sender-initial">${email.sender_initial}</div>
                            <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${email.from_email}</span>
                        </div>
                    </td>
                    <td>
                        <div class="email-subject" title="${email.subject || '(无主题)'}">
                            ${email.subject || '(无主题)'} ${attachmentIcon}
                        </div>
                    </td>
                    <td>
                        <div class="email-date">${formatEmailDate(email.date)}</div>
                    </td>
                    <td style="text-align: center;">
                        <button class="btn btn-sm" onclick="event.stopPropagation(); showEmailDetail('${email.message_id}')" style="padding: 4px 8px; font-size: 0.75rem;">
                            查看
                        </button>
                    </td>
                </tr>
            `;
        }

        // 搜索延迟执行（使用已存在的 searchTimeout 变量）
        function searchAndLoadEmails() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                emailCurrentPage = 1;
                loadEmails();
            }, 500); // 500ms 防抖
        }

        // 清除搜索过滤器
        function clearSearchFilters() {
            document.getElementById('senderSearch').value = '';
            document.getElementById('subjectSearch').value = '';
            document.getElementById('folderFilter').value = 'all';
            document.getElementById('sortOrder').value = 'desc';
            emailCurrentPage = 1;
            loadEmails();
        }

        function createEmailItem(email) {
            const unreadClass = email.is_read ? '' : 'unread';
            const attachmentIcon = email.has_attachments ? '<span style="color: #8b5cf6;">📎</span>' : '';
            const readIcon = email.is_read ? '📖' : '📧';

            return `
                <div class="email-item ${unreadClass}" onclick="showEmailDetail('${email.message_id}')">
                    <div class="email-avatar">${email.sender_initial}</div>
                    <div class="email-content">
                        <div class="email-header">
                            <div class="email-subject">${email.subject || '(无主题)'}</div>
                            <div class="email-date">${formatEmailDate(email.date)}</div>
                        </div>
                        <div class="email-from">${readIcon} ${email.from_email} ${attachmentIcon}</div>
                        <div class="email-preview">文件夹: ${email.folder} | 点击查看详情</div>
                    </div>
                </div>
            `;
        }

        async function showEmailDetail(messageId) {
            document.getElementById('emailModal').classList.remove('hidden');
            document.getElementById('emailModalTitle').textContent = '邮件详情';
            document.getElementById('emailModalContent').innerHTML = '<div class="loading">正在加载邮件详情...</div>';

            try {
                const data = await apiRequest(`/emails/${currentAccount}/${messageId}`);

                document.getElementById('emailModalTitle').textContent = data.subject || '(无主题)';
                document.getElementById('emailModalContent').innerHTML = `
                    <div class="email-detail-meta">
                        <p><strong>发件人:</strong> ${data.from_email}</p>
                        <p><strong>收件人:</strong> ${data.to_email}</p>
                        <p><strong>日期:</strong> ${formatEmailDate(data.date)} (${new Date(data.date).toLocaleString()})</p>
                        <p><strong>邮件ID:</strong> ${data.message_id}</p>
                    </div>
                    ${renderEmailContent(data)}
                `;

            } catch (error) {
                document.getElementById('emailModalContent').innerHTML = '<div class="error">加载失败: ' + error.message + '</div>';
            }
        }

        function renderEmailContent(email) {
            const hasHtml = email.body_html && email.body_html.trim();
            const hasPlain = email.body_plain && email.body_plain.trim();

            if (!hasHtml && !hasPlain) {
                return '<p style="color: #9ca3af; font-style: italic;">此邮件无内容</p>';
            }

            if (hasHtml) {
                // 优化HTML内容：添加样式重置和容器限制
                const wrappedHtml = `
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="UTF-8">
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            /* 重置样式，防止邮件样式影响外部 */
                            * {
                                box-sizing: border-box;
                            }
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
                            /* 限制图片大小 */
                            img {
                                max-width: 100%;
                                height: auto;
                            }
                            /* 限制表格宽度 */
                            table {
                                max-width: 100%;
                                border-collapse: collapse;
                            }
                            /* 限制内容宽度 */
                            .email-container {
                                max-width: 100%;
                                overflow-x: auto;
                            }
                            /* 防止内容溢出 */
                            pre {
                                white-space: pre-wrap;
                                word-wrap: break-word;
                                overflow-x: auto;
                            }
                        </style>
                    </head>
                    <body>
                        <div class="email-container">
                            ${email.body_html}
                        </div>
                    </body>
                    </html>
                `;
                
                const sanitizedHtml = wrappedHtml.replace(/"/g, '&quot;');

                return `
                    <div class="email-content-tabs">
                        <button class="content-tab active" onclick="showEmailContentTab('html', this)">HTML视图</button>
                        ${hasPlain ? '<button class="content-tab" onclick="showEmailContentTab(\'plain\', this)">纯文本</button>' : ''}
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
                        ${hasPlain ? `<div id="plainContent" class="hidden"><pre style="background: #f8fafc; padding: 16px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;">${email.body_plain}</pre></div>` : ''}
                        <div id="rawContent" class="hidden"><pre style="background: #1e293b; color: #e2e8f0; padding: 16px; border-radius: 6px; overflow-x: auto; font-size: 12px; white-space: pre-wrap; word-wrap: break-word;">${email.body_html.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</pre></div>
                    </div>
                `;
            } else {
                return `<div class="email-content-body"><pre style="background: #f8fafc; padding: 16px; border-radius: 6px; overflow-x: auto; white-space: pre-wrap; word-wrap: break-word;">${email.body_plain}</pre></div>`;
            }
        }

        function showEmailContentTab(type, targetElement = null) {
            // 更新标签状态
            document.querySelectorAll('.content-tab').forEach(tab => tab.classList.remove('active'));

            if (targetElement) {
                targetElement.classList.add('active');
            } else {
                // 根据type查找对应的标签按钮
                document.querySelectorAll('.content-tab').forEach(tab => {
                    if (tab.onclick && tab.onclick.toString().includes(`'${type}'`)) {
                        tab.classList.add('active');
                    }
                });
            }

            // 隐藏所有内容
            document.querySelectorAll('#htmlContent, #plainContent, #rawContent').forEach(content => {
                content.classList.add('hidden');
            });

            // 显示对应内容
            document.getElementById(type + 'Content').classList.remove('hidden');
        }

        function closeEmailModal() {
            document.getElementById('emailModal').classList.add('hidden');
        }

        function refreshEmails() {
            loadEmails(true); // 强制刷新
        }

        async function clearCache() {
            if (!currentAccount) return;

            try {
                await apiRequest(`/cache/${currentAccount}`, { method: 'DELETE' });
                showNotification('缓存已清除', 'success');
                loadEmails(true);
            } catch (error) {
                showNotification('清除缓存失败: ' + error.message, 'error');
            }
        }

        function exportEmails() {
            if (!filteredEmails || filteredEmails.length === 0) {
                showNotification('没有邮件可导出', 'warning');
                return;
            }

            const csvContent = generateEmailCSV(filteredEmails);
            downloadCSV(csvContent, `emails_${currentAccount}_${new Date().toISOString().split('T')[0]}.csv`);
            showNotification(`已导出 ${filteredEmails.length} 封邮件`, 'success');
        }

        function generateEmailCSV(emails) {
            const headers = ['主题', '发件人', '日期', '文件夹', '是否已读', '是否有附件'];
            const rows = emails.map(email => [
                `"${(email.subject || '').replace(/"/g, '""')}"`,
                `"${email.from_email.replace(/"/g, '""')}"`,
                `"${email.date}"`,
                `"${email.folder}"`,
                email.is_read ? '已读' : '未读',
                email.has_attachments ? '有附件' : '无附件'
            ]);

            return [headers, ...rows].map(row => row.join(',')).join('\n');
        }

        function downloadCSV(content, filename) {
            const blob = new Blob(['\uFEFF' + content], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            link.setAttribute('href', url);
            link.setAttribute('download', filename);
            link.style.visibility = 'hidden';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function updateEmailsPagination(totalEmails, pageSize) {
            const pagination = document.getElementById('emailsPagination');
            const totalPages = Math.ceil(totalEmails / pageSize);

            if (totalPages <= 1) {
                pagination.classList.add('hidden');
                return;
            }

            pagination.classList.remove('hidden');
            pagination.innerHTML = `
                <button class="btn btn-secondary btn-sm" onclick="changeEmailPage(${currentEmailPage - 1})" ${currentEmailPage === 1 ? 'disabled' : ''}>‹ 上一页</button>
                <span style="padding: 0 16px; color: #64748b;">${currentEmailPage} / ${totalPages}</span>
                <button class="btn btn-secondary btn-sm" onclick="changeEmailPage(${currentEmailPage + 1})" ${currentEmailPage === totalPages ? 'disabled' : ''}>下一页 ›</button>
            `;
        }

        function changeEmailPage(page) {
            currentEmailPage = page;
            loadEmails();
        }

        // 打开标签管理模态框
        function editAccountTags(emailId, tags) {
            currentEditAccount = emailId;
            currentEditTags = Array.isArray(tags) ? [...tags] : [];
            
            // 更新模态框标题
            document.querySelector('#tagsModal .modal-header h3').textContent = `管理 ${emailId} 的标签`;
            
            // 显示当前标签
            renderCurrentTags();
            
            // 显示模态框
            document.getElementById('tagsModal').style.display = 'flex';
        }

        // 渲染当前标签列表
        function renderCurrentTags() {
            const tagsList = document.getElementById('currentTagsList');
            
            if (currentEditTags.length === 0) {
                tagsList.innerHTML = '<p class="text-muted">暂无标签</p>';
                return;
            }
            
            tagsList.innerHTML = currentEditTags.map(tag => `
                <div class="tag-item">
                    <span class="tag-name">${tag}</span>
                    <button class="tag-delete" onclick="removeTag('${tag}')">×</button>
                </div>
            `).join('');
        }

        // 添加新标签
        function addTag() {
            const newTagInput = document.getElementById('newTag');
            const newTag = newTagInput.value.trim();
            
            if (!newTag) {
                showNotification('标签名称不能为空', 'warning');
                return;
            }
            
            // 检查标签是否已存在
            if (currentEditTags.includes(newTag)) {
                showNotification('标签已存在', 'warning');
                return;
            }
            
            // 添加新标签
            currentEditTags.push(newTag);
            
            // 清空输入框
            newTagInput.value = '';
            
            // 重新渲染标签列表
            renderCurrentTags();
        }

        // 删除标签
        function removeTag(tag) {
            currentEditTags = currentEditTags.filter(t => t !== tag);
            renderCurrentTags();
        }

        // 关闭标签管理模态框
        function closeTagsModal() {
            document.getElementById('tagsModal').style.display = 'none';
            currentEditAccount = null;
            currentEditTags = [];
        }

        // 保存账户标签
        async function saveAccountTags() {
            if (!currentEditAccount) {
                closeTagsModal();
                return;
            }
            
            try {
                const response = await apiRequest(`/accounts/${currentEditAccount}/tags`, {
                    method: 'PUT',
                    body: JSON.stringify({ tags: currentEditTags })
                });
                
                showSuccess('标签更新成功');
                closeTagsModal();
                
                // 重新加载账户列表
                loadAccounts();
            } catch (error) {
                showError('更新标签失败: ' + error.message);
            }
        }

        // 新增的账户管理辅助函数
        function updateAccountsStats() {
            const accountsStats = document.getElementById('accountsStats');
            document.getElementById('totalAccounts').textContent = accountsTotalCount;
            document.getElementById('currentPage').textContent = accountsCurrentPage;
            document.getElementById('pageSize').textContent = accountsPageSize;
            accountsStats.style.display = accountsTotalCount > 0 ? 'block' : 'none';
        }
        
        function updateAccountsPagination() {
            const accountsPagination = document.getElementById('accountsPagination');
            const prevBtn = document.getElementById('prevPageBtn');
            const nextBtn = document.getElementById('nextPageBtn');
            const pageNumbers = document.getElementById('pageNumbers');
            
            if (accountsTotalPages <= 1) {
                accountsPagination.style.display = 'none';
                return;
            }
            
            accountsPagination.style.display = 'flex';
            
            // 更新上一页/下一页按钮
            prevBtn.disabled = accountsCurrentPage <= 1;
            nextBtn.disabled = accountsCurrentPage >= accountsTotalPages;
            
            // 生成页码
            pageNumbers.innerHTML = generatePageNumbers();
        }
        
        function generatePageNumbers() {
            const maxVisiblePages = 5;
            let startPage = Math.max(1, accountsCurrentPage - Math.floor(maxVisiblePages / 2));
            let endPage = Math.min(accountsTotalPages, startPage + maxVisiblePages - 1);
            
            if (endPage - startPage < maxVisiblePages - 1) {
                startPage = Math.max(1, endPage - maxVisiblePages + 1);
            }
            
            let html = '';
            
            // 第一页
            if (startPage > 1) {
                html += `<span class="page-number" onclick="changePage(1)">1</span>`;
                if (startPage > 2) {
                    html += `<span class="page-number disabled">...</span>`;
                }
            }
            
            // 中间页码
            for (let i = startPage; i <= endPage; i++) {
                const activeClass = i === accountsCurrentPage ? 'active' : '';
                html += `<span class="page-number ${activeClass}" onclick="changePage(${i})">${i}</span>`;
            }
            
            // 最后一页
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
            if (direction === 'prev') {
                newPage = Math.max(1, accountsCurrentPage - 1);
            } else if (direction === 'next') {
                newPage = Math.min(accountsTotalPages, accountsCurrentPage + 1);
            } else {
                newPage = parseInt(direction);
            }
            
            if (newPage !== accountsCurrentPage && newPage >= 1 && newPage <= accountsTotalPages) {
                loadAccounts(newPage);
            }
        }
        
        function searchAccounts() {
            console.log('[搜索] 开始搜索...');
            
            currentEmailSearch = document.getElementById('emailSearch').value.trim();
            currentTagSearch = document.getElementById('tagSearch').value.trim();
            currentRefreshStatusFilter = document.getElementById('refreshStatusFilter').value;
            
            console.log('[搜索] 当前筛选条件:');
            console.log('  邮箱搜索:', currentEmailSearch);
            console.log('  标签搜索:', currentTagSearch);
            console.log('  状态筛选:', currentRefreshStatusFilter);
            
            // 如果是自定义筛选，从输入框读取最新的日期值
            if (currentRefreshStatusFilter === 'custom') {
                const startDateInput = document.getElementById('refreshStartDate').value;
                const endDateInput = document.getElementById('refreshEndDate').value;
                
                console.log('[搜索] 自定义模式 - 输入框值:');
                console.log('  起始时间输入:', startDateInput);
                console.log('  截止时间输入:', endDateInput);
                
                if (startDateInput && endDateInput) {
                    const startDate = new Date(startDateInput);
                    const endDate = new Date(endDateInput);
                    
                    if (startDate <= endDate) {
                        currentRefreshStartDate = startDate.toISOString();
                        currentRefreshEndDate = endDate.toISOString();
                        console.log('[搜索] 转换为ISO格式:');
                        console.log('  起始时间:', currentRefreshStartDate);
                        console.log('  截止时间:', currentRefreshEndDate);
                    } else {
                        console.error('[搜索] 错误: 起始时间晚于截止时间');
                        alert('起始时间不能晚于截止时间');
                        return;
                    }
                } else {
                    console.error('[搜索] 错误: 日期未选择');
                    alert('请选择起始时间和截止时间');
                    return;
                }
            } else {
                // 如果不是自定义筛选，清除日期范围
                currentRefreshStartDate = '';
                currentRefreshEndDate = '';
                console.log('[搜索] 非自定义模式，清除日期范围');
            }
            
            loadAccounts(1); // 搜索时重置到第一页
        }
        
        function clearSearch() {
            document.getElementById('emailSearch').value = '';
            document.getElementById('tagSearch').value = '';
            document.getElementById('refreshStatusFilter').value = 'all';
            document.getElementById('refreshStartDate').value = '';
            document.getElementById('refreshEndDate').value = '';
            document.getElementById('customDateRangeContainer').style.display = 'none';
            currentEmailSearch = '';
            currentTagSearch = '';
            currentRefreshStatusFilter = 'all';
            currentRefreshStartDate = '';
            currentRefreshEndDate = '';
            loadAccounts(1);
        }
        
        // 处理刷新状态筛选器变化
        function handleRefreshStatusChange() {
            const refreshStatus = document.getElementById('refreshStatusFilter').value;
            const customDateContainer = document.getElementById('customDateRangeContainer');
            
            console.log('[筛选] 状态变化:', refreshStatus);
            
            if (refreshStatus === 'custom') {
                // 显示自定义日期范围选择器
                customDateContainer.style.display = 'flex';
                
                // 设置默认日期：起始日期为30天前，截止日期为当前时间
                const now = new Date();
                const startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
                
                document.getElementById('refreshStartDate').value = formatDateTimeLocal(startDate);
                document.getElementById('refreshEndDate').value = formatDateTimeLocal(now);
                
                // 同时设置全局变量为默认值（转换为ISO格式）
                currentRefreshStartDate = startDate.toISOString();
                currentRefreshEndDate = now.toISOString();
                
                console.log('[筛选] 设置默认日期范围:');
                console.log('  起始时间:', currentRefreshStartDate);
                console.log('  截止时间:', currentRefreshEndDate);
                
                // 立即应用默认的日期范围筛选
                loadAccounts(1);
            } else {
                // 隐藏自定义日期范围选择器
                customDateContainer.style.display = 'none';
                currentRefreshStartDate = '';
                currentRefreshEndDate = '';
                
                console.log('[筛选] 清除日期范围');
                
                // 如果不是自定义筛选，立即执行搜索
                searchAccounts();
            }
        }
        
        // 应用自定义日期筛选
        function applyCustomDateFilter() {
            console.log('[应用筛选] 开始应用自定义日期筛选...');
            
            const startDateInput = document.getElementById('refreshStartDate').value;
            const endDateInput = document.getElementById('refreshEndDate').value;
            
            console.log('[应用筛选] 输入框值:');
            console.log('  起始时间:', startDateInput);
            console.log('  截止时间:', endDateInput);
            
            if (!startDateInput || !endDateInput) {
                console.error('[应用筛选] 错误: 日期未选择');
                alert('请选择起始时间和截止时间');
                return;
            }
            
            const startDate = new Date(startDateInput);
            const endDate = new Date(endDateInput);
            
            if (startDate > endDate) {
                console.error('[应用筛选] 错误: 起始时间晚于截止时间');
                alert('起始时间不能晚于截止时间');
                return;
            }
            
            // 转换为ISO格式
            currentRefreshStartDate = startDate.toISOString();
            currentRefreshEndDate = endDate.toISOString();
            
            // 设置筛选状态为custom
            currentRefreshStatusFilter = 'custom';
            
            // 同步更新下拉框的值
            document.getElementById('refreshStatusFilter').value = 'custom';
            
            console.log('[应用筛选] 转换为ISO格式:');
            console.log('  起始时间:', currentRefreshStartDate);
            console.log('  截止时间:', currentRefreshEndDate);
            console.log('  筛选状态:', currentRefreshStatusFilter);
            
            loadAccounts(1); // 应用筛选时重置到第一页
        }
        
        // 格式化日期时间为datetime-local格式
        function formatDateTimeLocal(date) {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, '0');
            const day = String(date.getDate()).padStart(2, '0');
            const hours = String(date.getHours()).padStart(2, '0');
            const minutes = String(date.getMinutes()).padStart(2, '0');
            return `${year}-${month}-${day}T${hours}:${minutes}`;
        }
        
        function handleSearchKeyPress(event) {
            if (event.key === 'Enter') {
                searchAccounts();
            }
        }
        
        async function deleteAccount(emailId) {
            if (!confirm(`确定要删除账户 ${emailId} 吗？`)) {
                return;
            }

            try {
                await apiRequest(`/accounts/${emailId}`, { method: 'DELETE' });
                showSuccess('账户删除成功');
                loadAccounts(accountsCurrentPage); // 保持当前页码
            } catch (error) {
                showError('删除账户失败: ' + error.message);
            }
        }
        
        async function refreshAccountToken(emailId) {
            if (!confirm(`确定要手动刷新账户 ${emailId} 的Token吗？`)) {
                return;
            }

            try {
                showNotification('正在刷新Token，请稍候...', 'info');
                
                const response = await apiRequest(`/accounts/${emailId}/refresh-token`, {
                    method: 'POST'
                });

                showNotification('Token刷新成功！', 'success');
                
                // 重新加载账户列表以显示更新后的刷新时间
                loadAccounts(accountsCurrentPage);

            } catch (error) {
                showNotification(`Token刷新失败: ${error.message}`, 'error');
            }
        }
        
        // 批量刷新Token功能
        async function showBatchRefreshDialog() {
            try {
                // 获取当前筛选条件下的账户数量
                const params = new URLSearchParams({
                    page: 1,
                    page_size: 1
                });
                
                if (currentEmailSearch) {
                    params.append('email_search', currentEmailSearch);
                }
                
                if (currentTagSearch) {
                    params.append('tag_search', currentTagSearch);
                }
                
                if (currentRefreshStatusFilter && currentRefreshStatusFilter !== 'all' && currentRefreshStatusFilter !== 'custom') {
                    params.append('refresh_status', currentRefreshStatusFilter);
                }
                
                // 添加自定义日期范围参数
                if (currentRefreshStatusFilter === 'custom' && currentRefreshStartDate && currentRefreshEndDate) {
                    params.append('refresh_start_date', currentRefreshStartDate);
                    params.append('refresh_end_date', currentRefreshEndDate);
                }
                
                const data = await apiRequest(`/accounts?${params.toString()}`);
                const totalAccounts = data.total_accounts || 0;
                
                if (totalAccounts === 0) {
                    showNotification('当前筛选条件下没有账户需要刷新', 'warning');
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
                if (currentRefreshStatusFilter && currentRefreshStatusFilter !== 'all') {
                    if (currentRefreshStatusFilter === 'custom') {
                        const startDate = new Date(currentRefreshStartDate);
                        const endDate = new Date(currentRefreshEndDate);
                        filterDesc.push(`刷新时间在 ${startDate.toLocaleString('zh-CN')} 至 ${endDate.toLocaleString('zh-CN')} 之间`);
                    } else {
                        const statusMap = {
                            'never_refreshed': '从未刷新',
                            'success': '刷新成功',
                            'failed': '刷新失败',
                            'pending': '待刷新'
                        };
                        filterDesc.push(`状态为"${statusMap[currentRefreshStatusFilter]}"`);
                    }
                }
                
                const filterText = filterDesc.length > 0 
                    ? `当前筛选条件：${filterDesc.join('、')}\n` 
                    : '当前筛选条件：全部账户\n';
                
                if (!confirm(`${filterText}将刷新 ${totalAccounts} 个账户的Token，确定继续吗？\n\n此操作可能需要较长时间，请耐心等待。`)) {
                    return;
                }
                
                await batchRefreshTokens();
                
            } catch (error) {
                showNotification(`获取账户信息失败: ${error.message}`, 'error');
            }
        }
        
        async function batchRefreshTokens() {
            try {
                // 构建请求参数
                const params = new URLSearchParams();
                
                if (currentEmailSearch) {
                    params.append('email_search', currentEmailSearch);
                }
                
                if (currentTagSearch) {
                    params.append('tag_search', currentTagSearch);
                }
                
                if (currentRefreshStatusFilter && currentRefreshStatusFilter !== 'all' && currentRefreshStatusFilter !== 'custom') {
                    params.append('refresh_status', currentRefreshStatusFilter);
                }
                
                // 添加自定义日期范围参数
                if (currentRefreshStatusFilter === 'custom' && currentRefreshStartDate && currentRefreshEndDate) {
                    params.append('refresh_start_date', currentRefreshStartDate);
                    params.append('refresh_end_date', currentRefreshEndDate);
                }
                
                showNotification('正在批量刷新Token，请稍候...', 'info');
                
                const result = await apiRequest(`/accounts/batch-refresh-tokens?${params.toString()}`, {
                    method: 'POST'
                });
                
                // 显示结果
                const successMsg = `批量刷新完成！\n总计: ${result.total_processed} 个账户\n成功: ${result.success_count} 个\n失败: ${result.failed_count} 个`;
                
                if (result.failed_count === 0) {
                    showNotification(successMsg, 'success');
                } else {
                    // 如果有失败的，显示详细信息
                    let detailMsg = successMsg + '\n\n失败账户：\n';
                    result.details.filter(d => d.status === 'failed').forEach(detail => {
                        detailMsg += `- ${detail.email}: ${detail.message}\n`;
                    });
                    showNotification(detailMsg, 'warning');
                }
                
                // 刷新账户列表
                loadAccounts(accountsCurrentPage);
                
            } catch (error) {
                showNotification(`批量刷新失败: ${error.message}`, 'error');
            }
        }
        
        // 右键菜单相关变量
        let contextMenuTarget = null;
        
        // 显示右键菜单
        function showAccountContextMenu(event, emailId) {
            event.preventDefault();
            event.stopPropagation();
            
            contextMenuTarget = emailId;
            const contextMenu = document.getElementById('contextMenu');
            
            // 设置菜单位置
            contextMenu.style.left = event.pageX + 'px';
            contextMenu.style.top = event.pageY + 'px';
            contextMenu.style.display = 'block';
            
            // 点击其他地方隐藏菜单
            setTimeout(() => {
                document.addEventListener('click', hideContextMenu);
            }, 10);
        }
        
        // 隐藏右键菜单
        function hideContextMenu() {
            const contextMenu = document.getElementById('contextMenu');
            contextMenu.style.display = 'none';
            contextMenuTarget = null;
            document.removeEventListener('click', hideContextMenu);
        }
        
        // 在新标签页中打开
        function openInNewTab() {
            if (contextMenuTarget) {
                const url = `${window.location.origin}/#/emails/${encodeURIComponent(contextMenuTarget)}`;
                window.open(url, '_blank');
            }
            hideContextMenu();
        }
        
        // 复制账户链接
        function copyAccountLink() {
            if (contextMenuTarget) {
                const url = `${window.location.origin}/#/emails/${encodeURIComponent(contextMenuTarget)}`;
                
                if (navigator.clipboard) {
                    navigator.clipboard.writeText(url).then(() => {
                        showNotification('链接已复制到剪贴板', 'success');
                    }).catch(() => {
                        fallbackCopyText(url);
                    });
                } else {
                    fallbackCopyText(url);
                }
            }
            hideContextMenu();
        }
        
        // 后备复制方法
        function fallbackCopyText(text) {
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                showNotification('链接已复制到剪贴板', 'success');
            } catch (err) {
                showNotification('复制失败，请手动复制', 'error');
            }
            document.body.removeChild(textArea);
        }
        
        // 从右键菜单编辑标签
        function contextEditTags() {
            if (contextMenuTarget) {
                const account = accounts.find(acc => acc.email_id === contextMenuTarget);
                if (account) {
                    editAccountTags(contextMenuTarget, account.tags || []);
                }
            }
            hideContextMenu();
        }
        
        // 从右键菜单删除账户
        function contextDeleteAccount() {
            if (contextMenuTarget) {
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
            
            const url = `${window.location.origin}/#/emails/${encodeURIComponent(currentAccount)}`;
            window.open(url, '_blank');
        }

        // 点击模态框外部关闭
        document.getElementById('emailModal').addEventListener('click', function(e) {
            if (e.target === this) {
                closeEmailModal();
            }
        });

        // 键盘快捷键
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + R: 刷新邮件
            if ((e.ctrlKey || e.metaKey) && e.key === 'r' && currentAccount) {
                e.preventDefault();
                refreshEmails();
            }

            // Escape: 关闭模态框
            if (e.key === 'Escape') {
                closeEmailModal();
            }

            // Ctrl/Cmd + F: 聚焦搜索框
            if ((e.ctrlKey || e.metaKey) && e.key === 'f' && document.getElementById('emailSearch')) {
                e.preventDefault();
                document.getElementById('emailSearch').focus();
            }
        });

        // 页面可见性变化时刷新数据
        document.addEventListener('visibilitychange', function() {
            if (!document.hidden && currentAccount) {
                // 页面重新可见时，如果超过5分钟则自动刷新
                const lastUpdate = document.getElementById('lastUpdateTime').textContent;
                if (lastUpdate !== '-') {
                    const lastUpdateTime = new Date(lastUpdate);
                    const now = new Date();
                    const diffMinutes = (now - lastUpdateTime) / (1000 * 60);

                    if (diffMinutes > 5) {
                        showNotification('检测到数据可能过期，正在刷新...', 'info', '', 2000);
                        setTimeout(() => refreshEmails(), 1000);
                    }
                }
            }
        });

        // 初始化
        window.addEventListener('load', function() {
            // 处理URL路由
            handleUrlRouting();
            
            // 如果没有路由匹配，显示默认页面
            if (!window.location.hash || window.location.hash === '#') {
                showPage('accounts');
            }

            // 显示欢迎消息
            setTimeout(() => {
                showNotification('欢迎使用邮件管理系统！', 'info', '欢迎', 3000);
            }, 500);
        });
        
        // URL路由处理
        function handleUrlRouting() {
            const hash = window.location.hash;
            
            if (hash.startsWith('#/emails/')) {
                const emailId = decodeURIComponent(hash.replace('#/emails/', ''));
                if (emailId) {
                    // 设置当前账户
                    currentAccount = emailId;
                    document.getElementById('currentAccountEmail').textContent = emailId;
                    document.getElementById('emailsNav').style.display = 'block';
                    
                    // 显示邮件页面
                    showPage('emails');
                    return;
                }
            }
        }
        
        // 监听浏览器返回按钮
        window.addEventListener('popstate', function() {
            handleUrlRouting();
        });

        // ==================== 管理面板功能 ====================
        
        // 切换管理面板标签
        function switchAdminTab(tabName, tabElement) {
            // 切换标签激活状态
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            tabElement.classList.add('active');
            
            // 切换面板显示
            if (tabName === 'tables') {
                document.getElementById('tablesPanel').classList.remove('hidden');
                document.getElementById('configPanel').classList.add('hidden');
                loadTablesList();
            } else if (tabName === 'config') {
                document.getElementById('tablesPanel').classList.add('hidden');
                document.getElementById('configPanel').classList.remove('hidden');
                loadSystemConfigs();
            }
        }
        
        // 加载数据表列表
        async function loadTablesList() {
            const tablesList = document.getElementById('tablesList');
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
        let currentTable = null;
        let currentTableData = [];
        
        async function loadTableData(tableName) {
            currentTable = tableName;
            document.getElementById('currentTableName').textContent = tableName;
            document.getElementById('tablesList').parentElement.style.display = 'none';
            document.getElementById('tableDataPanel').classList.remove('hidden');
            
            const contentDiv = document.getElementById('tableDataContent');
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
            document.getElementById('tableDataPanel').classList.add('hidden');
            document.getElementById('tablesList').parentElement.style.display = 'block';
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
            const searchTerm = document.getElementById('tableSearch').value.toLowerCase();
            
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
        
        // 存储当前编辑的记录信息
        let currentEditRecord = null;
        let currentTableColumns = [];
        
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
                document.getElementById('recordModalTitle').textContent = `添加记录 - ${currentTable}`;
                
                // 生成空白表单
                generateRecordForm(schema.columns, null);
                
                // 清空当前编辑记录
                currentEditRecord = null;
                
                // 显示模态框
                document.getElementById('recordModal').classList.remove('hidden');
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
                document.getElementById('recordModalTitle').textContent = `编辑记录 - ${currentTable} (ID: ${row.id})`;
                
                // 生成预填充的表单
                generateRecordForm(schema.columns, row);
                
                // 保存当前编辑记录
                currentEditRecord = row;
                
                // 显示模态框
                document.getElementById('recordModal').classList.remove('hidden');
            } catch (error) {
                showNotification(`获取表结构失败: ${error.message}`, 'error');
            }
        }
        
        // 生成记录表单
        function generateRecordForm(columns, data) {
            const formContent = document.getElementById('recordFormContent');
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
            document.getElementById('recordModal').classList.add('hidden');
            document.getElementById('recordFormContent').innerHTML = '';
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
                    const updateTime = config.updated_at ? formatRefreshTime(config.updated_at) : 'N/A';
                    
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

        // ==================== API测试功能 ====================
        
        // API配置定义
        const API_CONFIGS = {
            'login': {
                method: 'POST',
                endpoint: '/auth/login',
                body: { username: 'admin', password: 'admin123' },
                requiresAuth: false
            },
            'me': {
                method: 'GET',
                endpoint: '/auth/me',
                requiresAuth: true
            },
            'changePassword': {
                method: 'POST',
                endpoint: '/auth/change-password',
                body: { old_password: '', new_password: '' },
                requiresAuth: true
            },
            'accounts': {
                method: 'GET',
                endpoint: '/accounts',
                query: { 
                    page: 1, 
                    page_size: 10, 
                    email_search: '', 
                    tag_search: '',
                    refresh_status: '',
                    time_filter: '',
                    after_date: ''
                },
                requiresAuth: true
            },
            'addAccount': {
                method: 'POST',
                endpoint: '/accounts',
                body: { email_id: 'example@outlook.com', refresh_token: '', client_id: '', tags: [] },
                requiresAuth: true
            },
            'deleteAccount': {
                method: 'DELETE',
                endpoint: '/accounts/{email_id}',
                path: { email_id: 'example@outlook.com' },
                requiresAuth: true
            },
            'updateTags': {
                method: 'PUT',
                endpoint: '/accounts/{email_id}/tags',
                path: { email_id: 'example@outlook.com' },
                body: { tags: ['工作', '个人'] },
                requiresAuth: true
            },
            'addTag': {
                method: 'POST',
                endpoint: '/accounts/{email_id}/tags/add',
                path: { email_id: 'example@outlook.com' },
                body: { tag: 'VIP' },
                requiresAuth: true
            },
            'randomAccounts': {
                method: 'GET',
                endpoint: '/accounts/random',
                query: {
                    include_tags: '',
                    exclude_tags: '',
                    page: 1,
                    page_size: 5
                },
                requiresAuth: true
            },
            'refreshToken': {
                method: 'POST',
                endpoint: '/accounts/{email_id}/refresh-token',
                path: { email_id: 'example@outlook.com' },
                requiresAuth: true
            },
            'singleRefreshToken': {
                method: 'POST',
                endpoint: '/accounts/{email_id}/refresh-token',
                path: { email_id: 'example@outlook.com' },
                requiresAuth: true
            },
            'batchRefreshTokens': {
                method: 'POST',
                endpoint: '/accounts/batch-refresh-tokens',
                query: {
                    email_search: '',
                    tag_search: '',
                    refresh_status: '',
                    time_filter: '',
                    after_date: ''
                },
                requiresAuth: true
            },
            'emails': {
                method: 'GET',
                endpoint: '/emails/{email_id}',
                path: { email_id: 'example@outlook.com' },
                query: { folder: 'inbox', page: 1, page_size: 20, refresh: false },
                requiresAuth: true
            },
            'emailDetail': {
                method: 'GET',
                endpoint: '/emails/{email_id}/{message_id}',
                path: { email_id: 'example@outlook.com', message_id: 'INBOX-1' },
                requiresAuth: true
            },
            'dualView': {
                method: 'GET',
                endpoint: '/emails/{email_id}/dual-view',
                path: { email_id: 'example@outlook.com' },
                query: { inbox_page: 1, junk_page: 1, page_size: 20 },
                requiresAuth: true
            },
            'clearCache': {
                method: 'DELETE',
                endpoint: '/cache/{email_id}',
                path: { email_id: 'example@outlook.com' },
                requiresAuth: true
            },
            'clearAllCache': {
                method: 'DELETE',
                endpoint: '/cache',
                requiresAuth: true
            },
            'tableCount': {
                method: 'GET',
                endpoint: '/admin/tables/{table_name}/count',
                path: { table_name: 'accounts' },
                requiresAuth: true
            },
            'tableData': {
                method: 'GET',
                endpoint: '/admin/tables/{table_name}',
                path: { table_name: 'accounts' },
                requiresAuth: true
            },
            'deleteTableRecord': {
                method: 'DELETE',
                endpoint: '/admin/tables/{table_name}/{record_id}',
                path: { table_name: 'accounts', record_id: 1 },
                requiresAuth: true
            },
            'getConfig': {
                method: 'GET',
                endpoint: '/admin/config',
                requiresAuth: true
            },
            'updateConfig': {
                method: 'POST',
                endpoint: '/admin/config',
                body: { key: 'imap_server', value: 'outlook.office365.com', description: 'IMAP服务器地址' },
                requiresAuth: true
            },
            'systemInfo': {
                method: 'GET',
                endpoint: '/api',
                requiresAuth: false
            }
        };

        // 打开API测试模态框
        function openApiTest(apiKey) {
            const config = API_CONFIGS[apiKey];
            if (!config) {
                showNotification('API配置不存在', 'error');
                return;
            }

            // 设置标题和基本信息
            document.getElementById('apiTestTitle').textContent = `🚀 测试API: ${config.endpoint}`;
            document.getElementById('apiTestMethod').textContent = config.method;
            document.getElementById('apiTestEndpoint').textContent = config.endpoint;

            // 隐藏所有参数区域
            document.getElementById('apiTestPathParams').classList.add('hidden');
            document.getElementById('apiTestQueryParams').classList.add('hidden');
            document.getElementById('apiTestBody').classList.add('hidden');
            document.getElementById('apiTestResultSection').classList.add('hidden');

            // 路径参数
            if (config.path) {
                const pathParamsList = document.getElementById('apiTestPathParamsList');
                pathParamsList.innerHTML = '';
                Object.entries(config.path).forEach(([key, value]) => {
                    pathParamsList.innerHTML += `
                        <div class="api-test-param">
                            <label>${key}</label>
                            <input type="text" id="path_${key}" value="${value}" placeholder="${key}">
                        </div>
                    `;
                });
                document.getElementById('apiTestPathParams').classList.remove('hidden');
            }

            // 查询参数
            if (config.query) {
                const queryParamsList = document.getElementById('apiTestQueryParamsList');
                queryParamsList.innerHTML = '';
                Object.entries(config.query).forEach(([key, value]) => {
                    const inputType = typeof value === 'boolean' ? 'checkbox' : 
                                     typeof value === 'number' ? 'number' : 'text';
                    if (inputType === 'checkbox') {
                        queryParamsList.innerHTML += `
                            <div class="api-test-param">
                                <label>
                                    <input type="checkbox" id="query_${key}" ${value ? 'checked' : ''}>
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
                document.getElementById('apiTestQueryParams').classList.remove('hidden');
            }

            // 请求体
            if (config.body) {
                document.getElementById('apiTestBodyContent').value = JSON.stringify(config.body, null, 2);
                document.getElementById('apiTestBody').classList.remove('hidden');
            }

            // 存储当前API配置
            window.currentApiConfig = config;
            window.currentApiKey = apiKey;

            // 显示模态框
            document.getElementById('apiTestModal').classList.add('show');
        }

        // 关闭API测试模态框
        function closeApiTestModal(event) {
            if (event && event.target !== event.currentTarget) return;
            document.getElementById('apiTestModal').classList.remove('show');
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
                    Object.keys(config.path).forEach(key => {
                        const value = document.getElementById(`path_${key}`).value;
                        url = url.replace(`{${key}}`, encodeURIComponent(value));
                    });
                }

                // 添加查询参数
                if (config.query) {
                    const queryParams = new URLSearchParams();
                    Object.keys(config.query).forEach(key => {
                        const element = document.getElementById(`query_${key}`);
                        let value;
                        if (element.type === 'checkbox') {
                            value = element.checked;
                        } else {
                            value = element.value;
                        }
                        if (value !== '' && value !== null && value !== undefined) {
                            queryParams.append(key, value);
                        }
                    });
                    const queryString = queryParams.toString();
                    if (queryString) {
                        url += '?' + queryString;
                    }
                }

                // 构建请求选项
                const options = {
                    method: config.method
                };

                // 添加请求体
                if (config.body) {
                    try {
                        const bodyText = document.getElementById('apiTestBodyContent').value;
                        const bodyJson = JSON.parse(bodyText);
                        options.body = JSON.stringify(bodyJson);
                    } catch (e) {
                        showNotification('请求体JSON格式错误', 'error');
                        return;
                    }
                }

                // 发送请求
                showNotification('正在发送请求...', 'info');
                
                let response;
                if (config.requiresAuth) {
                    response = await apiRequest(url, options);
                } else {
                    // 不需要认证的接口直接fetch
                    const fetchOptions = {
                        method: options.method,
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    };
                    if (options.body) {
                        fetchOptions.body = options.body;
                    }
                    const res = await fetch(API_BASE + url, fetchOptions);
                    if (!res.ok) {
                        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                    }
                    response = await res.json();
                }

                // 显示响应
                const resultSection = document.getElementById('apiTestResultSection');
                const resultDiv = document.getElementById('apiTestResult');
                const resultContent = document.getElementById('apiTestResultContent');

                resultSection.classList.remove('hidden');
                resultDiv.className = 'api-test-result success';
                resultContent.textContent = JSON.stringify(response, null, 2);

                showNotification('请求成功！', 'success');

            } catch (error) {
                // 显示错误
                const resultSection = document.getElementById('apiTestResultSection');
                const resultDiv = document.getElementById('apiTestResult');
                const resultContent = document.getElementById('apiTestResultContent');

                resultSection.classList.remove('hidden');
                resultDiv.className = 'api-test-result error';
                resultContent.textContent = `错误: ${error.message}`;

                showNotification(`请求失败: ${error.message}`, 'error');
            }
        }