#!/usr/bin/env python3
"""
代码拆分辅助脚本
自动将 app.js 和 style.css 拆分成多个模块文件
"""

import os
import re
from pathlib import Path

# JavaScript 模块定义（函数名到文件的映射）
JS_MODULES = {
    'emails.js': [
        # 变量
        'let allEmails', 'let filteredEmails', 'let searchTimeout',
        'let autoRefreshTimer', 'let isLoadingEmails',
        'let emailCurrentPage', 'let emailPageSize', 'let emailTotalCount',
        # 函数
        'function startAutoRefresh', 'function stopAutoRefresh',
        'function viewAccountEmails', 'function backToAccounts',
        'function switchEmailTab', 'function loadEmails',
        'function renderEmails', 'function createEmailTableRow',
        'function createEmailItem', 'function showEmailDetail',
        'function renderEmailContent', 'function showEmailContentTab',
        'function closeEmailModal', 'function refreshEmails',
        'function clearCache', 'function exportEmails',
        'function searchAndLoadEmails', 'function clearSearchFilters',
        'function searchEmails', 'function applyFilters',
        'function changeEmailPageSize', 'function emailNextPage',
        'function emailPrevPage', 'function updateEmailPagination',
        'function updateEmailStats', 'function changeEmailPage',
    ],
    'batch.js': [
        'function batchAddAccounts', 'function validateBatchFormat',
        'function loadSampleData', 'function testAccountConnection',
    ],
    'tags.js': [
        'function editAccountTags', 'function renderCurrentTags',
        'function addTag', 'function removeTag',
        'function closeTagsModal', 'function saveAccountTags',
    ],
    'admin.js': [
        'let currentTable', 'let currentTableData',
        'let currentEditRecord', 'let currentTableColumns',
        'function switchAdminTab', 'function loadTablesList',
        'function loadTableData', 'function renderTableData',
        'function backToTablesList', 'function refreshTableData',
        'function searchTableData', 'function openAddRecordModal',
        'function editTableRow', 'function generateRecordForm',
        'function saveTableRecord', 'function closeRecordModal',
        'function deleteTableRow', 'function loadSystemConfigs',
        'function editConfig',
    ],
    'apitest.js': [
        'function openApiTest', 'function closeApiTestModal',
        'function resetApiTestForm', 'function executeApiTest',
    ],
    'context-menu.js': [
        'let contextMenuTarget',
        'function showAccountContextMenu', 'function hideContextMenu',
        'function openInNewTab', 'function copyAccountLink',
        'function contextEditTags', 'function contextDeleteAccount',
        'function showEmailsContextMenu',
    ],
    'apidocs.js': [
        'function initApiDocs', 'function copyApiBaseUrl',
        'function downloadApiDocs', 'function generateApiDocsMarkdown',
        'function tryApi',
    ],
}

# CSS 模块定义（选择器到文件的映射）
CSS_MODULES = {
    'layout.css': [
        '.app-container', '.sidebar', '.sidebar-header', '.sidebar-nav',
        '.nav-item', '.main-content', '.main-header', '.main-body',
    ],
    'accounts.css': [
        '.account-list', '.account-item', '.account-info', '.account-avatar',
        '.account-details', '.account-actions', '.account-status',
        '.account-tags', '.account-tag', '.account-refresh-info',
        '.refresh-status', '.refresh-time',
    ],
    'emails.css': [
        '.email-table', '.email-list', '.email-item', '.email-avatar',
        '.email-sender', '.email-subject', '.email-date', '.email-content',
        '.email-detail-meta', '.email-content-tabs', '.content-tab',
        '.email-copyable', '.copy-icon',
    ],
    'admin.css': [
        '.admin-panel', '.tables-list', '.table-item', '.table-icon',
        '.table-details', '.table-meta', '.table-actions', '.count-badge',
        '.configs-list', '.config-item', '.config-icon', '.config-details',
        '.config-value', '.config-meta', '.config-actions',
        '.table-responsive', '.data-table', '.data-table-actions',
        '.api-test-modal', '.api-test-content', '.api-test-header',
        '.api-test-body', '.api-test-section', '.api-test-param',
        '.api-test-result', '.api-test-actions',
    ],
    'search-filter.css': [
        '.search-container', '.search-input', '.search-icon',
        '.filter-container', '.filter-group', '.filter-label',
        '.filter-select',
    ],
    'context-menu.css': [
        '.context-menu', '.context-menu-item', '.context-menu-divider',
    ],
    'tags.css': [
        '#tagsModal', '.tag-item', '.tags-list', '.tag-name',
        '.tag-delete', '.input-group',
    ],
    'forms.css': [
        '.form-page', '.form-section',
    ],
    'apidocs.css': [
        '.api-docs', '.api-endpoint', '.api-header', '.api-method',
        '.api-path', '.api-body', '.api-description', '.api-section',
        '.api-params', '.api-param', '.api-example', '.api-response',
    ],
}

def extract_functions(source_file, target_patterns):
    """从源文件中提取匹配的函数"""
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    extracted = []
    for pattern in target_patterns:
        if pattern.startswith('let ') or pattern.startswith('const ') or pattern.startswith('var '):
            # 提取变量声明
            var_name = pattern.split()[1]
            regex = rf'{re.escape(pattern)}[^;]*;'
            matches = re.findall(regex, content, re.MULTILINE)
            if matches:
                extracted.extend(matches)
        elif pattern.startswith('function '):
            # 提取函数
            func_name = pattern.split()[1].replace('()', '')
            # 匹配函数定义（包括async）
            regex = rf'(async\s+)?function\s+{re.escape(func_name)}\s*\([^)]*\)\s*\{{[^}}]*\}}'
            matches = re.findall(regex, content, re.DOTALL)
            if matches:
                extracted.extend([''.join(match) for match in matches])
    
    return '\n\n'.join(extracted)

def extract_css_rules(source_file, target_selectors):
    """从源文件中提取匹配的CSS规则"""
    with open(source_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    extracted = []
    for selector in target_selectors:
        # 转义特殊字符
        escaped = re.escape(selector)
        # 匹配 CSS 规则
        regex = rf'{escaped}\s*{{[^}}]*}}'
        matches = re.findall(regex, content, re.DOTALL)
        if matches:
            extracted.extend(matches)
    
    return '\n\n'.join(extracted)

def split_files():
    """执行文件拆分"""
    base_dir = Path(__file__).parent
    js_dir = base_dir / 'static' / 'js'
    css_dir = base_dir / 'static' / 'css'
    
    # 确保目录存在
    js_dir.mkdir(parents=True, exist_ok=True)
    css_dir.mkdir(parents=True, exist_ok=True)
    
    source_js = base_dir / 'static' / 'js' / 'app.js'
    source_css = base_dir / 'static' / 'css' / 'style.css'
    
    if not source_js.exists():
        print(f"❌ 源文件不存在: {source_js}")
        return
    
    if not source_css.exists():
        print(f"❌ 源文件不存在: {source_css}")
        return
    
    print("🚀 开始拆分 JavaScript 文件...")
    for target_file, patterns in JS_MODULES.items():
        print(f"   处理: {target_file}")
        content = extract_functions(source_js, patterns)
        if content:
            output_file = js_dir / target_file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"// {target_file} - 自动生成\n\n")
                f.write(content)
            print(f"   ✅ 已创建: {target_file} ({len(content)} 字符)")
        else:
            print(f"   ⚠️  未找到匹配内容: {target_file}")
    
    print("\n🎨 开始拆分 CSS 文件...")
    for target_file, selectors in CSS_MODULES.items():
        print(f"   处理: {target_file}")
        content = extract_css_rules(source_css, selectors)
        if content:
            output_file = css_dir / target_file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"/* {target_file} - 自动生成 */\n\n")
                f.write(content)
            print(f"   ✅ 已创建: {target_file} ({len(content)} 字符)")
        else:
            print(f"   ⚠️  未找到匹配内容: {target_file}")
    
    print("\n✨ 拆分完成!")
    print("\n📝 下一步:")
    print("   1. 检查生成的文件是否正确")
    print("   2. 更新 HTML 文件中的脚本引用")
    print("   3. 测试所有功能是否正常")
    print("   4. 备份原始文件: app.js.bak 和 style.css.bak")

if __name__ == '__main__':
    split_files()

