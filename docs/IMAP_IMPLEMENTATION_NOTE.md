# IMAP实现说明

## 当前状态

当前的IMAP客户端实现是一个**占位版本**，用于演示系统的其他功能。

### 已实现的功能

✅ API路由正确配置（使用account_id）  
✅ OAuth2 token刷新机制正常工作  
✅ 数据库和账户管理正常  
✅ 前后端通信正常  

### 待完善的功能

⚠️ **IMAP邮件获取** - 当前返回空列表

## 为什么是占位实现？

Microsoft Outlook的IMAP OAuth2认证需要：

1. **XOAUTH2 SASL认证机制**
   - 需要正确实现Base64编码的认证字符串
   - 需要处理多步骤的SASL握手过程

2. **aioimaplib库的限制**
   - 标准的aioimaplib可能不直接支持XOAUTH2
   - 需要使用低级API或自定义实现

3. **Microsoft特定要求**
   - 可能需要特殊的认证流程
   - 需要正确的OAuth scopes和权限

## 如何完善IMAP实现？

### 方案1: 使用Microsoft Graph API（推荐）

Microsoft Graph API提供了更现代和稳定的方式访问邮件：

```python
# 使用 msgraph-sdk-python
from msgraph import GraphServiceClient
from azure.identity import ClientSecretCredential

# 创建客户端
credential = ClientSecretCredential(tenant_id, client_id, client_secret)
client = GraphServiceClient(credential)

# 获取邮件
messages = await client.me.messages.get()
```

**优点：**
- 官方支持，文档完善
- 更好的性能和稳定性
- 支持更多功能（日历、联系人等）
- 自动处理认证

### 方案2: 使用专门的OAuth IMAP库

使用支持OAuth2的IMAP库，如 `imapclient` + `oauthlib`：

```python
from imapclient import IMAPClient
from imapclient.config import create_default_config

# OAuth2认证
def generate_oauth2_string(email, access_token):
    return f"user={email}\x01auth=Bearer {access_token}\x01\x01"

# 连接并认证
client = IMAPClient('outlook.office365.com', ssl=True, use_uid=True)
client.oauth2_login(email, access_token)
```

### 方案3: 完善当前的aioimaplib实现

需要实现正确的XOAUTH2认证：

```python
import base64
import aioimaplib

async def oauth2_authenticate(client, email, access_token):
    auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
    auth_bytes = base64.b64encode(auth_string.encode('utf-8'))
    
    # 发送AUTHENTICATE命令
    await client.protocol.execute(
        aioimaplib.Command('AUTHENTICATE', 'XOAUTH2', auth_bytes, ...)
    )
```

## 测试IMAP连接

在完善实现后，可以使用以下方式测试：

```python
# 测试脚本
import asyncio
from src.infrastructure.external_services.imap import IMAPClientImpl
from src.domain.value_objects import EmailAddress, AccessToken

async def test_imap():
    client = IMAPClientImpl()
    email = EmailAddress.create("test@outlook.com")
    token = AccessToken("your-access-token")
    
    await client.connect(email, token)
    emails = await client.fetch_emails(EmailFolder.INBOX, limit=10)
    
    print(f"Found {len(emails)} emails")
    await client.disconnect()

asyncio.run(test_imap())
```

## 当前系统使用说明

尽管IMAP实现是占位版本，系统的其他功能都可以正常使用：

1. ✅ 登录/认证
2. ✅ 账户管理（添加、编辑、删除）
3. ✅ Token刷新
4. ✅ 管理员资料管理
5. ✅ 系统统计

邮件列表页面会显示"该文件夹暂无邮件"，这是预期行为。

## 参考资源

- [Microsoft Graph API文档](https://learn.microsoft.com/en-us/graph/api/overview)
- [OAuth 2.0 SASL for IMAP](https://developers.google.com/gmail/imap/xoauth2-protocol)
- [aioimaplib文档](https://aioimaplib.readthedocs.io/)
- [Microsoft Identity Platform](https://learn.microsoft.com/en-us/azure/active-directory/develop/)

## 联系

如需完整的IMAP实现，建议：
1. 使用Microsoft Graph API代替IMAP（最推荐）
2. 聘请有OAuth2 + IMAP经验的开发者
3. 参考其他开源项目的实现

---

**最后更新**: 2025-10-29  
**状态**: 占位实现，等待完善


