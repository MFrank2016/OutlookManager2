"""
IMAP连接池管理模块

提供连接复用、自动重连、连接状态监控等功能
优化IMAP连接性能，减少连接建立开销
"""

import imaplib
import logging
import socket
import ssl
import threading
from queue import Empty, Queue

from config import IMAP_SERVER, IMAP_PORT, MAX_CONNECTIONS, CONNECTION_TIMEOUT, SOCKET_TIMEOUT

# 获取日志记录器
logger = logging.getLogger(__name__)


class IMAPConnectionPool:
    """
    IMAP连接池管理器

    提供连接复用、自动重连、连接状态监控等功能
    优化IMAP连接性能，减少连接建立开销
    """

    def __init__(self, max_connections: int = MAX_CONNECTIONS):
        """
        初始化连接池

        Args:
            max_connections: 每个邮箱的最大连接数
        """
        self.max_connections = max_connections
        self.connections = {}  # {email: Queue of connections}
        self.connection_count = {}  # {email: active connection count}
        self.lock = threading.Lock()
        logger.info(
            f"Initialized IMAP connection pool with max_connections={max_connections}"
        )

    def _create_connection(self, email: str, access_token: str, retry_count: int = 0) -> imaplib.IMAP4_SSL:
        """
        创建新的IMAP连接（带重试机制）

        Args:
            email: 邮箱地址
            access_token: OAuth2访问令牌
            retry_count: 当前重试次数

        Returns:
            IMAP4_SSL: 已认证的IMAP连接

        Raises:
            Exception: 连接创建失败
        """
        max_retries = 2
        retry_delay = 1  # 秒
        
        try:
            # 设置全局socket超时
            socket.setdefaulttimeout(SOCKET_TIMEOUT)

            # 创建SSL IMAP连接
            imap_client = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)

            # 设置连接超时
            imap_client.sock.settimeout(CONNECTION_TIMEOUT)

            # XOAUTH2认证
            auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01".encode(
                "utf-8"
            )
            imap_client.authenticate("XOAUTH2", lambda _: auth_string)

            logger.info(f"Successfully created IMAP connection for {email}")
            return imap_client

        except Exception as e:
            # SSL错误或网络错误，可以重试
            error_msg = str(e).lower()
            error_type = type(e).__name__
            is_retryable = any(keyword in error_msg for keyword in [
                'unexpected_eof', 'eof', 'connection', 'timeout', 'reset', 
                'broken pipe', 'network', 'ssl', 'protocol'
            ]) or 'ssl' in error_type.lower()
            
            if is_retryable and retry_count < max_retries:
                logger.warning(
                    f"Failed to create IMAP connection for {email} (attempt {retry_count + 1}/{max_retries + 1}): {e}. Retrying..."
                )
                import time
                time.sleep(retry_delay * (retry_count + 1))  # 指数退避
                return self._create_connection(email, access_token, retry_count + 1)
            else:
                logger.error(f"Failed to create IMAP connection for {email} after {retry_count + 1} attempts: {e}")
                raise

    def get_connection(self, email: str, access_token: str) -> imaplib.IMAP4_SSL:
        """
        获取IMAP连接（从池中复用或创建新连接）

        Args:
            email: 邮箱地址
            access_token: OAuth2访问令牌

        Returns:
            IMAP4_SSL: 可用的IMAP连接

        Raises:
            Exception: 无法获取连接
        """
        with self.lock:
            # 初始化邮箱的连接池
            if email not in self.connections:
                self.connections[email] = Queue(maxsize=self.max_connections)
                self.connection_count[email] = 0

            connection_queue = self.connections[email]

            # 尝试从池中获取现有连接
            try:
                connection = connection_queue.get_nowait()
                # 测试连接有效性
                try:
                    connection.noop()
                    logger.debug(f"Reused existing IMAP connection for {email}")
                    return connection
                except Exception:
                    # 连接已失效，需要创建新连接
                    logger.debug(
                        f"Existing connection invalid for {email}, creating new one"
                    )
                    self.connection_count[email] -= 1
            except Empty:
                # 池中没有可用连接
                pass

            # 检查是否可以创建新连接
            if self.connection_count[email] < self.max_connections:
                connection = self._create_connection(email, access_token)
                self.connection_count[email] += 1
                return connection
            else:
                # 达到最大连接数，等待可用连接
                logger.warning(
                    f"Max connections ({self.max_connections}) reached for {email}, waiting..."
                )
                try:
                    return connection_queue.get(timeout=30)
                except Exception as e:
                    logger.error(f"Timeout waiting for connection for {email}: {e}")
                    raise

    def return_connection(self, email: str, connection: imaplib.IMAP4_SSL) -> None:
        """
        归还连接到池中

        Args:
            email: 邮箱地址
            connection: 要归还的IMAP连接
        """
        if email not in self.connections:
            logger.warning(
                f"Attempting to return connection for unknown email: {email}"
            )
            return

        try:
            # 测试连接状态
            connection.noop()
            # 连接有效，归还到池中
            self.connections[email].put_nowait(connection)
            logger.debug(f"Successfully returned IMAP connection for {email}")
        except Exception as e:
            # 连接已失效，减少计数并丢弃
            with self.lock:
                if email in self.connection_count:
                    self.connection_count[email] = max(
                        0, self.connection_count[email] - 1
                    )
            logger.debug(f"Discarded invalid connection for {email}: {e}")

    def close_all_connections(self, email: str = None) -> None:
        """
        关闭所有连接（带超时保护，防止卡住）

        Args:
            email: 指定邮箱地址，如果为None则关闭所有邮箱的连接
        """
        with self.lock:
            if email:
                # 关闭指定邮箱的所有连接
                if email in self.connections:
                    closed_count = 0
                    while not self.connections[email].empty():
                        try:
                            conn = self.connections[email].get_nowait()
                            
                            # 尝试优雅退出（带超时）
                            try:
                                # 设置短超时，防止卡住
                                original_timeout = conn.sock.gettimeout()
                                conn.sock.settimeout(2.0)  # 2秒超时
                                conn.logout()
                                closed_count += 1
                                logger.debug(f"Gracefully closed connection for {email}")
                            except socket.timeout:
                                # 超时，强制关闭
                                logger.warning(f"Logout timeout for {email}, forcing close")
                                try:
                                    conn.sock.shutdown(socket.SHUT_RDWR)
                                    conn.sock.close()
                                except:
                                    pass
                                closed_count += 1
                            except Exception as logout_err:
                                # logout失败，强制关闭socket
                                logger.debug(f"Logout failed for {email}: {logout_err}, forcing close")
                                try:
                                    if hasattr(conn, 'sock') and conn.sock:
                                        conn.sock.close()
                                except:
                                    pass
                                closed_count += 1
                                
                        except Exception as e:
                            logger.debug(f"Error closing connection for {email}: {e}")

                    self.connection_count[email] = 0
                    logger.info(f"Closed {closed_count} connections for {email}")
            else:
                # 关闭所有邮箱的连接
                total_closed = 0
                for email_key in list(self.connections.keys()):
                    count_before = self.connection_count.get(email_key, 0)
                    self.close_all_connections(email_key)
                    total_closed += count_before
                logger.info(f"Closed total {total_closed} connections for all accounts")


# 全局连接池实例
imap_pool = IMAPConnectionPool()

