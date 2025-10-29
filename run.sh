#!/bin/bash

# Outlook邮件管理系统 v2.0 启动脚本

echo "=================================="
echo "Outlook邮件管理系统 v2.0"
echo "=================================="
echo ""

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [ $? -ne 0 ]; then
    echo "错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

echo "Python版本: $python_version"
echo ""

# 检查是否需要安装依赖
if [ ! -d "venv" ]; then
    echo "首次运行，正在创建虚拟环境..."
    python3 -m venv venv
    
    echo "激活虚拟环境..."
    source venv/bin/activate
    
    echo "安装依赖包..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

echo ""

# 检查是否需要迁移数据
if [ ! -f "data.db" ] && [ -f "accounts.json" ]; then
    echo "检测到accounts.json文件，正在迁移数据..."
    python migrate.py
    echo ""
fi

# 检查是否已有数据库
if [ ! -f "data.db" ]; then
    echo "初始化数据库..."
    python -c "import database as db; db.init_database(); print('数据库初始化完成')"
    python -c "import auth; auth.init_default_admin()"
    echo ""
fi

# 启动应用
echo "启动Outlook邮件管理系统..."
echo ""
echo "访问地址:"
echo "  - 主页面: http://localhost:8000"
echo "  - 登录页面: http://localhost:8000/static/login.html"
echo "  - API文档: http://localhost:8000/docs"
echo ""
echo "默认管理员:"
echo "  用户名: admin"
echo "  密码: admin123"
echo "  ⚠️  请登录后立即修改密码！"
echo ""
echo "按 Ctrl+C 停止服务"
echo "=================================="
echo ""

python main.py

