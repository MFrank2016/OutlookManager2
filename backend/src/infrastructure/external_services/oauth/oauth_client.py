"""
OAuth2客户端实现

处理Microsoft OAuth2认证和Token刷新
"""

import logging
from typing import Optional

import httpx

from src.application.interfaces import IOAuthClient
from src.config.settings import settings
from src.domain.exceptions import InvalidRefreshTokenException, OAuthException
from src.domain.value_objects import AccessToken, Credentials

logger = logging.getLogger(__name__)


class OAuthClientImpl(IOAuthClient):
    """OAuth2客户端实现"""
    
    def __init__(self):
        """初始化OAuth客户端"""
        self._token_url = settings.OAUTH_TOKEN_URL
        self._scope = settings.OAUTH_SCOPE
        self._timeout = settings.OAUTH_TIMEOUT
    
    async def refresh_token(
        self,
        credentials: Credentials
    ) -> tuple[AccessToken, Optional[str]]:
        """刷新访问令牌"""
        logger.info(f"Refreshing token for client_id: {credentials.client_id[:10]}...")
        
        # 构建请求参数
        data = {
            "client_id": credentials.client_id,
            "refresh_token": credentials.refresh_token,
            "grant_type": "refresh_token",
            "scope": self._scope
        }
        
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"OAuth refresh failed: {response.status_code} - {error_detail}")
                    
                    # 判断是否为无效的refresh_token
                    if response.status_code in [400, 401]:
                        raise InvalidRefreshTokenException(
                            credentials.client_id,
                            f"HTTP {response.status_code}: {error_detail}"
                        )
                    
                    raise OAuthException(
                        f"HTTP {response.status_code}: {error_detail}",
                        {"status_code": response.status_code, "detail": error_detail}
                    )
                
                # 解析响应
                token_data = response.json()
                
                # 创建访问令牌值对象
                access_token = AccessToken.create(
                    value=token_data["access_token"],
                    expires_in=token_data.get("expires_in", 3600),
                    token_type=token_data.get("token_type", "Bearer")
                )
                
                # 获取新的refresh_token（如果有）
                new_refresh_token = token_data.get("refresh_token")
                
                logger.info("Token refreshed successfully")
                
                return access_token, new_refresh_token
                
        except httpx.TimeoutException as e:
            logger.error(f"OAuth request timeout: {str(e)}")
            raise OAuthException("Request timeout", {"error": str(e)})
        except httpx.HTTPError as e:
            logger.error(f"OAuth HTTP error: {str(e)}")
            raise OAuthException(f"HTTP error: {str(e)}", {"error": str(e)})
        except KeyError as e:
            logger.error(f"Invalid OAuth response format: {str(e)}")
            raise OAuthException(
                f"Invalid response format: missing {str(e)}",
                {"error": str(e)}
            )
    
    async def validate_token(self, access_token: AccessToken) -> bool:
        """验证访问令牌是否有效"""
        # 简单实现：检查是否过期
        return access_token.is_valid()
    
    async def revoke_token(self, refresh_token: str) -> bool:
        """
        撤销刷新令牌
        
        注意：Microsoft OAuth2不直接支持token撤销
        这里返回True作为占位实现
        """
        logger.info("Token revocation requested (not supported by Microsoft OAuth2)")
        return True

