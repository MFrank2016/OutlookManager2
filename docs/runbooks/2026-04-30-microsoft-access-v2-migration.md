# Microsoft Access v2 迁移 Runbook

更新时间：2026-04-30

## 目标

这份 runbook 用来回答三件事：

1. `v1` 和 `v2` 现在到底有什么区别
2. 批量导入该怎么先 `dry_run` 再 `commit`
3. 遇到 Graph / IMAP 读写异常时，如何用 override 排障

## 一、v1 vs v2

### v1

旧入口仍然保留，例如：

- `/accounts`
- `/emails`

这些路由现在已经是**兼容层**，内部会转发到统一的 Microsoft Access Layer。

兼容期内，`v1` 响应会带：

- `Deprecation: true`
- `Sunset: Wed, 31 Dec 2026 23:59:59 GMT`

### v2

新入口统一在 `/api/v2` 下：

- `POST /api/v2/accounts/probe`
- `GET /api/v2/accounts/{email}/health`
- `GET /api/v2/accounts/{email}/delivery-strategy`
- `GET /api/v2/accounts/{email}/messages`
- `POST /api/v2/accounts/import`

`v2` 的核心优势不是“换了路径”，而是：

- 直接暴露 capability / health / strategy 语义
- 支持 `override_provider`、`strategy_mode`、`skip_cache`
- 更适合排障、自动化与后续前端默认切换

## 二、批量导入：先 dry run，再 commit

### 1. dry run

先做不落库预检：

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/accounts/import?mode=dry_run" \
  -H 'Content-Type: application/json' \
  -d '{
    "api_method": "imap",
    "tags": ["seed"],
    "items": [
      {
        "email": "user@example.com",
        "refresh_token": "refresh-token",
        "client_id": "client-id"
      }
    ]
  }'
```

你应该重点看：

- `success_count`
- `failed_count`
- 每个 item 的 `message`

### 2. commit

确认 dry run 没问题后，再正式导入：

```bash
curl -X POST "http://127.0.0.1:8000/api/v2/accounts/import?mode=commit" \
  -H 'Content-Type: application/json' \
  -d '{
    "api_method": "imap",
    "tags": ["seed"],
    "items": [
      {
        "email": "user@example.com",
        "refresh_token": "refresh-token",
        "client_id": "client-id"
      }
    ]
  }'
```

重点确认：

- `persisted_count > 0`
- 返回项里 `persisted: true`

## 三、override 排障

### 1. 先看 health

```bash
curl http://127.0.0.1:8000/api/v2/accounts/user%40example.com/health
```

关注：

- `strategy_mode`
- `last_provider_used`
- `capability`
- `last_error`

### 2. 再看 delivery-strategy

```bash
curl "http://127.0.0.1:8000/api/v2/accounts/user%40example.com/delivery-strategy?override_provider=graph&skip_cache=true"
```

重点确认：

- `recommended_provider`
- `resolved_provider`
- `provider_order`
- `override_active`

### 3. 直接用 messages 验证

强制 Graph：

```bash
curl "http://127.0.0.1:8000/api/v2/accounts/user%40example.com/messages?override_provider=graph&skip_cache=true"
```

强制 IMAP：

```bash
curl "http://127.0.0.1:8000/api/v2/accounts/user%40example.com/messages?override_provider=imap&skip_cache=true"
```

如果：

- Graph 失败、IMAP 成功：说明 Graph read 能力或 token/scope 有问题
- Graph 成功、IMAP 失败：说明 IMAP 可用性或 provider 路径有问题
- 两边都失败：优先回到 `health` 和 `probe` 看 token / capability

## 四、推荐迁移顺序

1. 新脚本、新页面、新联调入口优先直接接 `/api/v2`
2. 旧脚本在兼容期内保持可用，但逐步切离 `/accounts`、`/emails`
3. 到 `2026-12-31 23:59:59 GMT` 前，完成主要调用方迁移

## 五、完成定义

一次迁移可以认为合格，至少要满足：

- `probe` 可返回能力建议
- `dry_run import` 不落库且结果可读
- `commit import` 可真正写入
- `health` / `delivery-strategy` 能解释当前 provider 选择
- 必要时能用 `override_provider + skip_cache` 复现实验
