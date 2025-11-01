# 🚀 服务器部署步骤（时区配置版）

## 📋 部署前准备

### 环境要求
- ✅ Debian 12 服务器
- ✅ Docker 20.10+
- ✅ Docker Compose 1.29+
- ✅ Git

### 检查环境
```bash
# 检查Docker版本
docker --version

# 检查Docker Compose版本
docker-compose --version

# 检查Git版本
git --version
```

## 🎯 部署步骤

### 步骤1: 更新代码

```bash
# 进入项目目录
cd /path/to/OutlookManager2

# 拉取最新代码
git pull origin main

# 查看当前分支和状态
git status
```

### 步骤2: 添加脚本执行权限

```bash
# 给时区相关脚本添加执行权限
chmod +x scripts/verify_timezone.sh
chmod +x scripts/fix_timezone.sh

# 验证权限
ls -lh scripts/*.sh
```

### 步骤3: 一键修复时区（推荐）

```bash
# 运行自动修复脚本
bash scripts/fix_timezone.sh
```

脚本会自动完成：
1. ✅ 检查宿主机时区
2. ✅ 停止现有容器
3. ✅ 备份配置文件
4. ✅ 重新构建镜像
5. ✅ 启动容器
6. ✅ 验证时区配置

### 步骤4: 手动修复（备选方案）

如果自动脚本失败，使用手动方式：

```bash
# 1. 设置宿主机时区（如果需要）
sudo timedatectl set-timezone Asia/Shanghai

# 2. 停止容器
docker-compose down

# 3. 重新构建镜像（不使用缓存）
docker-compose build --no-cache

# 4. 启动容器
docker-compose up -d

# 5. 等待容器启动
sleep 10
```

### 步骤5: 验证配置

```bash
# 运行验证脚本
bash scripts/verify_timezone.sh
```

**预期输出**:
```
==========================================
Docker容器时区配置验证
==========================================

1. 检查容器状态...
✓ 容器正在运行

2. 宿主机时区信息...
   当前时间: 2025-11-01 17:00:00 CST
   时区: +0800

3. 容器时区信息...
   当前时间: 2025-11-01 17:00:00 CST
   时区变量: Asia/Shanghai
   时区文件: Asia/Shanghai
   时区偏移: +0800

...

✓ 时区配置正确！
==========================================
```

### 步骤6: 查看容器日志

```bash
# 查看最近50行日志
docker-compose logs --tail=50

# 实时查看日志
docker-compose logs -f

# 按Ctrl+C退出日志查看
```

### 步骤7: 测试API

```bash
# 测试API状态
curl http://localhost:8001/api

# 预期返回JSON响应
```

### 步骤8: 访问前端

1. **清除浏览器缓存**
   - Chrome: `Ctrl+Shift+Delete`
   - Firefox: `Ctrl+Shift+Delete`
   - Safari: `Cmd+Option+E`

2. **访问Web界面**
   ```
   http://your-server-ip:8001
   ```

3. **硬刷新页面**
   - Windows/Linux: `Ctrl+Shift+R`
   - Mac: `Cmd+Shift+R`

4. **检查时间显示**
   - 查看邮件列表的时间
   - 查看账户刷新时间
   - 确认显示为东8区时间

## ✅ 验证清单

完成部署后，逐项检查：

### 服务器端
- [ ] 容器正常运行（`docker ps`）
- [ ] 容器时间显示正确（`docker exec outlook-email-api date`）
- [ ] 时区变量正确（`docker exec outlook-email-api sh -c 'echo $TZ'`）
- [ ] Python时间正确（验证脚本输出）
- [ ] 日志时间正确（`tail logs/outlook_manager.log`）
- [ ] API响应正常（`curl http://localhost:8001/api`）

### 前端
- [ ] 页面可以正常访问
- [ ] 登录功能正常
- [ ] 邮件列表显示正确
- [ ] 时间显示为东8区时间
- [ ] 账户刷新时间正确

### 功能
- [ ] 可以添加账户
- [ ] 可以查看邮件
- [ ] 可以刷新Token
- [ ] 后台任务正常运行

## 🔍 故障排查

### 问题1: 容器无法启动

**检查**:
```bash
# 查看容器状态
docker-compose ps

# 查看详细日志
docker-compose logs

# 检查端口占用
netstat -tlnp | grep 8001
```

**解决**:
```bash
# 如果端口被占用
sudo lsof -ti:8001 | xargs sudo kill -9

# 重新启动
docker-compose up -d
```

### 问题2: 时区仍然不对

**检查**:
```bash
# 运行验证脚本
bash scripts/verify_timezone.sh

# 手动检查
docker exec outlook-email-api date
docker exec outlook-email-api sh -c 'echo $TZ'
```

**解决**:
```bash
# 重新运行修复脚本
bash scripts/fix_timezone.sh

# 或手动重建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 问题3: 前端时间不对

**检查**:
```bash
# 确认容器时区正确
docker exec outlook-email-api date

# 查看浏览器控制台
# F12 -> Console -> 执行: console.log(new Date())
```

**解决**:
1. 清除浏览器缓存
2. 硬刷新页面（Ctrl+Shift+R）
3. 重新登录
4. 检查浏览器时区设置

### 问题4: 数据库锁定

**检查**:
```bash
# 查看日志中是否有数据库错误
docker-compose logs | grep -i "database"
```

**解决**:
```bash
# 停止容器
docker-compose stop

# 检查数据库完整性
sqlite3 data.db "PRAGMA integrity_check;"

# 如果需要，恢复备份
cp backups/data.db.20251101_170000 data.db

# 重启容器
docker-compose start
```

## 📊 监控和维护

### 日常监控

```bash
# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats outlook-email-api

# 查看最新日志
docker-compose logs --tail=100

# 查看应用日志
tail -f logs/outlook_manager.log
```

### 定期维护

```bash
# 每周备份数据库
cp data.db backups/data.db.$(date +%Y%m%d)

# 每月清理旧日志
find logs/ -name "*.log.*" -mtime +30 -delete

# 每季度清理Docker
docker system prune -a
```

### 性能优化

```bash
# 查看日志大小
du -sh logs/

# 查看数据库大小
ls -lh data.db

# 优化数据库
sqlite3 data.db "VACUUM;"
```

## 🔐 安全建议

### 1. 修改默认密码
首次登录后立即修改管理员密码：
- 访问 http://your-server:8001
- 登录（admin/admin123）
- 进入设置 -> 修改密码

### 2. 配置防火墙
```bash
# 只允许特定IP访问
sudo ufw allow from YOUR_IP to any port 8001

# 或使用Nginx反向代理
sudo apt install nginx
```

### 3. 启用HTTPS
使用Nginx + Let's Encrypt配置HTTPS

### 4. 定期备份
```bash
# 创建备份脚本
cat > /root/backup_outlook.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/outlook"
mkdir -p $BACKUP_DIR
cd /path/to/OutlookManager2
cp data.db $BACKUP_DIR/data.db.$(date +%Y%m%d_%H%M%S)
find $BACKUP_DIR -name "data.db.*" -mtime +7 -delete
EOF

chmod +x /root/backup_outlook.sh

# 添加到crontab（每天凌晨2点备份）
crontab -e
# 添加: 0 2 * * * /root/backup_outlook.sh
```

## 📚 相关文档

| 文档 | 说明 | 路径 |
|------|------|------|
| 时区配置指南 | 详细配置说明 | `docs/时区配置指南.md` |
| 快速修复 | 快速参考 | `TIMEZONE_QUICKFIX.md` |
| 命令速查 | Docker命令 | `DEPLOY_COMMANDS.md` |
| Docker部署 | 部署文档 | `docs/Docker部署说明.md` |
| 修改总结 | 更新内容 | `TIMEZONE_CHANGES_SUMMARY.md` |

## 🆘 获取帮助

### 查看文档
```bash
# 查看快速修复指南
cat TIMEZONE_QUICKFIX.md

# 查看命令速查表
cat DEPLOY_COMMANDS.md

# 查看详细指南
cat docs/时区配置指南.md
```

### 运行诊断
```bash
# 运行完整验证
bash scripts/verify_timezone.sh

# 查看容器详情
docker inspect outlook-email-api

# 查看网络配置
docker network inspect outlook-network
```

### 联系支持
- 查看项目文档
- 检查GitHub Issues
- 查看日志文件

## 🎉 部署完成

部署成功后，您应该能够：

✅ 访问Web界面  
✅ 看到正确的东8区时间  
✅ 正常使用所有功能  
✅ 后台任务正常运行  

**下一步**:
1. 添加邮箱账户
2. 配置标签分类
3. 设置定期备份
4. 监控系统运行

---

**部署时间**: 约10-15分钟  
**难度**: ⭐⭐☆☆☆  
**维护者**: Outlook Manager Team  
**最后更新**: 2025-11-01

**祝您使用愉快！** 🎊

