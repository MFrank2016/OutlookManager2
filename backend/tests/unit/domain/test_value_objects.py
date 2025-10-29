"""
值对象单元测试
"""

import pytest

from src.domain.exceptions import ValidationException
from src.domain.value_objects import AccessToken, Credentials, EmailAddress


class TestEmailAddress:
    """测试EmailAddress值对象"""
    
    def test_create_valid_email(self):
        """测试创建有效邮箱地址"""
        email = EmailAddress.create("test@outlook.com")
        assert str(email) == "test@outlook.com"
    
    def test_create_invalid_email(self):
        """测试创建无效邮箱地址应抛出异常"""
        with pytest.raises(ValidationException):
            EmailAddress.create("invalid-email")
    
    def test_email_normalization(self):
        """测试邮箱地址规范化（转小写）"""
        email = EmailAddress.create("Test@Outlook.COM")
        assert str(email) == "test@outlook.com"
    
    def test_get_domain(self):
        """测试获取域名"""
        email = EmailAddress.create("user@outlook.com")
        assert email.get_domain() == "outlook.com"
    
    def test_get_local_part(self):
        """测试获取本地部分"""
        email = EmailAddress.create("user@outlook.com")
        assert email.get_local_part() == "user"
    
    def test_is_outlook(self):
        """测试判断是否为Outlook邮箱"""
        email1 = EmailAddress.create("user@outlook.com")
        assert email1.is_outlook() is True
        
        email2 = EmailAddress.create("user@gmail.com")
        assert email2.is_outlook() is False
    
    def test_immutability(self):
        """测试不可变性"""
        email = EmailAddress.create("test@outlook.com")
        
        # 尝试修改应该失败（dataclass frozen=True）
        with pytest.raises(Exception):
            email.value = "new@outlook.com"


class TestCredentials:
    """测试Credentials值对象"""
    
    def test_create_valid_credentials(self):
        """测试创建有效凭证"""
        creds = Credentials.create(
            client_id="client_12345678",
            refresh_token="refresh_12345678"
        )
        assert creds.client_id == "client_12345678"
        assert creds.refresh_token == "refresh_12345678"
    
    def test_create_invalid_client_id(self):
        """测试创建无效client_id应抛出异常"""
        with pytest.raises(ValidationException):
            Credentials.create(client_id="", refresh_token="valid_token")
    
    def test_create_invalid_refresh_token(self):
        """测试创建无效refresh_token应抛出异常"""
        with pytest.raises(ValidationException):
            Credentials.create(client_id="valid_client", refresh_token="")
    
    def test_mask_refresh_token(self):
        """测试掩码refresh_token"""
        creds = Credentials.create(
            client_id="client_123",
            refresh_token="very_long_refresh_token_12345"
        )
        masked = creds.mask_refresh_token(visible_chars=5)
        assert masked == "very_...***"


class TestAccessToken:
    """测试AccessToken值对象"""
    
    def test_create_token(self):
        """测试创建访问令牌"""
        token = AccessToken.create(
            value="access_token_12345",
            expires_in=3600
        )
        assert token.value == "access_token_12345"
        assert token.token_type == "Bearer"
    
    def test_is_valid_fresh_token(self):
        """测试刚创建的Token应该是有效的"""
        token = AccessToken.create(
            value="access_token_12345",
            expires_in=3600
        )
        assert token.is_valid() is True
        assert token.is_expired() is False
    
    def test_is_expired_old_token(self):
        """测试过期的Token"""
        from datetime import datetime, timedelta
        
        # 创建已过期的Token
        expired_time = datetime.utcnow() - timedelta(hours=1)
        token = AccessToken.create_with_expiry(
            value="expired_token",
            expires_at=expired_time
        )
        assert token.is_expired() is True
        assert token.is_valid() is False
    
    def test_time_until_expiry(self):
        """测试计算到期时间"""
        token = AccessToken.create(
            value="access_token",
            expires_in=3600
        )
        seconds = token.seconds_until_expiry()
        # 应该接近3600秒（允许几秒误差）
        assert 3595 <= seconds <= 3600
    
    def test_mask_value(self):
        """测试掩码token值"""
        token = AccessToken.create(
            value="very_long_access_token_value",
            expires_in=3600
        )
        masked = token.mask_value(visible_chars=10)
        assert masked == "very_long_...***"


# 运行测试的命令：
# pytest tests/unit/domain/test_value_objects.py -v

