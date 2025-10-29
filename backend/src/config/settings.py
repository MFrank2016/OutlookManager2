"""
应用配置管理

使用Pydantic Settings管理所有配置项
支持从环境变量和.env文件读取配置
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""
    
    # ============================================================================
    # 应用基础配置
    # ============================================================================
    APP_NAME: str = "Outlook Email Manager"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = False
    ENV: str = Field(default="development", description="运行环境: development/production/test")
    
    # ============================================================================
    # 数据库配置
    # ============================================================================
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data.db",
        description="数据库连接URL"
    )
    DATABASE_POOL_SIZE: int = Field(default=5, ge=1, le=50)
    DATABASE_MAX_OVERFLOW: int = Field(default=10, ge=0, le=50)
    DATABASE_ECHO: bool = False  # 是否输出SQL日志
    
    # ============================================================================
    # JWT认证配置
    # ============================================================================
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-this-in-production",
        description="JWT密钥，生产环境必须修改"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = Field(default=24, ge=1, le=720)
    JWT_REFRESH_EXPIRE_DAYS: int = Field(default=30, ge=1, le=365)
    
    # ============================================================================
    # IMAP配置
    # ============================================================================
    IMAP_SERVER: str = "outlook.office365.com"
    IMAP_PORT: int = Field(default=993, ge=1, le=65535)
    MAX_IMAP_CONNECTIONS: int = Field(default=5, ge=1, le=20)
    IMAP_CONNECTION_TIMEOUT: int = Field(default=30, ge=5, le=120)
    IMAP_SOCKET_TIMEOUT: int = Field(default=15, ge=5, le=60)
    
    # ============================================================================
    # OAuth2配置
    # ============================================================================
    OAUTH_TOKEN_URL: str = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    OAUTH_SCOPE: str = "https://outlook.office.com/IMAP.AccessAsUser.All offline_access"
    OAUTH_TIMEOUT: int = Field(default=30, ge=5, le=120)
    
    # ============================================================================
    # 缓存配置
    # ============================================================================
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = Field(default=60, ge=10, le=3600, description="缓存过期时间（秒）")
    REDIS_URL: Optional[str] = Field(default=None, description="Redis连接URL，为空则使用内存缓存")
    REDIS_MAX_CONNECTIONS: int = Field(default=10, ge=1, le=50)
    
    # ============================================================================
    # CORS配置
    # ============================================================================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="允许的跨域来源"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # ============================================================================
    # 日志配置
    # ============================================================================
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_DIR: str = Field(default="logs", description="日志目录")
    LOG_FILE: str = Field(default="outlook_manager.log", description="日志文件名")
    LOG_RETENTION_DAYS: int = Field(default=30, ge=1, le=365)
    LOG_FORMAT: str = "%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s"
    
    # ============================================================================
    # API配置
    # ============================================================================
    API_V1_PREFIX: str = "/api/v1"
    API_DOCS_ENABLED: bool = True  # 是否启用API文档
    API_RATE_LIMIT_ENABLED: bool = True
    API_RATE_LIMIT_REQUESTS: int = Field(default=100, ge=10, le=1000, description="每分钟最大请求数")
    
    # ============================================================================
    # 安全配置
    # ============================================================================
    SECRET_KEY: str = Field(
        default="change-this-secret-key-in-production",
        description="应用密钥"
    )
    ALLOWED_HOSTS: List[str] = Field(default=["*"])
    HTTPS_ONLY: bool = False  # 生产环境应设为True
    
    # ============================================================================
    # 邮件处理配置
    # ============================================================================
    EMAIL_PAGE_SIZE: int = Field(default=100, ge=10, le=500, description="邮件列表每页大小")
    EMAIL_MAX_FETCH_SIZE: int = Field(default=1000, ge=100, le=5000, description="单次最大获取邮件数")
    EMAIL_FOLDERS: List[str] = Field(default=["INBOX", "Junk"], description="要同步的邮件文件夹")
    
    # ============================================================================
    # Token刷新配置
    # ============================================================================
    TOKEN_REFRESH_INTERVAL_DAYS: int = Field(default=3, ge=1, le=30, description="Token刷新间隔（天）")
    TOKEN_REFRESH_RETRY_TIMES: int = Field(default=3, ge=1, le=10, description="Token刷新重试次数")
    
    # ============================================================================
    # 性能配置
    # ============================================================================
    ENABLE_ASYNC_PROCESSING: bool = True  # 启用异步处理
    MAX_WORKERS: int = Field(default=4, ge=1, le=16, description="最大工作线程数")
    BACKGROUND_TASK_INTERVAL: int = Field(default=3600, ge=60, le=86400, description="后台任务执行间隔（秒）")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # 忽略额外的环境变量
    )
    
    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别"""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v_upper
    
    @field_validator("ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        """验证运行环境"""
        allowed_envs = ["development", "production", "test"]
        v_lower = v.lower()
        if v_lower not in allowed_envs:
            raise ValueError(f"ENV must be one of {allowed_envs}")
        return v_lower
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.ENV == "production"
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.ENV == "development"
    
    def is_test(self) -> bool:
        """是否为测试环境"""
        return self.ENV == "test"


@lru_cache()
def get_settings() -> Settings:
    """
    获取配置实例（单例模式）
    
    使用lru_cache装饰器确保整个应用只有一个配置实例
    """
    return Settings()


# 便捷访问
settings = get_settings()

