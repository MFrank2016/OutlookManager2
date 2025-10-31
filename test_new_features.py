"""
测试新功能脚本
测试API Key认证、随机获取邮箱、添加标签功能
"""

import sqlite3
import requests
import json

DB_FILE = "data.db"
BASE_URL = "http://localhost:8000"


def get_api_key():
    """从数据库获取API Key"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM system_config WHERE key = 'api_key'")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return None


def test_api_key_auth():
    """测试API Key认证"""
    print("=" * 60)
    print("测试1: API Key认证")
    print("=" * 60)
    
    api_key = get_api_key()
    if not api_key:
        print("❌ 未找到API Key")
        return False
    
    print(f"✓ 从数据库获取API Key: {api_key}")
    
    # 测试使用X-API-Key头访问
    headers = {"X-API-Key": api_key}
    response = requests.get(f"{BASE_URL}/accounts", headers=headers)
    
    if response.status_code == 200:
        print("✓ 使用X-API-Key头认证成功")
        data = response.json()
        print(f"  账户数量: {data['total_accounts']}")
        return True
    else:
        print(f"❌ API Key认证失败: {response.status_code}")
        print(f"  响应: {response.text}")
        return False


def test_random_accounts():
    """测试随机获取邮箱接口"""
    print("\n" + "=" * 60)
    print("测试2: 随机获取邮箱接口")
    print("=" * 60)
    
    api_key = get_api_key()
    headers = {"X-API-Key": api_key}
    
    # 测试1: 无筛选条件
    print("\n测试2.1: 随机获取所有账户（无筛选）")
    response = requests.get(
        f"{BASE_URL}/accounts/random",
        headers=headers,
        params={"page": 1, "page_size": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 获取成功: 总数={data['total_accounts']}, 返回={len(data['accounts'])}条")
        if data['accounts']:
            print(f"  示例账户: {data['accounts'][0]['email_id']}")
    else:
        print(f"❌ 获取失败: {response.status_code}")
        print(f"  响应: {response.text}")
        return False
    
    # 测试2: 包含标签筛选
    print("\n测试2.2: 随机获取包含特定标签的账户")
    response = requests.get(
        f"{BASE_URL}/accounts/random",
        headers=headers,
        params={"include_tags": "测试", "page": 1, "page_size": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 获取成功: 总数={data['total_accounts']}, 返回={len(data['accounts'])}条")
        if data['accounts']:
            for acc in data['accounts']:
                print(f"  - {acc['email_id']}: 标签={acc['tags']}")
    else:
        print(f"❌ 获取失败: {response.status_code}")
    
    # 测试3: 排除标签筛选
    print("\n测试2.3: 随机获取不包含特定标签的账户")
    response = requests.get(
        f"{BASE_URL}/accounts/random",
        headers=headers,
        params={"exclude_tags": "禁用", "page": 1, "page_size": 5}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 获取成功: 总数={data['total_accounts']}, 返回={len(data['accounts'])}条")
    else:
        print(f"❌ 获取失败: {response.status_code}")
    
    return True


def test_add_tag():
    """测试添加标签接口"""
    print("\n" + "=" * 60)
    print("测试3: 添加标签接口")
    print("=" * 60)
    
    api_key = get_api_key()
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    
    # 获取第一个账户用于测试
    response = requests.get(f"{BASE_URL}/accounts", headers={"X-API-Key": api_key})
    if response.status_code != 200 or not response.json().get('accounts'):
        print("❌ 没有可用的账户进行测试")
        return False
    
    test_email = response.json()['accounts'][0]['email_id']
    original_tags = response.json()['accounts'][0]['tags']
    print(f"测试账户: {test_email}")
    print(f"原始标签: {original_tags}")
    
    # 测试1: 添加新标签
    print("\n测试3.1: 添加新标签")
    new_tag = "自动测试标签"
    response = requests.post(
        f"{BASE_URL}/accounts/{test_email}/tags/add",
        headers=headers,
        json={"tag": new_tag}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 添加成功: {data['message']}")
        
        # 验证标签是否添加
        response = requests.get(f"{BASE_URL}/accounts", headers={"X-API-Key": api_key})
        accounts = response.json()['accounts']
        test_account = next((a for a in accounts if a['email_id'] == test_email), None)
        if test_account and new_tag in test_account['tags']:
            print(f"✓ 验证成功: 标签已添加 - {test_account['tags']}")
        else:
            print("❌ 验证失败: 标签未添加")
    else:
        print(f"❌ 添加失败: {response.status_code}")
        print(f"  响应: {response.text}")
        return False
    
    # 测试2: 重复添加相同标签（幂等性）
    print("\n测试3.2: 重复添加相同标签（测试幂等性）")
    response = requests.post(
        f"{BASE_URL}/accounts/{test_email}/tags/add",
        headers=headers,
        json={"tag": new_tag}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ 幂等性正确: {data['message']}")
    else:
        print(f"❌ 失败: {response.status_code}")
    
    # 测试3: 为不存在的账户添加标签
    print("\n测试3.3: 为不存在的账户添加标签")
    response = requests.post(
        f"{BASE_URL}/accounts/nonexistent@example.com/tags/add",
        headers=headers,
        json={"tag": "测试"}
    )
    
    if response.status_code == 404:
        print("✓ 正确返回404错误")
    else:
        print(f"❌ 应该返回404，实际返回: {response.status_code}")
    
    return True


def main():
    """运行所有测试"""
    print("开始测试新功能...")
    print(f"数据库文件: {DB_FILE}")
    print(f"API基础URL: {BASE_URL}")
    print()
    
    # 检查服务器是否运行
    try:
        response = requests.get(f"{BASE_URL}/api", timeout=2)
        print("✓ 服务器正在运行")
    except Exception as e:
        print(f"❌ 服务器未运行或无法访问: {e}")
        print("请先启动服务器: python main.py")
        return
    
    # 运行测试
    results = []
    
    results.append(("API Key认证", test_api_key_auth()))
    results.append(("随机获取邮箱", test_random_accounts()))
    results.append(("添加标签", test_add_tag()))
    
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


if __name__ == "__main__":
    main()

