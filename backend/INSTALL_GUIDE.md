# 📦 安装指南

## 问题说明

您遇到的错误是由于 **Python 3.13** 与旧版本依赖包的兼容性问题导致的。主要问题：

1. **asyncpg**、**dependency-injector**、**pydantic-core** 这些包需要编译 C/Cython 扩展
2. 旧版本没有为 Python 3.13 提供预编译的 wheel
3. Windows 环境缺少 Visual C++ 编译器

## ✅ 解决方案（已完成）

我已经更新了 `requirements.txt`：

### 主要变更：
- ❌ **移除** `asyncpg`（PostgreSQL 驱动）- 我们只用 SQLite
- ❌ **移除** `dependency-injector` - 改用 FastAPI 原生依赖注入
- ❌ **移除** `redis` - 使用内存缓存
- ✅ **升级** `pydantic` 从 2.6.1 到 2.10.6（支持 Python 3.13）
- ✅ **升级** 其他包到最新兼容版本

## 🚀 重新安装步骤

### 1. 清理旧依赖

```powershell
# 在 backend 目录下
cd backend

# 清理 pip 缓存（可选但推荐）
pip cache purge

# 卸载旧依赖（如果之前安装失败）
pip freeze | ForEach-Object { pip uninstall -y $_ }
```

### 2. 重新安装

```powershell
# 安装新的依赖
pip install -r requirements.txt
```

### 3. 验证安装

```powershell
# 测试导入
python -c "import fastapi; import pydantic; import sqlalchemy; print('✅ 所有核心依赖安装成功!')"
```

## 📋 主要依赖包（Python 3.13 兼容版）

| 包名 | 旧版本 | 新版本 | 说明 |
|------|--------|--------|------|
| fastapi | 0.109.2 | 0.115.6 | 升级到最新稳定版 |
| pydantic | 2.6.1 | 2.10.6 | **关键**：支持 Python 3.13 |
| sqlalchemy | 2.0.27 | 2.0.36 | 升级到最新版本 |
| uvicorn | 0.27.1 | 0.34.0 | 升级到最新版本 |
| pytest | 8.0.0 | 8.3.4 | 升级到最新版本 |
| asyncpg | 0.29.0 | ❌ 移除 | 不需要 PostgreSQL |
| dependency-injector | 4.41.0 | ❌ 移除 | 用 FastAPI DI |
| redis | 5.0.1 | ❌ 移除 | 用内存缓存 |

## ⚠️ 如果仍然遇到问题

### 方案A：使用 Python 3.11/3.12（推荐）

如果问题持续，建议切换到 Python 3.11 或 3.12：

```powershell
# 创建新的虚拟环境（使用 Python 3.11）
python3.11 -m venv venv_py311
.\venv_py311\Scripts\activate
pip install -r requirements.txt
```

### 方案B：安装 Visual C++ 编译器

如果您坚持使用 Python 3.13 并需要编译某些包：

1. 下载并安装 **Microsoft C++ Build Tools**
   - 访问：https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - 选择 "C++ build tools" 工作负载
   - 安装大小约 6-8 GB

### 方案C：使用预编译的 Wheel

某些包可能需要从非官方源获取预编译版本：
- 访问：https://www.lfd.uci.edu/~gohlke/pythonlibs/
- 下载对应的 .whl 文件
- 手动安装：`pip install xxx.whl`

## 🎯 推荐配置

### 开发环境
- **Python**: 3.11 或 3.12（最稳定）
- **数据库**: SQLite（开发）/ PostgreSQL（生产）
- **缓存**: 内存缓存（开发）/ Redis（生产）

### 生产环境
```bash
# 如需 PostgreSQL 支持（Linux/Docker 环境）
pip install asyncpg==0.29.0

# 如需 Redis 支持
pip install redis==5.0.1
```

## ✅ 预期结果

成功安装后，您应该看到：

```
Successfully installed fastapi-0.115.6 pydantic-2.10.6 sqlalchemy-2.0.36 ...
```

没有任何错误信息！

## 📞 获取帮助

如果仍有问题，请提供：
1. Python 版本：`python --version`
2. 操作系统版本
3. 完整的错误日志

---

**更新时间**: 2025-01-29  
**适用版本**: Python 3.11+ / Python 3.13

