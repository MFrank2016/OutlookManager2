import requests


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
    client_id = 'dbc8e03a-b00c-46bd-ae65-b683e7707cb0' # 替换为你的client_id
    refresh_token = 'M.C554_BAY.0.U.-Ct25haXIig81gL8B7ZdAN3K9NM0jG8hIGa02t8htYSvGONPR2c1fOZ9j4DneVDyQ3DMdBy4jaaauu4T0cV*5t!GHi01*w7LkLqwu73EUYJBKv4cpL5ZsD*OUG*sQDFcKUriDcDBE00icBR!C7jbmdj4lGpLuVeImVxVrofypXSu1*AK7Vt4lgZo!bS5IW4ewuCXcSJWdtoax*n4mIa20Qo7pUVmnAQnWH1Z47M50h*vGmkZCOQWPCwE75nnR8qE99EVgBeyohLm0bVCoTUqg9Z1UBvRQiI*MIzTekvqAL!x6Lk5dz5j3Hg4lSO84xj7IGL!nCxbzJUObdE8JwiRhQNecv7HF7HMx0yUGTYiszxMN'  # 替换为你的refresh_token
    emails = Graph(refresh_token, client_id)
    if emails:
        for email in emails:
            print(f"主题: {email['subject']}")
            print(f"发件人: {email['from']['emailAddress']['address']}")
            print(f"内容预览: {email['bodyPreview']}\n")

