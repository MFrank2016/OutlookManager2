"""
日志配置模块

使用loguru集中配置系统的日志记录器
支持滚动日志：保留7天，最大50MB
"""

import sys
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from config import LOG_DIR, LOG_FILE, LOG_RETENTION_DAYS, LOG_MAX_SIZE


# ============================================================================
# API日志记录辅助函数
# ============================================================================

def truncate_text(text: str, max_length: int = 1000) -> str:
    """
    截断文本到指定长度，如果被截断则添加提示
    
    Args:
        text: 要截断的文本
        max_length: 最大长度
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + f"... [truncated, total length: {len(text)}]"


def serialize_request_params(request) -> Dict[str, Any]:
    """
    序列化请求参数（Query、Path、Body）
    
    Args:
        request: FastAPI Request对象
        
    Returns:
        包含请求参数的字典
    """
    params = {
        "query_params": dict(request.query_params),
        "path_params": dict(request.path_params),
    }
    
    # 尝试获取请求体（如果是JSON）
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            # 检查Content-Type
            content_type = request.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                # 注意：这里不能直接读取body，因为stream已经被消费
                # 实际读取将在中间件中通过request.state保存
                params["has_json_body"] = True
        except Exception:
            pass
    
    return params


def format_request_log(request, body: Optional[str] = None) -> str:
    """
    格式化请求日志
    
    Args:
        request: FastAPI Request对象
        body: 请求体内容（可选）
        
    Returns:
        格式化的日志字符串
    """
    client_host = request.client.host if request.client else 'unknown'
    params = serialize_request_params(request)
    
    log_parts = [
        f"→ {request.method} {request.url.path}",
        f"Client: {client_host}",
    ]
    
    if params["query_params"]:
        log_parts.append(f"Query: {params['query_params']}")
    
    if params["path_params"]:
        log_parts.append(f"Path: {params['path_params']}")
    
    if body:
        truncated_body = truncate_text(body, 1000)
        log_parts.append(f"Body: {truncated_body}")
    
    return " | ".join(log_parts)


def format_response_log(status_code: int, body: Optional[str] = None, elapsed_time: float = 0.0) -> str:
    """
    格式化响应日志
    
    Args:
        status_code: HTTP状态码
        body: 响应体内容（可选）
        elapsed_time: 处理时间（秒）
        
    Returns:
        格式化的日志字符串
    """
    log_parts = [
        f"← Status: {status_code}",
        f"Time: {elapsed_time:.3f}s",
    ]
    
    if body:
        truncated_body = truncate_text(body, 1000)
        log_parts.append(f"Response: {truncated_body}")
    
    return " | ".join(log_parts)


# ============================================================================
# Loguru配置
# ============================================================================

def setup_logger():
    """
    配置并返回loguru日志记录器
    
    Returns:
        loguru logger实例
    """
    # 移除默认handler
    logger.remove()
    
    # 确保日志目录存在
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    
    log_file_path = os.path.join(LOG_DIR, LOG_FILE)
    
    # 配置日志格式（Asia/Shanghai时区会在loguru中自动处理）
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 添加控制台输出
    logger.add(
        sys.stderr,
        format=log_format,
        level="DEBUG",
        colorize=True,
        enqueue=True,  # 异步写入，提高性能
    )
    
    # 添加文件输出（滚动日志）
    logger.add(
        log_file_path,
        format=log_format,
        level="INFO",
        rotation=LOG_MAX_SIZE,  # 文件大小达到50MB时滚动
        retention=f"{LOG_RETENTION_DAYS} days",  # 保留7天的日志
        compression="zip",  # 压缩旧日志文件
        encoding="utf-8",
        enqueue=True,  # 异步写入，提高性能
        backtrace=True,  # 记录完整的异常堆栈
        diagnose=True,  # 记录变量值以帮助调试
    )
    
    logger.info("Loguru logging system initialized")
    
    return logger


# 初始化logger（供其他模块直接导入使用）
logger = setup_logger()
