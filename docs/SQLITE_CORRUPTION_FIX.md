# SQLite 数据库损坏修复指南

## 问题症状

应用启动时出现以下错误：

```
Tree 147 page 96790 cell 3: Rowid 978297 out of order
sqlite3.ProgrammingError: Cannot operate on a closed database.
ERROR: Application startup failed. Exiting.
```

这是 SQLite 数据库损坏的典型错误。

## 快速修复方案

### 方案 1: 切换到 PostgreSQL（推荐）

如果 PostgreSQL 已经配置好，这是最简单的方案：

1. **停止应用**：

   ```bash
   docker compose stop outlook-email-api
   ```

2. **配置 PostgreSQL**：
   编辑 `.env` 文件，添加：

   ```bash
   DB_TYPE=postgresql
   DB_HOST=postgresql
   DB_PORT=5432
   DB_NAME=outlook_manager
   DB_USER=outlook_user
   DB_PASSWORD=your_password
   POSTGRES_PASSWORD=your_password
   ```

3. **初始化 PostgreSQL 数据库**：

   ```bash
   docker compose exec outlook-email-api python3 scripts/init_postgresql.py
   ```

4. **启动应用**：
   ```bash
   docker compose start outlook-email-api
   ```

### 方案 2: 修复 SQLite 数据库

#### 方法 A: 使用修复脚本（自动）

```bash
# 在容器内运行
docker compose exec outlook-email-api bash scripts/fix_corrupted_db.sh

# 或在宿主机运行（需要sqlite3工具）
cd /path/to/OutlookManager2
bash scripts/fix_corrupted_db.sh
```

#### 方法 B: 使用 Python 修复脚本

```bash
docker compose exec outlook-email-api python3 scripts/repair_database.py
```

#### 方法 C: 手动修复

1. **备份数据库**：

   ```bash
   cp data.db data.db.backup.$(date +%Y%m%d_%H%M%S)
   ```

2. **尝试恢复数据**：

   ```bash
   # 导出数据
   sqlite3 data.db ".recover" > recovered.sql

   # 创建新数据库
   sqlite3 data.db.new < recovered.sql

   # 检查新数据库
   sqlite3 data.db.new "PRAGMA integrity_check;"

   # 如果检查通过，替换原文件
   mv data.db.new data.db
   ```

### 方案 3: 重建数据库（会丢失数据）

如果数据不重要或无法修复：

1. **备份旧数据库**（以防万一）：

   ```bash
   cp data.db data.db.backup.$(date +%Y%m%d_%H%M%S)
   ```

2. **删除损坏的数据库**：

   ```bash
   rm data.db
   ```

3. **重启应用**（会自动创建新数据库）：
   ```bash
   docker compose restart outlook-email-api
   ```

## 预防措施

### 1. 定期备份

```bash
# 手动备份
cp data.db backups/data.db.$(date +%Y%m%d_%H%M%S)

# 或设置自动备份（cron）
0 2 * * * cd /path/to/OutlookManager2 && cp data.db backups/data.db.$(date +\%Y\%m\%d)
```

### 2. 切换到 PostgreSQL

PostgreSQL 比 SQLite 更稳定，适合生产环境：

- 更好的并发支持
- 更好的数据完整性保护
- 支持事务和回滚
- 更好的性能

### 3. 监控磁盘空间

确保有足够的磁盘空间，避免数据库写入失败：

```bash
df -h
```

### 4. 正确关闭应用

使用正常方式停止应用，避免强制终止：

```bash
docker compose stop outlook-email-api
# 或
docker compose down
```

## 故障排查

### 问题 1: 修复脚本无法运行

**检查**：

- 确保有执行权限：`chmod +x scripts/fix_corrupted_db.sh`
- 确保 sqlite3 工具已安装：`which sqlite3`

### 问题 2: 修复后仍然损坏

**尝试**：

1. 使用不同的修复方法
2. 检查磁盘是否有坏道：`badblocks -v /dev/sda1`
3. 考虑切换到 PostgreSQL

### 问题 3: 数据丢失

**恢复**：

- 检查备份文件：`ls -lh backups/`
- 从备份恢复：`cp backups/data.db.backup_YYYYMMDD_HHMMSS data.db`

## 相关文档

- [PostgreSQL 部署指南](POSTGRESQL_DEPLOYMENT.md)
- [Docker 部署指南](DOCKER_UPDATE_GUIDE.md)
