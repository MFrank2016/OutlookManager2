"""
日志配置

配置结构化日志系统
"""

import logging
import sys
from pathlib import Path

from src.config.settings import settings


def setup_logging() -> None:
    """
    配置日志系统
    
    设置日志格式、级别和处理器
    """
    # 确保日志目录存在
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置根日志记录器
    logging.basicConfig(
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        handlers=[
            # 控制台处理器
            logging.StreamHandler(sys.stdout),
            # 文件处理器
            logging.FileHandler(
                log_dir / settings.LOG_FILE,
                encoding="utf-8"
            )
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("aioimaplib").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={settings.LOG_LEVEL}, file={settings.LOG_FILE}")


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)

