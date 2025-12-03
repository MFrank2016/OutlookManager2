# 使用Python 3.11 Alpine作为基础镜像，体积更小
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/python:3.11-alpine3.21

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai

# 安装系统依赖和时区数据
RUN apk add --no-cache tzdata \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# 复制requirements文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY main.py .
COPY config.py .
COPY models.py .
COPY logger_config.py .
COPY database.py .
COPY auth.py .
COPY permissions.py .
COPY admin_api.py .
COPY account_service.py .
COPY oauth_service.py .
COPY graph_api_service.py .
COPY email_service.py .
COPY email_utils.py .
COPY imap_pool.py .
COPY cache_service.py .
COPY verification_code_detector.py .
COPY rate_limiter.py .
COPY routes/ ./routes/
COPY dao/ ./dao/
COPY static/ ./static/
COPY docker/docker-entrypoint.sh .

# 设置启动脚本权限
RUN chmod +x docker-entrypoint.sh

# 创建数据目录和日志目录用于持久化存储
RUN mkdir -p /app/data /app/logs && chmod 777 /app/data /app/logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api')" || exit 1

# 启动命令
CMD ["./docker-entrypoint.sh"] 