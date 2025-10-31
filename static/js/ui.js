// UI工具模块

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
    // 顶部栏已移除，不再需要设置标题
    // const pageTitleElement = document.getElementById('pageTitle');
    // if (pageTitleElement) {
    //     pageTitleElement.textContent = titles[pageName] || '';
    // }

    // 页面特定逻辑
    if (pageName === 'accounts') {
        // 智能加载：优先使用缓存
        loadAccountsSmart();
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

// 表单管理函数
function clearAddAccountForm() {
    document.getElementById('email').value = '';
    document.getElementById('refreshToken').value = '';
    document.getElementById('clientId').value = '';
}

function clearBatchForm() {
    document.getElementById('batchAccounts').value = '';
}

// 批量添加进度管理
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

