import requests
import json

# 配置 token 和 header
access_token = "EwBYBMl6BAAUBKgm8k1UswUNwklmy2v7U/S+1fEAAfn1egrMO/gIFdxadvy8Zd7KYuTIeWmXKn0bm/hIHCYumEuvF/SQQs9KyXyaEI0M1ici3mejMA3Zf0LqlcRcuc+dqKE+udLjdT2RJ1PzoxyVQ6VNg0JClI+jj+TDyEcjRfCCUE90qOj+dOZ7cDLKC8jEOyFtiPZF4AIVQYBLiBsi6/2AfYDtS6iXR3UoQ8eK8BVtvQsexQmR7+JBcgHX+875Id3mzKBomwsStB0ePDpq8ww3tinHPEn3ipT3tN14ENbiCv5ugeUWndjPKWhAHQtSw1ZgB7lXDvaDHRxTYpKXQqOKAHiBVC4mCSPMmYiMoJn5zSlfyHKHCXn8tgjFT1sQZgAAEK798/tCJzszfkmNUctEl3wgA2hb3lFm++H41Ay0KfRzi27Nk7t41iVv4w/yptv8K5VEerpUi28zzfWH8JSbI05gUArzGA6mIkLAu4WFuU9khNohve14FZJO/f2TNFpSjvOrr9roA8RX3/497KJIv7Il6sSWboxx40D/TwQrJ8kTfO5JpjzICnJt2zqhtXbfcOw3k5OH+tGUnpEfYeD8ADfm/ZgPhl3nkmQaQ6onlDaDvUOR1zhGYzbzycqMHI3FRILunN7RPO4aT268JymQ8Dd4Ocoq6SfMu+RBRRLK5lVXGj/fYNdHgg1NyPCUpdSQst7fBn9IrQPsFb14NQ0IPKDOk0DQGGfJFFFqKxqIxW03CR0zlnLAcG8jfcQNsVy9m8Vp2LkcwrZg4hIHbhRpimxg5e7lHNsezSozUMtBqy4+EC9ilJrV/b8aaIf6XyM2HNORdrt+sHSoxaM3Hi+giUaMTQncInsSR47gxddqqUo9nvPA9dfMGXIanBqK6mSqmtJBcMmeO+IIKtvWuk6aPqWoWyFHVTfJ2np84Dnwb23M8rD12Q4eTl9znircLJWQYBPC0eVeLtXaezPQRjiOGT/ZNX0Yi41tHBFH0UckklchpsMc293kzdSANW8sal84fYbQDmdOK4uZpfoReSYesYgzFmh+qCk7BcIZPNa6n4CNK44QBvTAsK1pY6cPV5a5YFI5/I/HmC8jxMdddM5Xy0WbhsVCkDyGuO4M8razaMtUwB7HFjwf5ez1KngEKnbm/7/6ag/Nqel4Njz02D9XRjDK+qfBhHv1NDI8UWdEDWFzH9A/o5vV9hjJLNtwrmzo1cQ5L/n/SG0IekRUcEzsF1XSt1ZV1xNlZ4WSHwDVQxCQdwmum2TCe7WVFtR2RUcLbTKJzre+FC710rhDouFfKU3Ax8DsPq7Ez5BJR+0vM51M4iD+A87QWmbifw3/cMUFSgmXmwrhkpG4d6FnnN5tbZmDL0RsS84J8ZvLeH87xHJqTg5jgPy3W3nKKVFUlmYYhxzG6lRWP4jVH//muuhlPn1sTbjvA3+i7nFAt3fA0nY+hHDFy3l6kWV0r01Z5MHaoBrKcAM="
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

def clear_inbox():
    # 1. 获取邮件列表（仅获取ID）
    # 注意：实际生产中需要处理翻页 (@odata.nextLink)，这里简化为只取前100封
    # list_url = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages?$select=id&$top=100"

    list_url = "https://graph.microsoft.com/v1.0/me/messages?$select=id&$top=100"
    
    response = requests.get(list_url, headers=headers)
    messages = response.json().get('value', [])
    
    if not messages:
        print("收件箱已空")
        return

    # 2. 分批删除（Graph API 限制每次 batch 最多 20 个请求）
    batch_size = 20
    for i in range(0, len(messages), batch_size):
        batch_chunk = messages[i:i + batch_size]
        
        batch_payload = {
            "requests": []
        }
        
        # 构建 batch 请求体
        for index, msg in enumerate(batch_chunk):
            batch_payload["requests"].append({
                "id": str(index), # 这里的 id 是请求的序号，不是邮件 ID
                "method": "DELETE",
                "url": f"/me/messages/{msg['id']}"
            })
            
        # 发送删除请求
        batch_url = "https://graph.microsoft.com/v1.0/$batch"
        del_resp = requests.post(batch_url, headers=headers, json=batch_payload)
        
        if del_resp.status_code == 200:
            print(f"成功处理了一批邮件: {len(batch_chunk)} 封")
        else:
            print(f"删除失败: {del_resp.text}")

# 执行
clear_inbox()