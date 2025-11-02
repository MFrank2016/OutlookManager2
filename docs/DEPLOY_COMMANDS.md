# 🚀 Docker部署命令速查表

## 📦 初次部署

```bash
# 1. 克隆项目（如果还没有）
git clone <repository-url>
cd OutlookManager2

# 2. 构建并启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 验证时区
bash scripts/verify_timezone.sh
```

## ⏰ 时区修复

### 快速修复
```bash
bash scripts/fix_timezone.sh
```

### 手动修复
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 验证时区
```bash
# 方法1：使用验证脚本
bash scripts/verify_timezone.sh

# 方法2：手动检查
docker exec outlook-email-api date
docker exec outlook-email-api sh -c 'echo $TZ'
```

## 🔄 更新部署

### 更新代码并重新构建
```bash
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 仅重启容器（代码未变）
```bash
docker-compose restart
```

### 查看更新后的日志
```bash
docker-compose logs -f --tail=100
```

## 📊 监控和管理

### 查看容器状态
```bash
docker-compose ps
docker ps | grep outlook
```

### 查看容器日志
```bash
# 实时日志
docker-compose logs -f

# 最近100行
docker-compose logs --tail=100

# 特定时间范围
docker-compose logs --since 30m
```

### 查看应用日志
```bash
tail -f logs/outlook_manager.log
tail -100 logs/outlook_manager.log
```

### 进入容器
```bash
docker exec -it outlook-email-api sh
```

### 容器内常用命令
```bash
# 在容器内执行
date                                    # 查看时间
echo $TZ                               # 查看时区变量
cat /etc/timezone                      # 查看时区文件
python -c "import datetime; print(datetime.datetime.now())"  # Python时间
ls -lh /app                           # 查看应用文件
ps aux                                # 查看进程
```

## 🗄️ 数据管理

### 备份数据库
```bash
# 创建备份目录
mkdir -p backups

# 备份数据库
cp data.db backups/data.db.$(date +%Y%m%d_%H%M%S)

# 或从容器中导出
docker cp outlook-email-api:/app/data.db backups/data.db.$(date +%Y%m%d_%H%M%S)
```

### 恢复数据库
```bash
# 停止容器
docker-compose stop

# 恢复数据库
cp backups/data.db.20251101_170000 data.db

# 启动容器
docker-compose start
```

### 清理日志
```bash
# 清理30天前的日志
find logs/ -name "*.log.*" -mtime +30 -delete

# 查看日志大小
du -sh logs/
```

## 🔍 故障排查

### 容器无法启动
```bash
# 查看详细日志
docker-compose logs

# 检查配置文件
docker-compose config

# 检查端口占用
netstat -tlnp | grep 8001
lsof -i :8001
```

### 时间显示不对
```bash
# 1. 验证时区配置
bash scripts/verify_timezone.sh

# 2. 如果不对，运行修复
bash scripts/fix_timezone.sh

# 3. 清除浏览器缓存并刷新
```

### 容器健康检查失败
```bash
# 查看健康状态
docker inspect outlook-email-api | grep -A 10 Health

# 手动测试API
curl http://localhost:8001/api

# 进入容器检查
docker exec -it outlook-email-api sh
python -c "import requests; print(requests.get('http://localhost:8000/api').json())"
```

### 数据库锁定
```bash
# 停止容器
docker-compose stop

# 检查数据库文件
sqlite3 data.db "PRAGMA integrity_check;"

# 重启容器
docker-compose start
```

## 🛑 停止和清理

### 停止容器
```bash
docker-compose stop
```

### 停止并删除容器
```bash
docker-compose down
```

### 停止并删除容器和卷
```bash
docker-compose down -v
```

### 清理未使用的镜像
```bash
docker image prune -a
```

### 完全清理（谨慎使用）
```bash
# 停止容器
docker-compose down

# 删除镜像
docker rmi outlook-email-manager

# 清理系统
docker system prune -a
```

## 🔐 安全管理

### 修改管理员密码
```bash
# 1. 访问 http://your-server:8001
# 2. 使用默认账号登录（admin/admin123）
# 3. 在设置中修改密码
```

### 查看API Key
```bash
# 查看容器日志中的API Key
docker-compose logs | grep "API Key"

# 或查看数据库
sqlite3 data.db "SELECT * FROM api_keys;"
```

### 限制访问
```bash
# 修改 docker-compose.yml 中的端口映射
# 从 0.0.0.0:8001:8000 改为 127.0.0.1:8001:8000
# 然后通过Nginx反向代理访问
```

## 📈 性能优化

### 查看资源使用
```bash
docker stats outlook-email-api
```

### 设置资源限制
在 `docker-compose.yml` 中添加：
```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### 查看日志大小
```bash
du -sh logs/
docker inspect outlook-email-api | grep LogPath
```

## 🌐 网络配置

### 查看网络
```bash
docker network ls
docker network inspect outlook-network
```

### 测试连接
```bash
# 从宿主机测试
curl http://localhost:8001/api

# 从容器内测试
docker exec outlook-email-api wget -qO- http://localhost:8000/api
```

### 端口映射修改
修改 `docker-compose.yml`：
```yaml
ports:
  - "9000:8000"  # 改为其他端口
```

## 📝 常用组合命令

### 快速重启
```bash
docker-compose restart && docker-compose logs -f --tail=50
```

### 重新构建并查看日志
```bash
docker-compose down && docker-compose build --no-cache && docker-compose up -d && docker-compose logs -f
```

### 备份并更新
```bash
cp data.db backups/data.db.$(date +%Y%m%d_%H%M%S) && \
git pull && \
docker-compose down && \
docker-compose build --no-cache && \
docker-compose up -d
```

### 一键部署（首次）
```bash
docker-compose build && \
docker-compose up -d && \
sleep 5 && \
bash scripts/verify_timezone.sh && \
docker-compose logs --tail=50
```

## 🔗 访问地址

部署完成后访问：

- **Web界面**: http://your-server-ip:8001
- **API文档**: http://your-server-ip:8001/docs
- **API状态**: http://your-server-ip:8001/api
- **OpenAPI**: http://your-server-ip:8001/redoc

## 📚 相关文档

- [时区配置指南](docs/时区配置指南.md)
- [Docker部署说明](docs/Docker部署说明.md)
- [快速开始](docs/QUICK_START.md)
- [架构文档](docs/ARCHITECTURE.md)

---

**提示**: 将常用命令添加到 `~/.bashrc` 或创建别名以提高效率

```bash
# 添加到 ~/.bashrc
alias outlook-logs='docker-compose -f /path/to/OutlookManager2/docker-compose.yml logs -f'
alias outlook-restart='docker-compose -f /path/to/OutlookManager2/docker-compose.yml restart'
alias outlook-status='docker-compose -f /path/to/OutlookManager2/docker-compose.yml ps'
```

