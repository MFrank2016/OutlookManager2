# 前端 Docker 部署说明

## 问题排查

如果前端服务没有启动，请按以下步骤排查：

### 1. 检查构建日志

```bash
# 查看前端服务构建日志
docker compose build outlook-email-frontend 2>&1 | tee frontend-build.log

# 查看是否有错误
grep -i error frontend-build.log
```

### 2. 检查容器状态

```bash
# 查看所有容器（包括已停止的）
docker compose ps -a

# 查看前端容器日志
docker compose logs outlook-email-frontend

# 如果容器已创建但未运行，查看退出代码
docker compose ps -a | grep frontend
```

### 3. 手动测试构建

```bash
# 手动构建前端镜像
docker build -f docker/Dockerfile.frontend -t outlook-email-frontend:test .

# 查看构建过程中的错误
docker build -f docker/Dockerfile.frontend -t outlook-email-frontend:test . 2>&1 | tee build.log
```

### 4. 检查 standalone 输出

如果构建成功但启动失败，可能是 standalone 输出结构问题：

```bash
# 进入构建容器检查结构
docker run --rm -it outlook-email-frontend:test sh
# 然后执行：
# ls -la /app
# ls -la /app/frontend 2>/dev/null || echo "frontend dir not found"
# find /app -name "server.js"
```

### 5. 常见问题

#### 问题：构建失败 - npm ci 错误

**解决**：确保 `frontend/package-lock.json` 存在且是最新的

```bash
cd frontend
npm install
```

#### 问题：构建失败 - Next.js build 错误

**解决**：检查 `next.config.ts` 配置，确保 `output: "standalone"` 已设置

#### 问题：容器启动后立即退出

**解决**：查看日志，通常是找不到 `server.js` 文件

```bash
docker compose logs outlook-email-frontend
```

#### 问题：端口已被占用

**解决**：修改 `FRONTEND_PORT` 环境变量或停止占用 3000 端口的服务

```bash
# 检查端口占用
lsof -i :3000
# 或
netstat -tulpn | grep 3000
```

## 快速修复

如果遇到问题，可以尝试：

```bash
# 1. 停止所有服务
docker compose down

# 2. 清理构建缓存
docker compose build --no-cache outlook-email-frontend

# 3. 重新启动
docker compose up -d --build

# 4. 查看日志
docker compose logs -f outlook-email-frontend
```
