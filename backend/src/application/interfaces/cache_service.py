"""
缓存服务接口

定义缓存操作的抽象接口
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class ICacheService(ABC):
    """
    缓存服务接口
    
    定义缓存的基本操作
    具体实现在基础设施层（支持内存缓存和Redis）
    """
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Any | None: 缓存值或None
        """
        pass
    
    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示使用默认值
            
        Returns:
            bool: 是否设置成功
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        检查缓存是否存在
        
        Args:
            key: 缓存键
            
        Returns:
            bool: 是否存在
        """
        pass
    
    @abstractmethod
    async def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有缓存
        
        Args:
            pattern: 键模式（支持通配符*）
            
        Returns:
            int: 清除的数量
        """
        pass
    
    @abstractmethod
    async def get_ttl(self, key: str) -> Optional[int]:
        """
        获取缓存剩余有效期
        
        Args:
            key: 缓存键
            
        Returns:
            int | None: 剩余秒数，None表示不存在或永久有效
        """
        pass

