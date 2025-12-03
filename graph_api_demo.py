import requests
from datetime import datetime

def get_accesstoken(refresh_token,client_id):
    data = {
        'client_id': client_id,
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'scope': 'https://graph.microsoft.com/.default'
    }
    return requests.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token', data=data).json()['access_token']

def Graph(refresh_token,client_id):
    try:
        access_token = get_accesstoken(refresh_token, client_id)
        if access_token == '':
            return []
        # url = "https://graph.microsoft.com/v1.0/me/messages" #获取全部邮件
        url ="https://graph.microsoft.com/v1.0/me/messages?$top=1&$orderby=receivedDateTime desc" #获取最新的一封邮件 
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            emails = response.json()["value"]
            print(emails)
            return emails
        else:
            print("请求失败:", response.status_code, response.text)
            return []
    except:
        return []


if __name__ == '__main__':
    client_id = '9e5f94bc-e8a4-4e73-b8be-63364c29d753' # 替换为你的client_id
    refresh_token = 'M.C514_BAY.0.U.-Cg5w3zEhhGlLTEsuqTa1p1LeEh2Sc*v43NV4*Nwpm9BCmuaXorNbbzE*hWcPrc0DVBqQ6RCl1jp7KQ2eV5I5rPziZ!4hNqPwVfvcjbKKZa9fBunEP8lgM4QI*OLmBL1Sh8vwLIPHSnrS3JI73E3LDb8xS9HMsHNERTG3ltZhQnyIqQrM6T1Gz*j4jrN*O1ndCvhRkmt1beArbtkY1DucU9PXj0p3kjzKmqYCyehAyaIeG2WZhbBn!YeW*2Jue5lBuEOV3lSpIcSpz2BdjCc4OBlsivi!O2HECQHXUuxqPxaDu7IAMhz5Fj!Z8L2EW99b9JvPoq227!AFNxc3EFA6LO*gPqXc1chYLvRj23pVelb1'  # 替换为你的refresh_token
    now = datetime.now()
    emails = Graph(refresh_token, client_id)
    time_used = datetime.now() - now
    print(f"时间: {time_used.total_seconds()}秒")
    if emails:
        for email in emails:
            print(f"主题: {email['subject']}")
            print(f"发件人: {email['from']['emailAddress']['address']}")
            print(f"内容预览: {email['bodyPreview']}\n")
