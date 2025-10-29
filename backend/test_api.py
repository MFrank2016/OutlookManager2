#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API端点测试脚本

测试所有16个API端点的功能
"""

import sys
import io

# 设置标准输出编码为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import json
import time
from typing import Dict, List, Optional
from datetime import datetime

import httpx

# 配置
BASE_URL = "http://localhost:8000"
TIMEOUT = 10.0

# 测试结果
test_results: List[Dict] = []
total_tests = 0
passed_tests = 0
failed_tests = 0


def print_header(text: str):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_test(name: str, status: str, message: str = ""):
    """打印测试结果"""
    global total_tests, passed_tests, failed_tests
    
    total_tests += 1
    if status == "PASS":
        passed_tests += 1
        symbol = "✅"
    else:
        failed_tests += 1
        symbol = "❌"
    
    print(f"{symbol} {name}: {status}")
    if message:
        print(f"   {message}")
    
    test_results.append({
        "name": name,
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })


def test_health_check():
    """测试健康检查端点"""
    print_header("1. 健康检查端点")
    
    try:
        response = httpx.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_test("GET /health", "PASS", f"状态: {data.get('status')}")
        else:
            print_test("GET /health", "FAIL", f"状态码: {response.status_code}")
    except Exception as e:
        print_test("GET /health", "FAIL", str(e))


def test_auth_endpoints(admin_token: Optional[str] = None) -> Optional[str]:
    """测试认证端点"""
    print_header("2. 认证端点")
    
    token = None
    
    # 2.1 登录
    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print_test(
                "POST /api/v1/auth/login",
                "PASS",
                f"Token获取成功 (长度: {len(token) if token else 0})"
            )
        else:
            print_test(
                "POST /api/v1/auth/login",
                "FAIL",
                f"状态码: {response.status_code}, 响应: {response.text[:100]}"
            )
    except Exception as e:
        print_test("POST /api/v1/auth/login", "FAIL", str(e))
    
    if not token:
        print("⚠️  无法获取Token，跳过需要认证的测试")
        return None
    
    # 2.2 验证Token
    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/auth/verify-token",
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            print_test("POST /api/v1/auth/verify-token", "PASS")
        else:
            print_test(
                "POST /api/v1/auth/verify-token",
                "FAIL",
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("POST /api/v1/auth/verify-token", "FAIL", str(e))
    
    # 2.3 修改密码（跳过，避免影响测试账户）
    print_test(
        "POST /api/v1/auth/change-password",
        "SKIP",
        "跳过以避免修改测试账户密码"
    )
    
    return token


def test_account_endpoints(token: str):
    """测试账户管理端点"""
    print_header("3. 账户管理端点")
    
    headers = {"Authorization": f"Bearer {token}"}
    account_id = None
    
    # 清理已有的测试账户
    try:
        response = httpx.get(
            f"{BASE_URL}/api/v1/accounts",
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            accounts = response.json().get("items", [])  # 修复：使用items而不是data
            for account in accounts:
                if account.get("email") == "test@outlook.com":
                    httpx.delete(
                        f"{BASE_URL}/api/v1/accounts/{account['id']}",
                        headers=headers,
                        timeout=TIMEOUT
                    )
    except:
        pass  # 忽略清理错误
    
    # 3.1 创建账户
    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/accounts",
            headers=headers,
            json={
                "email": "test@outlook.com",
                "refresh_token": "test_refresh_token",
                "client_id": "test_client_id",
                "tags": ["test"]
            },
            timeout=TIMEOUT
        )
        if response.status_code in [200, 201]:
            data = response.json()
            account_id = data.get("id")
            print_test(
                "POST /api/v1/accounts",
                "PASS",
                f"账户创建成功 (ID: {account_id})"
            )
        else:
            print_test(
                "POST /api/v1/accounts",
                "FAIL",
                f"状态码: {response.status_code}, 响应: {response.text[:100]}"
            )
    except Exception as e:
        print_test("POST /api/v1/accounts", "FAIL", str(e))
    
    # 3.2 获取账户列表
    try:
        response = httpx.get(
            f"{BASE_URL}/api/v1/accounts",
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            count = data.get("total", 0)
            print_test(
                "GET /api/v1/accounts",
                "PASS",
                f"返回 {count} 个账户"
            )
        else:
            print_test(
                "GET /api/v1/accounts",
                "FAIL",
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("GET /api/v1/accounts", "FAIL", str(e))
    
    if not account_id:
        print("⚠️  无可用账户ID，跳过后续账户测试")
        return
    
    # 3.3 获取账户详情
    try:
        response = httpx.get(
            f"{BASE_URL}/api/v1/accounts/{account_id}",
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            print_test("GET /api/v1/accounts/{id}", "PASS")
        else:
            print_test(
                "GET /api/v1/accounts/{id}",
                "FAIL",
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("GET /api/v1/accounts/{id}", "FAIL", str(e))
    
    # 3.4 更新账户
    try:
        response = httpx.put(
            f"{BASE_URL}/api/v1/accounts/{account_id}",
            headers=headers,
            json={"tags": ["updated", "test"]},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            print_test("PUT /api/v1/accounts/{id}", "PASS")
        else:
            print_test(
                "PUT /api/v1/accounts/{id}",
                "FAIL",
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("PUT /api/v1/accounts/{id}", "FAIL", str(e))
    
    # 3.5 刷新Token（预期会失败，因为是测试token）
    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/accounts/{account_id}/refresh-token",
            headers=headers,
            timeout=TIMEOUT
        )
        # 预期失败，因为是测试数据
        print_test(
            "POST /api/v1/accounts/{id}/refresh-token",
            "TESTED",
            f"状态码: {response.status_code} (预期失败)"
        )
    except Exception as e:
        print_test(
            "POST /api/v1/accounts/{id}/refresh-token",
            "TESTED",
            "预期异常（测试数据）"
        )
    
    # 3.6 删除账户
    try:
        response = httpx.delete(
            f"{BASE_URL}/api/v1/accounts/{account_id}",
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code in [200, 204]:  # 204 No Content is also success
            print_test("DELETE /api/v1/accounts/{id}", "PASS")
        else:
            print_test(
                "DELETE /api/v1/accounts/{id}",
                "FAIL",
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("DELETE /api/v1/accounts/{id}", "FAIL", str(e))


def test_email_endpoints(token: str):
    """测试邮件管理端点"""
    print_header("4. 邮件管理端点")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 使用一个假的account_id（预期会失败或返回空）
    test_account_id = "00000000-0000-0000-0000-000000000000"
    
    # 4.1 获取邮件列表
    try:
        response = httpx.get(
            f"{BASE_URL}/api/v1/emails/{test_account_id}",
            headers=headers,
            params={"folder": "INBOX"},
            timeout=TIMEOUT
        )
        print_test(
            "GET /api/v1/emails/{account_id}",
            "TESTED",
            f"状态码: {response.status_code} (测试账户不存在)"
        )
    except Exception as e:
        print_test(
            "GET /api/v1/emails/{account_id}",
            "TESTED",
            "预期异常（测试账户）"
        )
    
    # 4.2 获取邮件详情
    try:
        response = httpx.get(
            f"{BASE_URL}/api/v1/emails/{test_account_id}/test-message-id",
            headers=headers,
            timeout=TIMEOUT
        )
        print_test(
            "GET /api/v1/emails/{account_id}/{message_id}",
            "TESTED",
            f"状态码: {response.status_code} (测试数据)"
        )
    except Exception as e:
        print_test(
            "GET /api/v1/emails/{account_id}/{message_id}",
            "TESTED",
            "预期异常（测试数据）"
        )
    
    # 4.3 搜索邮件
    try:
        response = httpx.post(
            f"{BASE_URL}/api/v1/emails/{test_account_id}/search",
            headers=headers,
            json={"query": "test"},
            timeout=TIMEOUT
        )
        print_test(
            "POST /api/v1/emails/{account_id}/search",
            "TESTED",
            f"状态码: {response.status_code} (测试数据)"
        )
    except Exception as e:
        print_test(
            "POST /api/v1/emails/{account_id}/search",
            "TESTED",
            "预期异常（测试数据）"
        )


def test_admin_endpoints(token: str):
    """测试管理员端点"""
    print_header("5. 管理员端点")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 5.1 获取管理员资料
    try:
        response = httpx.get(
            f"{BASE_URL}/api/v1/admin/profile",
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/v1/admin/profile",
                "PASS",
                f"用户名: {data.get('username')}"
            )
        else:
            print_test(
                "GET /api/v1/admin/profile",
                "FAIL",
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("GET /api/v1/admin/profile", "FAIL", str(e))
    
    # 5.2 更新管理员资料
    try:
        response = httpx.put(
            f"{BASE_URL}/api/v1/admin/profile",
            headers=headers,
            json={"email": "admin@example.com"},
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            print_test("PUT /api/v1/admin/profile", "PASS")
        else:
            print_test(
                "PUT /api/v1/admin/profile",
                "FAIL",
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("PUT /api/v1/admin/profile", "FAIL", str(e))
    
    # 5.3 获取系统统计
    try:
        response = httpx.get(
            f"{BASE_URL}/api/v1/admin/stats",
            headers=headers,
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            print_test(
                "GET /api/v1/admin/stats",
                "PASS",
                f"账户数: {data.get('total_accounts', 0)}"
            )
        else:
            print_test(
                "GET /api/v1/admin/stats",
                "FAIL",
                f"状态码: {response.status_code}"
            )
    except Exception as e:
        print_test("GET /api/v1/admin/stats", "FAIL", str(e))


def generate_report():
    """生成测试报告"""
    print_header("测试总结")
    
    print(f"\n总测试数: {total_tests}")
    print(f"✅ 通过: {passed_tests}")
    print(f"❌ 失败: {failed_tests}")
    print(f"⚠️  其他: {total_tests - passed_tests - failed_tests}")
    
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    print(f"\n成功率: {success_rate:.1f}%")
    
    # 保存详细报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate
        },
        "tests": test_results
    }
    
    with open("api_test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细报告已保存到: api_test_report.json")
    
    if failed_tests > 0:
        print("\n⚠️  存在失败的测试，请检查详细报告")
        return 1
    else:
        print("\n🎉 所有测试通过！")
        return 0


def main():
    """主函数"""
    print_header("OutlookManager v3.0 - API测试")
    print(f"目标: {BASE_URL}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 等待服务器启动
    print("\n⏳ 等待服务器启动...")
    time.sleep(5)
    
    # 1. 健康检查
    test_health_check()
    
    # 2. 认证端点
    token = test_auth_endpoints()
    
    if not token:
        print("\n❌ 无法获取认证Token，停止测试")
        return 1
    
    # 3. 账户管理端点
    test_account_endpoints(token)
    
    # 4. 邮件管理端点
    test_email_endpoints(token)
    
    # 5. 管理员端点
    test_admin_endpoints(token)
    
    # 生成报告
    return generate_report()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

