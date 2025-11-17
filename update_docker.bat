@echo off
chcp 65001 >nul
REM Docker 代码更新脚本 (Windows版本)

echo ==========================================
echo   OutlookManager2 Docker 代码更新
echo ==========================================
echo.

REM 1. 停止并删除旧容器
echo 📦 [1/4] 停止并删除旧容器...
docker-compose down
echo ✅ 容器已停止
echo.

REM 2. 删除旧镜像
echo 🗑️  [2/4] 删除旧镜像...
docker-compose rm -f
docker rmi outlook-email-client 2>nul
echo ✅ 旧镜像已清理
echo.

REM 3. 重新构建镜像
echo 🔨 [3/4] 重新构建镜像（不使用缓存）...
docker-compose build --no-cache
if errorlevel 1 (
    echo ❌ 构建失败！请检查错误信息
    pause
    exit /b 1
)
echo ✅ 镜像构建完成
echo.

REM 4. 启动新容器
echo 🚀 [4/4] 启动新容器...
docker-compose up -d
if errorlevel 1 (
    echo ❌ 启动失败！请检查错误信息
    pause
    exit /b 1
)
echo ✅ 容器已启动
echo.

REM 等待服务启动
echo ⏳ 等待服务启动（10秒）...
timeout /t 10 /nobreak >nul
echo.

REM 检查容器状态
echo 📊 容器状态：
docker-compose ps
echo.

echo ✅ 更新完成！
echo.
echo 📋 查看日志：
echo   docker-compose logs -f
echo.
echo 🔍 验证修复：
echo   浏览器访问 http://localhost:8001 测试批量刷新Token功能
echo.
pause

