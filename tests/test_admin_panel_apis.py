"""
测试管理面板中的新增API接口
验证两个新接口在Web界面中的功能
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def get_api_key():
    """从数据库获取API Key"""
    import sqlite3
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_config WHERE key = 'api_key'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def test_admin_panel_accessible():
    """测试管理面板是否可访问"""
    print("=" * 60)
    print("测试1: 管理面板可访问性")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200 and "Outlook邮件管理系统" in response.text:
            print("✓ 管理面板可访问")
            
            # 检查新接口是否在HTML中
            if "/accounts/random" in response.text:
                print("✓ 随机获取邮箱接口已添加到管理面板")
            else:
                print("❌ 随机获取邮箱接口未找到")
                return False
            
            if "/accounts/{email_id}/tags/add" in response.text:
                print("✓ 添加标签接口已添加到管理面板")
            else:
                print("❌ 添加标签接口未找到")
                return False
            
            # 检查试用按钮
            if 'openApiTest(\'randomAccounts\')' in response.text:
                print("✓ 随机获取邮箱试用按钮已配置")
            else:
                print("❌ 随机获取邮箱试用按钮未配置")
                return False
                
            if 'openApiTest(\'addTag\')' in response.text:
                print("✓ 添加标签试用按钮已配置")
            else:
                print("❌ 添加标签试用按钮未配置")
                return False
            
            # 检查JavaScript配置
            if "'randomAccounts':" in response.text:
                print("✓ 随机获取邮箱API配置已添加")
            else:
                print("❌ 随机获取邮箱API配置未找到")
                return False
                
            if "'addTag':" in response.text:
                print("✓ 添加标签API配置已添加")
            else:
                print("❌ 添加标签API配置未找到")
                return False
            
            return True
        else:
            print(f"❌ 管理面板访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 访问管理面板失败: {e}")
        return False

def test_random_accounts_via_panel():
    """测试通过管理面板调用随机获取邮箱接口"""
    print("\n" + "=" * 60)
    print("测试2: 随机获取邮箱接口功能")
    print("=" * 60)
    
    api_key = get_api_key()
    headers = {"X-API-Key": api_key}
    
    # 模拟管理面板的API调用
    params = {
        "include_tags": "",
        "exclude_tags": "",
        "page": 1,
        "page_size": 5
    }
    
    try:
        response = requests.get(
            f"{BASE_URL}/accounts/random",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 接口调用成功")
            print(f"  返回账户数: {len(data['accounts'])}")
            print(f"  总数: {data['total_accounts']}")
            print(f"  分页: {data['page']}/{data['total_pages']}")
            
            if data['accounts']:
                print(f"  示例账户: {data['accounts'][0]['email_id']}")
            
            return True
        else:
            print(f"❌ 接口调用失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        return False

def test_add_tag_via_panel():
    """测试通过管理面板调用添加标签接口"""
    print("\n" + "=" * 60)
    print("测试3: 添加标签接口功能")
    print("=" * 60)
    
    api_key = get_api_key()
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    # 首先获取一个测试账户
    response = requests.get(
        f"{BASE_URL}/accounts",
        headers={"X-API-Key": api_key},
        params={"page_size": 1}
    )
    
    if response.status_code != 200 or not response.json().get('accounts'):
        print("❌ 无可用账户进行测试")
        return False
    
    test_email = response.json()['accounts'][0]['email_id']
    print(f"测试账户: {test_email}")
    
    # 模拟管理面板的API调用
    try:
        response = requests.post(
            f"{BASE_URL}/accounts/{test_email}/tags/add",
            headers=headers,
            json={"tag": "管理面板测试"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 接口调用成功")
            print(f"  邮箱: {data['email_id']}")
            print(f"  消息: {data['message']}")
            return True
        else:
            print(f"❌ 接口调用失败: {response.status_code}")
            print(f"  响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        return False

def test_api_documentation():
    """测试API文档中是否包含新接口"""
    print("\n" + "=" * 60)
    print("测试4: API文档完整性")
    print("=" * 60)
    
    try:
        # 访问Swagger文档
        response = requests.get(f"{BASE_URL}/docs", timeout=5)
        if response.status_code == 200:
            print("✓ Swagger文档可访问")
        else:
            print(f"⚠️  Swagger文档访问异常: {response.status_code}")
        
        # 访问OpenAPI JSON
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            openapi_spec = response.json()
            paths = openapi_spec.get('paths', {})
            
            if '/accounts/random' in paths:
                print("✓ 随机获取邮箱接口已包含在API文档中")
            else:
                print("❌ 随机获取邮箱接口未包含在API文档中")
                return False
            
            if '/accounts/{email_id}/tags/add' in paths:
                print("✓ 添加标签接口已包含在API文档中")
            else:
                print("❌ 添加标签接口未包含在API文档中")
                return False
            
            return True
        else:
            print(f"❌ 无法访问OpenAPI文档: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 文档检查失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("开始测试管理面板新增API接口...")
    print(f"基础URL: {BASE_URL}")
    print()
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/api", timeout=2)
        print("✓ 服务器正在运行\n")
    except Exception as e:
        print(f"❌ 服务器未运行或无法访问: {e}")
        print("请先启动服务器: python main.py")
        return
    
    # 运行测试
    results = []
    
    results.append(("管理面板可访问性", test_admin_panel_accessible()))
    results.append(("随机获取邮箱接口", test_random_accounts_via_panel()))
    results.append(("添加标签接口", test_add_tag_via_panel()))
    results.append(("API文档完整性", test_api_documentation()))
    
    # 打印总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for name, result in results:
        status = "✓ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！新接口已成功集成到管理面板。")
    else:
        print("\n⚠️  部分测试失败，请检查相关配置。")

if __name__ == "__main__":
    main()

