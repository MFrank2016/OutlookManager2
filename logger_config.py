"""
日志配置模块

集中配置系统的日志记录器
"""

import logging
import os
from logging.handlers import TimedRotatingFileHandler

from config import LOG_DIR, LOG_FILE, LOG_RETENTION_DAYS


def setup_logger():
    """
    配置并返回日志记录器
    """
    # 获取根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 清除现有处理器
    logger.handlers.clear()

    # 文件处理器 - 按天轮转，保留指定天数
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(LOG_DIR, LOG_FILE),
        when="midnight",
        interval=1,
        backupCount=LOG_RETENTION_DAYS,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("Logging system initialized")
    
    return logger

