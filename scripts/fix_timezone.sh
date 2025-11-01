#!/bin/bash
# 时区配置修复脚本
# 自动修复Docker容器的时区配置并重启服务

set -e

echo "=========================================="
echo "Docker容器时区配置修复"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    exit 1
fi

# 步骤1: 检查宿主机时区
echo "步骤1: 检查宿主机时区..."
CURRENT_TZ=$(timedatectl show -p Timezone --value 2>/dev/null || cat /etc/timezone 2>/dev/null || echo "Unknown")
echo "   当前时区: $CURRENT_TZ"

if [ "$CURRENT_TZ" != "Asia/Shanghai" ]; then
    echo -e "${YELLOW}   提示: 宿主机时区不是 Asia/Shanghai${NC}"
    read -p "   是否设置宿主机时区为 Asia/Shanghai? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo timedatectl set-timezone Asia/Shanghai
        echo -e "${GREEN}   ✓ 宿主机时区已设置${NC}"
    fi
fi
echo ""

# 步骤2: 停止容器
echo "步骤2: 停止现有容器..."
docker-compose down
echo -e "${GREEN}   ✓ 容器已停止${NC}"
echo ""

# 步骤3: 备份配置文件
echo "步骤3: 备份配置文件..."
BACKUP_DIR="backups/timezone_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp docker-compose.yml "$BACKUP_DIR/"
cp docker/Dockerfile "$BACKUP_DIR/"
echo -e "${GREEN}   ✓ 配置文件已备份到 $BACKUP_DIR${NC}"
echo ""

# 步骤4: 检查配置文件
echo "步骤4: 检查配置文件..."

# 检查 docker-compose.yml
if grep -q "TZ=Asia/Shanghai" docker-compose.yml; then
    echo -e "${GREEN}   ✓ docker-compose.yml 已包含时区配置${NC}"
else
    echo "   ⚠ docker-compose.yml 缺少时区配置"
    echo "   请手动添加或查看 docs/时区配置指南.md"
fi

# 检查 Dockerfile
if grep -q "TZ=Asia/Shanghai" docker/Dockerfile; then
    echo -e "${GREEN}   ✓ Dockerfile 已包含时区配置${NC}"
else
    echo "   ⚠ Dockerfile 缺少时区配置"
    echo "   请手动添加或查看 docs/时区配置指南.md"
fi
echo ""

# 步骤5: 重新构建镜像
echo "步骤5: 重新构建Docker镜像..."
echo "   这可能需要几分钟时间..."
docker-compose build --no-cache
echo -e "${GREEN}   ✓ 镜像构建完成${NC}"
echo ""

# 步骤6: 启动容器
echo "步骤6: 启动容器..."
docker-compose up -d
echo -e "${GREEN}   ✓ 容器已启动${NC}"
echo ""

# 步骤7: 等待容器就绪
echo "步骤7: 等待容器就绪..."
sleep 5
echo -e "${GREEN}   ✓ 容器已就绪${NC}"
echo ""

# 步骤8: 验证时区配置
echo "步骤8: 验证时区配置..."
echo ""

# 运行验证脚本
if [ -f "scripts/verify_timezone.sh" ]; then
    bash scripts/verify_timezone.sh
else
    # 简单验证
    CONTAINER_NAME="outlook-email-api"
    CONTAINER_DATE=$(docker exec $CONTAINER_NAME date)
    CONTAINER_TZ=$(docker exec $CONTAINER_NAME sh -c 'echo $TZ')
    
    echo "   容器时间: $CONTAINER_DATE"
    echo "   时区变量: $CONTAINER_TZ"
    echo ""
    
    if [[ "$CONTAINER_DATE" == *"CST"* ]] && [ "$CONTAINER_TZ" == "Asia/Shanghai" ]; then
        echo -e "${GREEN}   ✓ 时区配置成功！${NC}"
    else
        echo "   ⚠ 时区可能未正确配置，请手动检查"
    fi
fi

echo ""
echo "=========================================="
echo "修复完成"
echo "=========================================="
echo ""
echo "后续步骤:"
echo "  1. 访问前端页面: http://your-server-ip:8001"
echo "  2. 清除浏览器缓存并刷新页面"
echo "  3. 检查显示的时间是否正确"
echo ""
echo "如有问题，请查看:"
echo "  - 日志: docker-compose logs -f"
echo "  - 文档: docs/时区配置指南.md"
echo ""

