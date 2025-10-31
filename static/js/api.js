// API请求模块
const API_BASE = '';

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

// API 配置已移至 apitest.js 模块

