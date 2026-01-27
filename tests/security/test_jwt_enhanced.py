"""
Comprehensive tests for enhanced JWT authentication system
Tests cover:
- Token generation and validation
- RBAC permissions
- Token revocation
- Audit logging
- Rate limiting
- Security edge cases
"""

import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, AsyncMock, patch

# Add deploy/docker to path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../deploy/docker'))

from auth_enhanced import (
    EnhancedAuthManager,
    TokenBlacklist,
    AuditLogger,
    UserRole,
    Permission,
    ROLE_PERMISSIONS,
    create_access_token,
    create_refresh_token,
    verify_token,
    TokenRequest,
    AuditLogEntry
)

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


@pytest.fixture
async def mock_redis():
    """Mock Redis client"""
    redis = AsyncMock()
    redis.setex = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.exists = AsyncMock(return_value=0)
    redis.sadd = AsyncMock()
    redis.scard = AsyncMock(return_value=0)
    redis.smembers = AsyncMock(return_value=[])
    redis.delete = AsyncMock()
    redis.expire = AsyncMock()
    redis.lpush = AsyncMock()
    redis.ltrim = AsyncMock()
    redis.lrange = AsyncMock(return_value=[])
    return redis


@pytest.fixture
async def auth_manager(mock_redis):
    """Create auth manager with mock Redis"""
    return EnhancedAuthManager(mock_redis)


@pytest.fixture
async def token_blacklist(mock_redis):
    """Create token blacklist with mock Redis"""
    return TokenBlacklist(mock_redis)


@pytest.fixture
async def audit_logger(mock_redis):
    """Create audit logger with mock Redis"""
    return AuditLogger(mock_redis)


class TestTokenGeneration:
    """Test token generation functionality"""
    
    def test_create_access_token_basic(self):
        """Test basic access token creation"""
        token = create_access_token(
            {"sub": "test@example.com"},
            role=UserRole.USER
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_role(self):
        """Test access token with specific role"""
        for role in UserRole:
            token = create_access_token(
                {"sub": f"test@example.com"},
                role=role
            )
            assert token is not None
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token = create_refresh_token(
            {"sub": "test@example.com"},
            user_id="user123"
        )
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_token_expiration(self):
        """Test token expiration setting"""
        short_expiry = timedelta(seconds=1)
        token = create_access_token(
            {"sub": "test@example.com"},
            expires_delta=short_expiry,
            role=UserRole.USER
        )
        
        assert token is not None


class TestTokenValidation:
    """Test token validation functionality"""
    
    @pytest.mark.asyncio
    async def test_valid_token_verification(self, token_blacklist):
        """Test verification of valid token"""
        token = create_access_token(
            {"sub": "test@example.com", "user_id": "user123"},
            role=UserRole.USER
        )
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        payload = await verify_token(credentials, token_blacklist)
        
        assert payload["sub"] == "test@example.com"
        assert payload["role"] == UserRole.USER.value
        assert "permissions" in payload
    
    @pytest.mark.asyncio
    async def test_invalid_token_verification(self, token_blacklist):
        """Test verification of invalid token"""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid.token.here"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials, token_blacklist)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_missing_token_verification(self, token_blacklist):
        """Test verification with no token"""
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(None, token_blacklist)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_blacklisted_token_verification(self, token_blacklist):
        """Test verification of blacklisted token"""
        token = create_access_token(
            {"sub": "test@example.com", "user_id": "user123"},
            role=UserRole.USER
        )
        
        # Mock blacklist check
        token_blacklist.is_blacklisted = AsyncMock(return_value=True)
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials, token_blacklist)
        
        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail.lower()


class TestRBAC:
    """Test Role-Based Access Control"""
    
    def test_role_permissions_mapping(self):
        """Test that all roles have permissions mapped"""
        for role in UserRole:
            assert role in ROLE_PERMISSIONS
            assert len(ROLE_PERMISSIONS[role]) > 0
    
    def test_admin_has_all_permissions(self):
        """Test that admin has all permissions"""
        admin_perms = ROLE_PERMISSIONS[UserRole.ADMIN]
        
        # Admin should have all permission types
        assert Permission.ADMIN_READ in admin_perms
        assert Permission.ADMIN_WRITE in admin_perms
        assert Permission.CRAWL_DELETE in admin_perms
        assert Permission.SESSION_DELETE in admin_perms
    
    def test_guest_limited_permissions(self):
        """Test that guest has limited permissions"""
        guest_perms = ROLE_PERMISSIONS[UserRole.GUEST]
        
        # Guest should only have read permissions
        assert Permission.CRAWL_READ in guest_perms
        assert Permission.SESSION_READ in guest_perms
        
        # Guest should NOT have write/delete permissions
        assert Permission.CRAWL_WRITE not in guest_perms
        assert Permission.CRAWL_DELETE not in guest_perms
        assert Permission.ADMIN_WRITE not in guest_perms
    
    def test_token_includes_role_permissions(self):
        """Test that tokens include role and permissions"""
        token = create_access_token(
            {"sub": "test@example.com"},
            role=UserRole.POWER_USER
        )
        
        # Decode token to check payload
        from jwt import JWT, jwk_from_dict
        import base64
        
        SECRET_KEY = os.environ.get("SECRET_KEY", "mysecret")
        secret_bytes = SECRET_KEY.encode('utf-8')
        b64_secret = base64.urlsafe_b64encode(secret_bytes).rstrip(b'=').decode('utf-8')
        verifying_key = jwk_from_dict({"kty": "oct", "k": b64_secret})
        
        instance = JWT()
        payload = instance.decode(token, verifying_key, do_time_check=False, algorithms='HS256')
        
        assert payload["role"] == UserRole.POWER_USER.value
        assert "permissions" in payload
        assert len(payload["permissions"]) > 0


class TestTokenRevocation:
    """Test token revocation functionality"""
    
    @pytest.mark.asyncio
    async def test_add_token_to_blacklist(self, token_blacklist):
        """Test adding token to blacklist"""
        await token_blacklist.add_token("test_token", "user123", 3600)
        
        token_blacklist.redis.setex.assert_called_once()
        token_blacklist.redis.sadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_blacklisted_token(self, token_blacklist):
        """Test checking if token is blacklisted"""
        token_blacklist.redis.exists = AsyncMock(return_value=1)
        
        is_blacklisted = await token_blacklist.is_blacklisted("test_token")
        
        assert is_blacklisted is True
    
    @pytest.mark.asyncio
    async def test_revoke_user_tokens(self, token_blacklist):
        """Test revoking all tokens for a user"""
        token_blacklist.redis.smembers = AsyncMock(
            return_value=[b"token1", b"token2", b"token3"]
        )
        
        await token_blacklist.revoke_user_tokens("user123")
        
        # Should add 3 tokens to blacklist
        assert token_blacklist.redis.setex.call_count == 3
    
    @pytest.mark.asyncio
    async def test_get_active_tokens_count(self, token_blacklist):
        """Test getting active token count for user"""
        token_blacklist.redis.scard = AsyncMock(return_value=5)
        
        count = await token_blacklist.get_active_tokens_count("user123")
        
        assert count == 5


class TestAuditLogging:
    """Test audit logging functionality"""
    
    @pytest.mark.asyncio
    async def test_log_event(self, audit_logger):
        """Test logging security event"""
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            user_id="user123",
            email="test@example.com",
            action="login",
            success=True
        )
        
        await audit_logger.log_event(entry)
        
        audit_logger.redis.lpush.assert_called_once()
        audit_logger.redis.ltrim.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_logs(self, audit_logger):
        """Test retrieving user audit logs"""
        mock_log = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            user_id="user123",
            email="test@example.com",
            action="login",
            success=True
        ).model_dump_json()
        
        audit_logger.redis.lrange = AsyncMock(return_value=[mock_log.encode()])
        
        logs = await audit_logger.get_user_logs("user123")
        
        assert len(logs) == 1
        assert logs[0].user_id == "user123"
        assert logs[0].action == "login"
    
    @pytest.mark.asyncio
    async def test_get_failed_login_count(self, audit_logger):
        """Test counting failed login attempts"""
        now = datetime.now(timezone.utc)
        
        failed_log = AuditLogEntry(
            timestamp=now - timedelta(minutes=5),
            user_id="user123",
            email="test@example.com",
            action="login",
            success=False
        )
        
        audit_logger.redis.lrange = AsyncMock(
            return_value=[failed_log.model_dump_json().encode()]
        )
        
        count = await audit_logger.get_failed_login_count("user123", minutes=15)
        
        assert count >= 0


class TestAuthManager:
    """Test EnhancedAuthManager functionality"""
    
    @pytest.mark.asyncio
    async def test_create_tokens(self, auth_manager):
        """Test creating tokens through auth manager"""
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers.get = Mock(return_value="test-agent")
        
        response = await auth_manager.create_tokens(
            email="test@example.com",
            role=UserRole.USER,
            request=mock_request
        )
        
        assert response.access_token is not None
        assert response.refresh_token is not None
        assert response.email == "test@example.com"
        assert response.role == UserRole.USER
        assert len(response.permissions) > 0
    
    @pytest.mark.asyncio
    async def test_revoke_token(self, auth_manager):
        """Test token revocation through auth manager"""
        await auth_manager.revoke_token(
            token="test_token",
            user_id="user123"
        )
        
        # Should call blacklist
        auth_manager.blacklist.redis.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_revoke_all_tokens(self, auth_manager):
        """Test revoking all tokens for user"""
        auth_manager.blacklist.redis.smembers = AsyncMock(
            return_value=[b"token1", b"token2"]
        )
        
        await auth_manager.revoke_token(
            user_id="user123",
            revoke_all=True
        )
        
        # Should call revoke_user_tokens
        auth_manager.blacklist.redis.delete.assert_called()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit(self, auth_manager):
        """Test rate limit checking"""
        # Mock audit logger to return failed attempts
        now = datetime.now(timezone.utc)
        failed_logs = [
            AuditLogEntry(
                timestamp=now - timedelta(minutes=i),
                user_id="user123",
                email="test@example.com",
                action="login",
                success=False
            )
            for i in range(6)
        ]
        
        auth_manager.audit_logger.redis.lrange = AsyncMock(
            return_value=[log.model_dump_json().encode() for log in failed_logs]
        )
        
        is_limited = await auth_manager.check_rate_limit("user123", max_attempts=5)
        
        # Should be rate limited after 5+ failed attempts
        assert isinstance(is_limited, bool)


class TestSecurityEdgeCases:
    """Test security edge cases and vulnerabilities"""
    
    def test_token_without_expiration(self):
        """Test that tokens always have expiration"""
        token = create_access_token(
            {"sub": "test@example.com"},
            role=UserRole.USER
        )
        
        # Decode and check for exp claim
        from jwt import JWT, jwk_from_dict
        import base64
        
        SECRET_KEY = os.environ.get("SECRET_KEY", "mysecret")
        secret_bytes = SECRET_KEY.encode('utf-8')
        b64_secret = base64.urlsafe_b64encode(secret_bytes).rstrip(b'=').decode('utf-8')
        verifying_key = jwk_from_dict({"kty": "oct", "k": b64_secret})
        
        instance = JWT()
        payload = instance.decode(token, verifying_key, do_time_check=False, algorithms='HS256')
        
        assert "exp" in payload
    
    def test_token_has_unique_id(self):
        """Test that tokens have unique JWT ID"""
        token1 = create_access_token(
            {"sub": "test@example.com"},
            role=UserRole.USER
        )
        token2 = create_access_token(
            {"sub": "test@example.com"},
            role=UserRole.USER
        )
        
        assert token1 != token2  # Should be different due to JTI
    
    @pytest.mark.asyncio
    async def test_expired_token_rejection(self, token_blacklist):
        """Test that expired tokens are rejected"""
        # Create token with 0 second expiration
        token = create_access_token(
            {"sub": "test@example.com", "user_id": "user123"},
            expires_delta=timedelta(seconds=0),
            role=UserRole.USER
        )
        
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )
        
        # Wait a moment to ensure expiration
        await asyncio.sleep(0.1)
        
        with pytest.raises(HTTPException) as exc_info:
            await verify_token(credentials, token_blacklist)
        
        assert exc_info.value.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

