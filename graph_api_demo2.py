import requests
from datetime import datetime

def get_accesstoken(refresh_token, client_id):
    url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
    data = {
        'client_id': client_id,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'scope': 'https://graph.microsoft.com/.default'
    }
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"获取Token失败: {response.text}")
            return ""
    except Exception as e:
        print(f"网络请求异常: {e}")
        return ""

def Graph(refresh_token, client_id):
    try:
        access_token = get_accesstoken(refresh_token, client_id)
        if not access_token:
            return []

        url = "https://graph.microsoft.com/v1.0/me/messages"
        
        # === 终极修复方案：使用 $search (KQL) ===
        # 语法说明：
        # 1. 发件人: "from:邮箱"
        # 2. 主题: "subject:关键词"
        # 3. 组合: "from:邮箱 AND subject:关键词"
        
        search_query = '"from:qiuyingjia2019"'
        search_query = '"(from/emailAddress/address) eq \'qiuyingjia2019@gmail.com\'"'
        # 如果需要同时查主题，取消下面这行的注释：
        # search_query = '"from:qiuyingjia2019@gmail.com AND subject:invoice"'

        params = {
            # "$filter": search_query,
            # "$search": "12",
            "$top": 10,
            "$select": "subject,from,bodyPreview,receivedDateTime",
            # 注意：使用 $search 时，通常不需要 $orderby，也不支持复杂的 $filter
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            # 虽然 $search 本身支持最终一致性，但带上这个头是个好习惯
            "ConsistencyLevel": "eventual" 
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            emails = response.json().get("value", [])
            return emails
        else:
            print("请求失败:", response.status_code, response.text)
            return []
            
    except Exception as e:
        print(f"发生代码异常: {e}")
        return []

if __name__ == '__main__':
    client_id = '9e5f94bc-e8a4-4e73-b8be-63364c29d753' 
    refresh_token = 'M.C514_BAY.0.U.-Cg5w3zEhhGlLTEsuqTa1p1LeEh2Sc*v43NV4*Nwpm9BCmuaXorNbbzE*hWcPrc0DVBqQ6RCl1jp7KQ2eV5I5rPziZ!4hNqPwVfvcjbKKZa9fBunEP8lgM4QI*OLmBL1Sh8vwLIPHSnrS3JI73E3LDb8xS9HMsHNERTG3ltZhQnyIqQrM6T1Gz*j4jrN*O1ndCvhRkmt1beArbtkY1DucU9PXj0p3kjzKmqYCyehAyaIeG2WZhbBn!YeW*2Jue5lBuEOV3lSpIcSpz2BdjCc4OBlsivi!O2HECQHXUuxqPxaDu7IAMhz5Fj!Z8L2EW99b9JvPoq227!AFNxc3EFA6LO*gPqXc1chYLvRj23pVelb1'
    
    now = datetime.now()
    emails = Graph(refresh_token, client_id)
    time_used = datetime.now() - now
    
    print(f"耗时: {time_used.total_seconds()}秒")
    print(f"找到邮件数量: {len(emails)}")
    
    if emails:
        for email in emails:
            print(f"主题: {email.get('subject')}")
            print(f"时间: {email.get('receivedDateTime')}") # 打印时间确认排序
            sender = email.get('from', {}).get('emailAddress', {}).get('address', 'Unknown')
            print(f"发件人: {sender}")
            # print(f"email: {email}")
            print("-" * 30)