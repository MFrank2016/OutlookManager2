@echo off
chcp 65001 > nul
cls

echo ==================================
echo Outlook邮件管理系统 v2.0
echo ==================================
echo.

REM 检查Python版本
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

python --version
echo.

REM 检查虚拟环境
if not exist "venv" (
    echo 首次运行，正在创建虚拟环境...
    python -m venv venv
    
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
    
    echo 安装依赖包...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

echo.

REM 检查是否需要迁移数据
if not exist "data.db" (
    if exist "accounts.json" (
        echo 检测到accounts.json文件，正在迁移数据...
        python migrate.py
        echo.
    )
)

REM 检查是否已有数据库
if not exist "data.db" (
    echo 初始化数据库...
    python -c "import database as db; db.init_database(); print('数据库初始化完成')"
    python -c "import auth; auth.init_default_admin()"
    echo.
)

REM 启动应用
echo 启动Outlook邮件管理系统...
echo.
echo 访问地址:
echo   - 主页面: http://localhost:8000
echo   - 登录页面: http://localhost:8000/static/login.html
echo   - API文档: http://localhost:8000/docs
echo.
echo 默认管理员:
echo   用户名: admin
echo   密码: admin123
echo   ⚠️  请登录后立即修改密码！
echo.
echo 按 Ctrl+C 停止服务
echo ==================================
echo.

python main.py

pause

