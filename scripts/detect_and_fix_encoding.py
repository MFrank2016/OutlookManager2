#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能检测并修复文件编码
"""

import sys
import os


def try_decode_with_encodings(file_bytes):
    """尝试不同编码解码文件"""
    encodings_to_try = [
        'utf-8',
        'gbk',
        'gb2312',
        'gb18030',
        'utf-16',
        'utf-16le',
        'utf-16be',
        'latin-1',
        'cp1252',
        'iso-8859-1',
    ]
    
    results = []
    for encoding in encodings_to_try:
        try:
            text = file_bytes.decode(encoding)
            # 统计中文字符数量
            chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            # 统计乱码特征（连续的生僻字）
            garbled_score = sum(1 for c in text if '\ue000' <= c <= '\uf8ff')
            
            results.append({
                'encoding': encoding,
                'text': text,
                'chinese_count': chinese_count,
                'garbled_score': garbled_score,
                'total_chars': len(text)
            })
            print(f"✓ {encoding:15s} - 中文:{chinese_count:5d}, 乱码分:{garbled_score:3d}")
        except (UnicodeDecodeError, LookupError):
            print(f"✗ {encoding:15s} - 解码失败")
            continue
    
    return results


def find_best_encoding(results):
    """找到最佳编码"""
    if not results:
        return None
    
    # 按中文字符数和乱码分数排序
    results.sort(key=lambda x: (x['chinese_count'], -x['garbled_score']), reverse=True)
    return results[0]


def main():
    backup_file = 'static/index.html.backup'
    
    if not os.path.exists(backup_file):
        print(f"❌ 文件不存在: {backup_file}")
        return
    
    print("=" * 70)
    print(f"正在分析文件: {backup_file}")
    print("=" * 70)
    
    # 读取原始字节
    with open(backup_file, 'rb') as f:
        file_bytes = f.read()
    
    print(f"\n文件大小: {len(file_bytes)} 字节\n")
    print("尝试不同编码:")
    print("-" * 70)
    
    # 尝试不同编码
    results = try_decode_with_encodings(file_bytes)
    
    # 找到最佳编码
    best = find_best_encoding(results)
    
    if best:
        print("\n" + "=" * 70)
        print(f"✅ 推荐编码: {best['encoding']}")
        print(f"   - 中文字符: {best['chinese_count']} 个")
        print(f"   - 乱码分数: {best['garbled_score']}")
        print("=" * 70)
        
        # 显示示例文本
        lines = best['text'].split('\n')
        print("\n前50行中包含中文的行:")
        print("-" * 70)
        count = 0
        for i, line in enumerate(lines[:100]):
            if any('\u4e00' <= c <= '\u9fff' for c in line):
                print(f"行{i+1:4d}: {line.strip()[:80]}")
                count += 1
                if count >= 10:
                    break
        
        # 保存修复后的文件
        print("\n" + "=" * 70)
        print("开始重新拆分文件...")
        print("=" * 70)
        
        # 重新拆分HTML
        lines = best['text'].split('\n')
        
        # 找到各部分的边界
        css_start = -1
        css_end = -1
        body_start = -1
        body_end = -1
        script_start = -1
        
        for i, line in enumerate(lines):
            if '<style>' in line:
                css_start = i + 1
            elif '</style>' in line and css_start > 0:
                css_end = i
            elif '<body>' in line:
                body_start = i + 1
            elif '</body>' in line:
                body_end = i
            elif '<script>' in line and body_end > 0:
                script_start = i + 1
                break
        
        if css_start > 0 and css_end > 0:
            # 提取CSS
            css_content = '\n'.join(lines[css_start:css_end])
            with open('static/css/style.css', 'w', encoding='utf-8') as f:
                f.write(css_content)
            print(f"✅ CSS文件: static/css/style.css ({len(css_content)} 字符)")
        
        if script_start > 0:
            # 提取JS
            js_content = '\n'.join(lines[script_start:-2])  # 去掉最后的</script></body></html>
            with open('static/js/app.js', 'w', encoding='utf-8') as f:
                f.write(js_content)
            print(f"✅ JS文件: static/js/app.js ({len(js_content)} 字符)")
        
        if body_start > 0 and body_end > 0:
            # 创建新的HTML
            html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Outlook邮件管理系统</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
'''
            html_content += '\n'.join(lines[body_start-1:body_end+1])
            html_content += '''
    <script src="/static/js/app.js"></script>
</body>
</html>'''
            
            with open('static/index.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✅ HTML文件: static/index.html ({len(html_content)} 字符)")
        
        print("\n" + "=" * 70)
        print("✅ 所有文件修复并拆分完成！")
        print("=" * 70)
        
    else:
        print("\n❌ 无法找到合适的编码")


if __name__ == '__main__':
    main()

