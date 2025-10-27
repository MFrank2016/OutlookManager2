#!/usr/bin/env python3
"""
Token刷新测试脚本

用于测试Microsoft OAuth2 Token刷新机制
验证响应是否返回新的 access_token 和 refresh_token
"""

import json
import httpx
from pathlib import Path


# OAuth2配置
TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
OAUTH_SCOPE = "https://outlook.office.com/IMAP.AccessAsUser.All offline_access"
ACCOUNTS_FILE = "accounts.json"


async def test_token_refresh():
    """测试Token刷新功能"""
    
    # 读取第一个账户的凭证
    try:
        accounts_path = Path(ACCOUNTS_FILE)
        if not accounts_path.exists():
            print(f"❌ 错误: 未找到 {ACCOUNTS_FILE} 文件")
            return
        
        with open(accounts_path, 'r', encoding='utf-8') as f:
            accounts = json.load(f)
        
        if not accounts:
            print("❌ 错误: accounts.json 中没有账户")
            return
        
        # 获取第一个账户
        email_id = list(accounts.keys())[0]
        account_data = accounts[email_id]
        
        print(f"📧 测试账户: {email_id}")
        print(f"🔑 Client ID: {account_data['client_id']}")
        print(f"🔄 Refresh Token: {account_data['refresh_token'][:50]}...")
        print("\n" + "="*60)
        
        # 构建Token刷新请求
        token_request_data = {
            'client_id': account_data['client_id'],
            'grant_type': 'refresh_token',
            'refresh_token': account_data['refresh_token'],
            'scope': OAUTH_SCOPE
        }
        
        print("🚀 发送Token刷新请求...")
        
        # 发送请求
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(TOKEN_URL, data=token_request_data)
            
            print(f"📡 响应状态码: {response.status_code}")
            print("\n" + "="*60)
            
            if response.status_code == 200:
                token_data = response.json()
                
                print("✅ Token刷新成功！\n")
                
                # 检查返回的字段
                has_access_token = 'access_token' in token_data
                has_refresh_token = 'refresh_token' in token_data
                has_expires_in = 'expires_in' in token_data
                
                print(f"📦 响应包含 access_token: {'✅' if has_access_token else '❌'}")
                print(f"📦 响应包含 refresh_token: {'✅' if has_refresh_token else '❌'}")
                print(f"📦 响应包含 expires_in: {'✅' if has_expires_in else '❌'}")
                
                print("\n" + "="*60)
                print("📄 完整响应数据:")
                print("="*60)
                
                # 打印完整的JSON响应（格式化）
                print(json.dumps(token_data, indent=2, ensure_ascii=False))
                
                print("\n" + "="*60)
                print("📄 响应字段详情 (敏感信息部分隐藏):")
                print("="*60)
                
                # 打印响应（敏感信息截断）
                for key, value in token_data.items():
                    if key in ['access_token', 'refresh_token']:
                        print(f"{key}: {value[:50]}... (长度: {len(value)})")
                    else:
                        print(f"{key}: {value}")
                
                # 验证结果
                print("\n" + "="*60)
                if has_access_token and has_refresh_token:
                    print("🎉 测试结果: 成功")
                    print("   - 新的 access_token 已获取")
                    print("   - 新的 refresh_token 已获取")
                    print("   - 可以更新到 accounts.json")
                    
                    # 显示是否需要更新
                    if token_data['refresh_token'] != account_data['refresh_token']:
                        print("\n⚠️  注意: refresh_token 已更改，建议更新到 accounts.json")
                    else:
                        print("\nℹ️  refresh_token 未改变")
                else:
                    print("⚠️  测试结果: 部分成功")
                    print("   - 缺少某些必要字段")
                
            else:
                print(f"❌ Token刷新失败")
                print(f"错误信息: {response.text}")
                
                try:
                    error_data = response.json()
                    print("\n错误详情:")
                    print(json.dumps(error_data, indent=2, ensure_ascii=False))
                except:
                    pass
    
    except FileNotFoundError as e:
        print(f"❌ 文件错误: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP错误: {e}")
    except httpx.RequestError as e:
        print(f"❌ 请求错误: {e}")
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    
    print("="*60)
    print("🔬 Microsoft OAuth2 Token 刷新测试")
    print("="*60)
    print()
    
    asyncio.run(test_token_refresh())
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

