import imaplib
import requests
import base64
import sys

# ================= 配置区域 =================
# 你的 Azure App Client ID
CLIENT_ID = "9e5f94bc-e8a4-4e73-b8be-63364c29d753"

# 如果你的应用是 Web App (Confidential Client)，需要 Client Secret。
# 如果是 Public Client (如手机/桌面App)，通常不需要，设为 None 即可。
CLIENT_SECRET = None 

# 你的 Refresh Token
REFRESH_TOKEN = "M.C546_SN1.0.U.-Cs5ZT5Q6PNDzrP*0thQJFb3MU9SHWe0nFyByzQ9kZq4ReDwsVssRiLin5OjP69EzNbsPxFBJA6XsGRfLJ4lGKYTkF9NySZHI5!sfhoPQgQSyYxtNopQfsG0l9xw3CM5Pz0TwFrjFkmJmdK2appzqoHLRDuIoxrmgdUAh4ANiMoaS8tnZE7d5TQbhIlSE5D6ar7Aqg80xzOl0b70tqQLPdNs4vqav!kSGZVf*o54YSm!jKADl97F7Borfk2AR!p4BzsRcELXqEj*dXJA2ZHB!7UczNZFXAiP2Zq3fZyHL093OhNPEVrX6n86wP!SpVMJDDUcLDrh60lyqh9X6Jt34vdTmtbJwiMaoWbwqRu6CaJpaCCXGjl6CodtM7!Y3OyxLKw$$"

# 你的邮箱地址 (必须与 Token 归属账号一致)
EMAIL_ADDRESS = "LornaBuckridge6967@outlook.com"

# 微软 OAuth2 Token 端点
TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
# ===========================================

def get_access_token():
    """
    使用 Refresh Token 换取新的 Access Token
    """
    data = {
        'client_id': CLIENT_ID,
        'refresh_token': REFRESH_TOKEN,
        'grant_type': 'refresh_token',
        # scope 必须包含 IMAP 权限，通常 Refresh Token 申请时已包含，此处可不填或填默认
        'scope': 'https://outlook.office.com/IMAP.AccessAsUser.All'
    }
    
    if CLIENT_SECRET:
        data['client_secret'] = CLIENT_SECRET

    try:
        response = requests.post(TOKEN_URL, data=data)
        response.raise_for_status()
        tokens = response.json()
        print("[+] 成功获取 Access Token")
        return tokens['access_token']
    except Exception as e:
        print(f"[-] 获取 Access Token 失败: {e}")
        if 'response' in locals():
            print(f"[-] 服务器返回: {response.text}")
        sys.exit(1)

def generate_auth_string(user, token):
    """
    生成 IMAP XOAUTH2 认证字符串
    格式: user={user}^Aauth=Bearer {token}^A^A
    """
    auth_string = f"user={user}\x01auth=Bearer {token}\x01\x01"
    return auth_string

def clear_inbox():
    # 1. 获取 Access Token
    access_token = get_access_token()

    # 2. 连接 Outlook IMAP 服务器
    try:
        imap = imaplib.IMAP4_SSL("outlook.office365.com", 993)
        # 调试模式，设为 True 可以看到详细交互日志
        imap.debug = 4 
    except Exception as e:
        print(f"[-] 连接 IMAP 服务器失败: {e}")
        return

    # 3. 进行 OAuth2 认证
    try:
        # imaplib 的 authenticate 方法需要一个生成器函数，或者我们手动处理
        # 这里使用标准方法，传递 XOAUTH2 机制
        imap.authenticate('XOAUTH2', lambda x: generate_auth_string(EMAIL_ADDRESS, access_token))
        print(f"[+] 邮箱 {EMAIL_ADDRESS} 登录成功")
    except imaplib.IMAP4.error as e:
        print(f"[-] 认证失败，请检查邮箱地址或 Scope 权限: {e}")
        return

    # 4. 选择收件箱 (INBOX)
    # select 返回由 ('OK', [b'数量']) 组成的元组
    status, messages = imap.select('INBOX')
    if status != 'OK':
        print("[-] 无法打开收件箱")
        return
    
    total_emails = int(messages[0])
    print(f"[+] 收件箱共有 {total_emails} 封邮件")

    if total_emails == 0:
        print("[+] 收件箱为空，无需清理")
        imap.logout()
        return

    # 5. 搜索所有邮件
    # search(charset, criterion)
    status, data = imap.search(None, 'ALL')
    
    if status != 'OK':
        print("[-] 搜索邮件失败")
        return

    email_ids = data[0].split()
    print(f"[+] 准备删除 {len(email_ids)} 封邮件...")

    # 6. 批量标记删除
    # 将 ID 列表转换为逗号分隔的字符串，以提高效率 (如果数量极大，建议分批处理)
    # 注意：imaplib 接收 bytes 或 str，通常建议使用 batch 方式
    
    batch_size = 100 # 每次处理 100 封，防止请求过长
    id_list = [i.decode('utf-8') for i in email_ids]
    
    for i in range(0, len(id_list), batch_size):
        batch = id_list[i:i + batch_size]
        batch_ids = ','.join(batch)
        
        #store 命令用于修改标记，+FLAGS \Deleted 表示添加删除标记
        typ, response = imap.store(batch_ids, '+FLAGS', '\\Deleted')
        print(f"    - 已标记 {len(batch)} 封邮件 (进度: {min(i + batch_size, len(id_list))}/{len(id_list)})")

    # 7. 执行永久删除 (Expunge)
    # 这一步会将带 \Deleted 标记的邮件移除收件箱（通常是移动到“已删除邮件”文件夹）
    imap.expunge()
    print("[+] 清理完成 (Expunge 执行完毕)")

    # 8. 关闭连接
    imap.close()
    imap.logout()

if __name__ == "__main__":
    clear_inbox()