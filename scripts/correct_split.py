#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正确拆分HTML文件
"""

import re


def main():
    # 读取原始备份文件
    with open('static/index.html.backup', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("=" * 70)
    print("开始正确拆分HTML文件...")
    print("=" * 70)
    print(f"\n原始文件大小: {len(content)} 字符\n")
    
    # 使用正则表达式更精确地找到各部分
    # 1. 提取CSS (从<style>到</style>)
    css_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    if css_match:
        css_content = css_match.group(1).strip()
        with open('static/css/style.css', 'w', encoding='utf-8') as f:
            f.write(css_content)
        print(f"✅ CSS文件: {len(css_content)} 字符, {len(css_content.splitlines())} 行")
    else:
        print("❌ 未找到CSS部分")
    
    # 2. 提取JavaScript (从最后一个<script>到</script>)
    # 找到</body>之前的<script>标签
    script_pattern = r'<script>(.*?)</script>\s*</body>'
    script_match = re.search(script_pattern, content, re.DOTALL)
    if script_match:
        js_content = script_match.group(1).strip()
        with open('static/js/app.js', 'w', encoding='utf-8') as f:
            f.write(js_content)
        print(f"✅ JS文件: {len(js_content)} 字符, {len(js_content.splitlines())} 行")
    else:
        print("❌ 未找到JavaScript部分")
    
    # 3. 构建新的HTML文件
    # 找到</head>和<body>之间，以及<script>之前的body结束位置
    head_end = content.find('</head>')
    body_start = content.find('<body>', head_end)
    script_start = content.rfind('<script>')
    
    if head_end > 0 and body_start > 0 and script_start > 0:
        # 提取body内容(从<body>到<script>之前)
        body_content = content[body_start:script_start].strip()
        
        # 构建新的HTML
        new_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Outlook邮件管理系统</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
''' + body_content + '''

    <script src="/static/js/app.js"></script>
</body>
</html>'''
        
        with open('static/index.html', 'w', encoding='utf-8') as f:
            f.write(new_html)
        print(f"✅ HTML文件: {len(new_html)} 字符, {len(new_html.splitlines())} 行")
    else:
        print("❌ 未找到HTML结构")
    
    # 验证中文
    print("\n" + "=" * 70)
    print("验证中文显示:")
    print("=" * 70)
    
    with open('static/index.html', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    chinese_lines = []
    for i, line in enumerate(lines[:100], 1):
        if any('\u4e00' <= c <= '\u9fff' for c in line):
            chinese_lines.append((i, line.strip()[:80]))
            if len(chinese_lines) >= 10:
                break
    
    for line_num, text in chinese_lines:
        print(f"行{line_num:4d}: {text}")
    
    print("\n" + "=" * 70)
    print("✅ 文件拆分完成！")
    print("=" * 70)


if __name__ == '__main__':
    main()

