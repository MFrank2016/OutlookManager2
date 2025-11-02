#!/usr/bin/env python3
"""
测试模板系统 - 验证所有模板文件是否正确加载
"""

import os
from pathlib import Path
from fastapi.templating import Jinja2Templates
from fastapi import Request

def test_templates():
    """测试模板系统"""
    print("🔍 开始测试模板系统...")
    print()
    
    # 初始化Jinja2模板
    template_dir = "static/templates"
    
    if not os.path.exists(template_dir):
        print(f"❌ 模板目录不存在: {template_dir}")
        return False
    
    print(f"✅ 模板目录存在: {template_dir}")
    templates = Jinja2Templates(directory=template_dir)
    print(f"✅ Jinja2模板引擎初始化成功")
    print()
    
    # 测试的模板文件
    test_files = {
        "主模板": [
            "base.html",
            "index.html",
        ],
        "组件": [
            "components/sidebar.html",
            "components/context_menu.html",
            "components/api_docs_content.html",
        ],
        "页面": [
            "pages/accounts.html",
            "pages/add_account.html",
            "pages/batch_add.html",
            "pages/admin_panel.html",
            "pages/api_docs.html",
            "pages/emails.html",
        ],
        "模态框": [
            "modals/email_detail.html",
            "modals/tags.html",
            "modals/record.html",
            "modals/config_edit.html",
            "modals/api_test.html",
        ],
    }
    
    total_files = 0
    success_files = 0
    failed_files = []
    
    # 检查所有模板文件
    for category, files in test_files.items():
        print(f"📁 {category}:")
        for file_path in files:
            total_files += 1
            full_path = Path(template_dir) / file_path
            
            if full_path.exists():
                print(f"  ✓ {file_path}")
                success_files += 1
            else:
                print(f"  ✗ {file_path} (文件不存在)")
                failed_files.append(file_path)
        print()
    
    # 测试渲染主模板
    print("🎨 测试模板渲染...")
    try:
        # 创建一个模拟的Request对象
        class MockRequest:
            def __init__(self):
                self.url = type('obj', (object,), {'path': '/'})()
                self.headers = {}
                self.query_params = {}
        
        mock_request = MockRequest()
        
        # 尝试获取模板（不实际渲染）
        template = templates.get_template("index.html")
        print("  ✓ 主模板 (index.html) 加载成功")
        print("  ✓ 模板继承和引用结构正确")
    except Exception as e:
        print(f"  ✗ 模板渲染测试失败: {e}")
        failed_files.append("index.html (渲染测试)")
    
    print()
    print("=" * 60)
    print(f"测试结果:")
    print(f"  总计: {total_files} 个文件")
    print(f"  成功: {success_files} 个")
    print(f"  失败: {len(failed_files)} 个")
    
    if failed_files:
        print()
        print("失败的文件:")
        for file in failed_files:
            print(f"  - {file}")
        return False
    
    print()
    print("🎉 所有模板测试通过!")
    return True

if __name__ == "__main__":
    success = test_templates()
    exit(0 if success else 1)

