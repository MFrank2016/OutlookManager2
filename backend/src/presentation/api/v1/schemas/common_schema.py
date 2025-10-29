"""
通用API Schemas

定义通用的请求和响应Schema
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# 泛型类型变量
T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页参数Schema"""
    
    page: int = Field(default=1, ge=1, description="页码（从1开始）")
    page_size: int = Field(default=20, ge=1, le=500, description="每页大小")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应Schema"""
    
    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页")
    page_size: int = Field(description="每页大小")
    total_pages: int = Field(description="总页数")
    
    @classmethod
    def create(cls, items: List[T], total: int, page: int, page_size: int):
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class SuccessResponse(BaseModel, Generic[T]):
    """成功响应Schema"""
    
    success: bool = Field(default=True, description="是否成功")
    message: str = Field(description="消息")
    data: Optional[T] = Field(default=None, description="数据")


class ErrorResponse(BaseModel):
    """错误响应Schema"""
    
    success: bool = Field(default=False, description="是否成功")
    error_code: str = Field(description="错误码")
    message: str = Field(description="错误消息")
    details: Optional[dict] = Field(default=None, description="错误详情")


class HealthResponse(BaseModel):
    """健康检查响应Schema"""
    
    status: str = Field(description="服务状态")
    version: str = Field(description="应用版本")
    timestamp: str = Field(description="当前时间戳")

