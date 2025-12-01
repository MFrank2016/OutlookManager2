"""
DAO (Data Access Object) 层

提供统一的数据访问接口，每个表对应一个 DAO 类
"""

from .base_dao import BaseDAO, get_db_connection
from .account_dao import AccountDAO
from .user_dao import UserDAO
from .config_dao import ConfigDAO
from .email_cache_dao import EmailCacheDAO
from .email_detail_cache_dao import EmailDetailCacheDAO
from .share_token_dao import ShareTokenDAO
from .batch_import_task_dao import BatchImportTaskDAO, BatchImportTaskItemDAO

__all__ = [
    'BaseDAO',
    'get_db_connection',
    'AccountDAO',
    'UserDAO',
    'ConfigDAO',
    'EmailCacheDAO',
    'EmailDetailCacheDAO',
    'ShareTokenDAO',
    'BatchImportTaskDAO',
    'BatchImportTaskItemDAO',
]

