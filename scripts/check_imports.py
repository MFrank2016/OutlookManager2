"""
导入检查脚本

用于验证所有模块是否能正常导入
"""

import sys

def check_imports():
    """检查所有模块导入"""
    print("=" * 60)
    print("模块导入检查")
    print("=" * 60)
    
    modules = [
        "config",
        "logger_config",
        "models",
        "imap_pool",
        "cache_service",
        "email_utils",
        "account_service",
        "oauth_service",
        "email_service",
        "routes",
        "routes.auth_routes",
        "routes.account_routes",
        "routes.email_routes",
        "routes.cache_routes",
    ]
    
    failed = []
    
    for module in modules:
        try:
            __import__(module)
            print(f"✅ {module:<30} 导入成功")
        except Exception as e:
            print(f"❌ {module:<30} 导入失败: {e}")
            failed.append(module)
    
    print("=" * 60)
    
    if failed:
        print(f"\n❌ 失败: {len(failed)} 个模块导入失败")
        for module in failed:
            print(f"  - {module}")
        return False
    else:
        print(f"\n✅ 成功: 所有 {len(modules)} 个模块导入成功！")
        return True

if __name__ == "__main__":
    success = check_imports()
    sys.exit(0 if success else 1)

