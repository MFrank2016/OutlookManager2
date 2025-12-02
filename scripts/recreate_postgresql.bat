@echo off
REM 重新创建 PostgreSQL 容器和数据卷的脚本 (Windows)

echo ==========================================
echo 重新创建 PostgreSQL 容器和数据卷
echo ==========================================
echo.
echo ⚠️  警告：此操作将删除所有现有数据！
echo.

REM 确认操作
set /p confirm="确定要继续吗？(yes/no): "
if /i not "%confirm%"=="yes" (
    echo 操作已取消
    exit /b 0
)

echo.
echo 步骤 1: 停止并删除 PostgreSQL 容器...
docker compose stop postgresql
docker compose rm -f postgresql

echo.
echo 步骤 2: 删除 PostgreSQL 数据卷...
docker volume rm outlook_postgres_data 2>nul
if errorlevel 1 (
    echo 数据卷不存在或已被删除
)

echo.
echo 步骤 3: 重新创建并启动 PostgreSQL 容器...
docker compose up -d postgresql

echo.
echo 步骤 4: 等待 PostgreSQL 就绪...
timeout /t 5 /nobreak >nul

REM 检查容器状态
echo.
echo 检查容器状态...
docker compose ps postgresql

echo.
echo 检查容器日志（最后 20 行）...
docker compose logs --tail=20 postgresql

echo.
echo ==========================================
echo ✅ PostgreSQL 容器和数据卷已重新创建
echo ==========================================
echo.
echo 数据库连接信息：
echo   数据库名: outlook_manager (或 .env 中的 POSTGRES_DB)
echo   用户名: outlook_user (或 .env 中的 POSTGRES_USER)
echo   密码: changeme (或 .env 中的 POSTGRES_PASSWORD)
echo   端口: 5432 (或 .env 中的 POSTGRES_PORT)
echo.
echo 测试连接：
echo   docker compose exec postgresql psql -U outlook_user -d outlook_manager -c "SELECT version();"
echo.

pause

