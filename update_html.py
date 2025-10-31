#!/usr/bin/env python3
"""
更新 HTML 文件以引用拆分后的模块
"""

import re
from pathlib import Path

# CSS 模块列表（按加载顺序）
CSS_MODULES = [
    'base.css',
    'layout.css',
    'components.css',
    'search-filter.css',
    'tags.css',
    'forms.css',
    'accounts.css',
    'emails.css',
    'admin.css',
    'apidocs.css',
    'context-menu.css',
    'responsive.css',
]

# JavaScript 模块列表（按依赖顺序）
JS_MODULES = [
    'api.js',
    'utils.js',
    'ui.js',
    'accounts.js',
    'emails.js',
    'batch.js',
    'tags.js',
    'apidocs.js',
    'admin.js',
    'apitest.js',
    'context-menu.js',
    'main.js',
]

def generate_css_links():
    """生成 CSS 链接标签"""
    links = []
    for module in CSS_MODULES:
        links.append(f'    <link rel="stylesheet" href="static/css/{module}">')
    return '\n'.join(links)

def generate_js_scripts():
    """生成 JavaScript 脚本标签"""
    scripts = []
    for module in JS_MODULES:
        scripts.append(f'    <script src="static/js/{module}"></script>')
    return '\n'.join(scripts)

def update_html_file(html_file):
    """更新 HTML 文件"""
    if not html_file.exists():
        print(f"❌ 文件不存在: {html_file}")
        return False
    
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    backup_file = html_file.with_suffix('.html.bak')
    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"📦 已备份: {backup_file.name}")
    
    # 替换 CSS 引用
    # 查找旧的 CSS 引用
    old_css_pattern = r'<link rel="stylesheet" href="static/css/style\.css">'
    new_css = generate_css_links()
    
    if re.search(old_css_pattern, content):
        content = re.sub(old_css_pattern, new_css, content)
        print("✅ 已更新 CSS 引用")
    else:
        print("⚠️  未找到旧的 CSS 引用，请手动添加:")
        print(new_css)
    
    # 替换 JavaScript 引用
    # 查找旧的 JS 引用
    old_js_pattern = r'<script src="static/js/app\.js"></script>'
    new_js = generate_js_scripts()
    
    if re.search(old_js_pattern, content):
        content = re.sub(old_js_pattern, new_js, content)
        print("✅ 已更新 JavaScript 引用")
    else:
        print("⚠️  未找到旧的 JavaScript 引用，请手动添加:")
        print(new_js)
    
    # 写回文件
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"💾 已保存: {html_file.name}")
    return True

def main():
    """主函数"""
    base_dir = Path(__file__).parent
    
    # 查找所有 HTML 文件
    html_files = list(base_dir.glob('static/**/*.html'))
    html_files.extend(base_dir.glob('templates/**/*.html'))
    
    if not html_files:
        print("❌ 未找到 HTML 文件")
        return
    
    print(f"🔍 找到 {len(html_files)} 个 HTML 文件\n")
    
    for html_file in html_files:
        print(f"\n处理: {html_file.relative_to(base_dir)}")
        print("-" * 50)
        update_html_file(html_file)
    
    print("\n" + "=" * 50)
    print("✨ 更新完成!")
    print("\n📝 下一步:")
    print("   1. 检查生成的 HTML 文件")
    print("   2. 清除浏览器缓存")
    print("   3. 重新加载页面测试")
    print("   4. 如有问题，可恢复 .bak 文件")
    
    # 生成引用列表供手动添加
    print("\n" + "=" * 50)
    print("📋 CSS 引用列表（可手动复制）:")
    print("-" * 50)
    print(generate_css_links())
    
    print("\n" + "=" * 50)
    print("📋 JavaScript 引用列表（可手动复制）:")
    print("-" * 50)
    print(generate_js_scripts())

if __name__ == '__main__':
    main()

