"""
配置常量模块

集中管理系统的所有配置常量，包括OAuth2、IMAP、连接池、缓存和日志配置
"""

import os
from pathlib import Path

# ============================================================================
# OAuth2配置
# ============================================================================

TOKEN_URL = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
OAUTH_SCOPE = "https://outlook.office.com/IMAP.AccessAsUser.All offline_access"
GRAPH_API_SCOPE = "https://graph.microsoft.com/.default"
GRAPH_API_BASE_URL = "https://graph.microsoft.com/v1.0"

# ============================================================================
# IMAP服务器配置
# ============================================================================

IMAP_SERVER = "outlook.live.com"
IMAP_PORT = 993

# ============================================================================
# 连接池配置
# ============================================================================

MAX_CONNECTIONS = 5
CONNECTION_TIMEOUT = 30
SOCKET_TIMEOUT = 15

# ============================================================================
# 缓存配置
# ============================================================================

CACHE_EXPIRE_TIME = 60  # 内存缓存过期时间（秒）

# LRU 缓存配置
MAX_CACHE_SIZE_MB = 500  # 最大缓存大小（MB）
MAX_EMAILS_CACHE_COUNT = 10000  # 最大邮件列表缓存数量
MAX_EMAIL_DETAILS_CACHE_COUNT = 5000  # 最大邮件详情缓存数量
LRU_CLEANUP_THRESHOLD = 0.9  # LRU清理阈值（90%时触发）

# 缓存预热配置
CACHE_WARMUP_ENABLED = True  # 是否启用缓存预热
CACHE_WARMUP_ACCOUNTS = 5  # 预热账户数量
CACHE_WARMUP_EMAILS_PER_ACCOUNT = 100  # 每个账户预热邮件数

# 正文压缩配置
COMPRESS_BODY_THRESHOLD = 1024  # 超过1KB的正文才压缩（字节）

# ============================================================================
# 日志配置
# ============================================================================

LOG_DIR = "logs"
LOG_FILE = "outlook_manager.log"
LOG_RETENTION_DAYS = 30

# 确保日志目录存在
Path(LOG_DIR).mkdir(exist_ok=True)

# ============================================================================
# 应用配置
# ============================================================================

APP_TITLE = "Outlook邮件API服务"
APP_DESCRIPTION = "基于FastAPI和IMAP协议的高性能邮件管理系统"
APP_VERSION = "2.0.0"

# 服务器配置
HOST = "0.0.0.0"
PORT = 8000

# ============================================================================
# 后台邮件同步配置
# ============================================================================

# 是否启用后台邮件自动同步
AUTO_SYNC_EMAILS_ENABLED = True

# 邮件同步间隔（秒）- 默认5分钟
EMAIL_SYNC_INTERVAL = 300

# 每次同步获取的邮件页数（page_size=100，即每次最多100封）
EMAIL_SYNC_PAGE_SIZE = 100

