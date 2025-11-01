# ⏰ 时区问题快速修复

## 🚨 问题现象

- 容器显示：上午 9 点
- 实际时间：下午 5 点（东 8 区）
- 时差：8 小时

## ✅ 快速解决（3 步）

### 方法 1：一键修复（推荐）

```bash
# 在服务器上运行
cd /path/to/OutlookManager2
chmod +x scripts/fix_timezone.sh
bash scripts/fix_timezone.sh
```

### 方法 2：手动修复

```bash
# 1. 停止容器
docker-compose down

# 2. 重新构建
docker-compose build --no-cache

# 3. 启动容器
docker-compose up -d
```

### 方法 3：验证配置

```bash
# 检查时区是否正确
docker exec outlook-email-api date

# 应该显示类似：
# Sat Nov  1 17:00:00 CST 2025
```

## 📋 验证清单

运行验证脚本：

```bash
chmod +x scripts/verify_timezone.sh
bash scripts/verify_timezone.sh
```

手动验证：

```bash
# ✓ 容器时间
docker exec outlook-email-api date

# ✓ 时区变量
docker exec outlook-email-api sh -c 'echo $TZ'
# 应该显示: Asia/Shanghai

# ✓ Python时间
docker exec outlook-email-api python -c "import datetime; print(datetime.datetime.now())"
# 应该显示东8区时间
```

## 🔧 前端显示不对？

1. **清除浏览器缓存**
2. **硬刷新页面**：
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`
3. **重新登录**

## 📚 详细文档

- 完整指南：`docs/时区配置指南.md`
- 更新说明：`docs/时区配置更新说明.md`
- Docker 部署：`docs/Docker部署说明.md`

## 💡 配置说明

已修改的文件：

- ✅ `docker-compose.yml` - 添加时区环境变量和卷挂载
- ✅ `docker/Dockerfile` - 添加时区设置

配置内容：

```yaml
# docker-compose.yml
environment:
  - TZ=Asia/Shanghai
volumes:
  - /etc/localtime:/etc/localtime:ro
  - /etc/timezone:/etc/timezone:ro
```

```dockerfile
# Dockerfile
ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone
```

## ❓ 仍有问题？

1. 查看容器日志：`docker-compose logs -f`
2. 查看应用日志：`tail -f logs/outlook_manager.log`
3. 运行验证脚本：`bash scripts/verify_timezone.sh`
4. 参考详细文档：`docs/时区配置指南.md`

---

**快速修复完成后，记得清除浏览器缓存！**
