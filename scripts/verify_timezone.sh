#!/bin/bash
# 时区配置验证脚本
# 用于验证Docker容器的时区配置是否正确

set -e

echo "=========================================="
echo "Docker容器时区配置验证"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 容器名称
CONTAINER_NAME="outlook-email-api"

# 检查容器是否运行
echo "1. 检查容器状态..."
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}✗ 容器未运行${NC}"
    echo "请先启动容器: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ 容器正在运行${NC}"
echo ""

# 验证宿主机时区
echo "2. 宿主机时区信息..."
echo "   当前时间: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "   时区: $(date '+%z')"
if [ -f /etc/timezone ]; then
    echo "   时区文件: $(cat /etc/timezone)"
fi
echo ""

# 验证容器时区
echo "3. 容器时区信息..."
CONTAINER_DATE=$(docker exec $CONTAINER_NAME date '+%Y-%m-%d %H:%M:%S %Z')
CONTAINER_TZ=$(docker exec $CONTAINER_NAME sh -c 'echo $TZ' 2>/dev/null || echo "未设置")
CONTAINER_TIMEZONE=$(docker exec $CONTAINER_NAME cat /etc/timezone 2>/dev/null || echo "未找到")
CONTAINER_OFFSET=$(docker exec $CONTAINER_NAME date '+%z')

echo "   当前时间: $CONTAINER_DATE"
echo "   时区变量: $CONTAINER_TZ"
echo "   时区文件: $CONTAINER_TIMEZONE"
echo "   时区偏移: $CONTAINER_OFFSET"
echo ""

# 验证Python时区
echo "4. Python时区信息..."
PYTHON_TIME=$(docker exec $CONTAINER_NAME python -c "import datetime; print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))")
echo "   Python时间: $PYTHON_TIME"
echo ""

# 判断时区是否正确
echo "5. 时区验证结果..."
if [ "$CONTAINER_OFFSET" == "+0800" ] || [ "$CONTAINER_OFFSET" == "+08:00" ]; then
    echo -e "${GREEN}✓ 时区配置正确（东8区）${NC}"
    TIMEZONE_OK=true
elif [ "$CONTAINER_OFFSET" == "+0000" ]; then
    echo -e "${RED}✗ 时区配置错误（仍为UTC）${NC}"
    TIMEZONE_OK=false
else
    echo -e "${YELLOW}⚠ 时区偏移为 $CONTAINER_OFFSET${NC}"
    TIMEZONE_OK=false
fi
echo ""

# 时间差异检查
echo "6. 时间差异检查..."
HOST_HOUR=$(date '+%H')
CONTAINER_HOUR=$(docker exec $CONTAINER_NAME date '+%H')
TIME_DIFF=$((HOST_HOUR - CONTAINER_HOUR))

if [ $TIME_DIFF -eq 0 ] || [ $TIME_DIFF -eq -24 ] || [ $TIME_DIFF -eq 24 ]; then
    echo -e "${GREEN}✓ 宿主机与容器时间一致${NC}"
elif [ $TIME_DIFF -eq 8 ] || [ $TIME_DIFF -eq -16 ]; then
    echo -e "${RED}✗ 时间相差8小时（UTC时区问题）${NC}"
    echo "   宿主机小时: $HOST_HOUR"
    echo "   容器小时: $CONTAINER_HOUR"
else
    echo -e "${YELLOW}⚠ 时间差异: ${TIME_DIFF}小时${NC}"
    echo "   宿主机小时: $HOST_HOUR"
    echo "   容器小时: $CONTAINER_HOUR"
fi
echo ""

# 检查环境变量
echo "7. 环境变量检查..."
if [ "$CONTAINER_TZ" == "Asia/Shanghai" ]; then
    echo -e "${GREEN}✓ TZ环境变量已设置为 Asia/Shanghai${NC}"
else
    echo -e "${RED}✗ TZ环境变量未正确设置${NC}"
    echo "   当前值: $CONTAINER_TZ"
fi
echo ""

# 检查时区文件
echo "8. 时区文件检查..."
if [ "$CONTAINER_TIMEZONE" == "Asia/Shanghai" ]; then
    echo -e "${GREEN}✓ /etc/timezone 文件正确${NC}"
else
    echo -e "${YELLOW}⚠ /etc/timezone 文件: $CONTAINER_TIMEZONE${NC}"
fi
echo ""

# 检查日志时间
echo "9. 日志时间检查..."
if [ -f "logs/outlook_manager.log" ]; then
    LAST_LOG_TIME=$(tail -1 logs/outlook_manager.log | grep -oP '^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}' || echo "无法解析")
    echo "   最新日志时间: $LAST_LOG_TIME"
    
    # 提取小时
    if [ "$LAST_LOG_TIME" != "无法解析" ]; then
        LOG_HOUR=$(echo $LAST_LOG_TIME | cut -d' ' -f2 | cut -d':' -f1)
        CURRENT_HOUR=$(date '+%H')
        LOG_DIFF=$((CURRENT_HOUR - LOG_HOUR))
        
        if [ $LOG_DIFF -ge -1 ] && [ $LOG_DIFF -le 1 ]; then
            echo -e "${GREEN}✓ 日志时间与当前时间接近${NC}"
        else
            echo -e "${YELLOW}⚠ 日志时间可能不准确（差异: ${LOG_DIFF}小时）${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠ 日志文件不存在${NC}"
fi
echo ""

# 最终结论
echo "=========================================="
echo "验证总结"
echo "=========================================="

if [ "$TIMEZONE_OK" = true ]; then
    echo -e "${GREEN}✓ 时区配置正确！${NC}"
    echo ""
    echo "容器已正确配置为东8区（Asia/Shanghai）"
    echo "如果前端显示时间仍然不对，请："
    echo "  1. 清除浏览器缓存"
    echo "  2. 硬刷新页面（Ctrl+Shift+R）"
    echo "  3. 检查前端JavaScript时区处理逻辑"
else
    echo -e "${RED}✗ 时区配置需要修复${NC}"
    echo ""
    echo "修复步骤："
    echo "  1. 确保 docker-compose.yml 包含时区配置"
    echo "  2. 确保 Dockerfile 包含时区设置"
    echo "  3. 重新构建镜像: docker-compose build --no-cache"
    echo "  4. 重启容器: docker-compose up -d"
    echo "  5. 再次运行此脚本验证"
    echo ""
    echo "详细文档: docs/时区配置指南.md"
fi

echo ""
echo "=========================================="

