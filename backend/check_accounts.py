# -*- coding: utf-8 -*-
import httpx
import json

# 登录
login_resp = httpx.post(
    "http://localhost:8000/api/v1/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = login_resp.json().get("access_token")

# 获取账户列表
accounts_resp = httpx.get(
    "http://localhost:8000/api/v1/accounts",
    headers={"Authorization": f"Bearer {token}"}
)

print("账户列表API响应结构:")
print(json.dumps(accounts_resp.json(), indent=2, ensure_ascii=False))

