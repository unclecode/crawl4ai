"""
Enhanced JWT Authentication System with RBAC
Provides production-ready authentication with:
- Access & Refresh tokens
- Role-Based Access Control (RBAC)
- Token revocation/blacklisting
- Audit logging
- Rate limiting per user
"""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List, Set
from enum import Enum

from jwt import JWT, jwk_from_dict
from jwt.utils import get_int_from_datetime
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import EmailStr, BaseModel, Field
import base64
import logging
from redis import asyncio as aioredis

logger = logging.getLogger(__name__)

# JWT Configuration
instance = JWT()
security = HTTPBearer(auto_error=False)
SECRET_KEY = os.environ.get("SECRET_KEY", "mysecret")
REFRESH_SECRET_KEY = os.environ.get("REFRESH_SECRET_KEY", "myrefreshsecret")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "30"))


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    POWER_USER = "power_user"
    USER = "user"
    GUEST = "guest"


class Permission(str, Enum):
    """Permissions for fine-grained access control"""
    CRAWL_READ = "crawl:read"
    CRAWL_WRITE = "crawl:write"
    CRAWL_DELETE = "crawl:delete"
    SESSION_READ = "session:read"
    SESSION_WRITE = "session:write"
    SESSION_DELETE = "session:delete"
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    EXPORT_DATA = "export:data"
    ANALYTICS_VIEW = "analytics:view"


# Role-Permission Mapping
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        Permission.CRAWL_READ, Permission.CRAWL_WRITE, Permission.CRAWL_DELETE,
        Permission.SESSION_READ, Permission.SESSION_WRITE, Permission.SESSION_DELETE,
        Permission.ADMIN_READ, Permission.ADMIN_WRITE,
        Permission.EXPORT_DATA, Permission.ANALYTICS_VIEW
    },
    UserRole.POWER_USER: {
        Permission.CRAWL_READ, Permission.CRAWL_WRITE, Permission.CRAWL_DELETE,
        Permission.SESSION_READ, Permission.SESSION_WRITE, Permission.SESSION_DELETE,
        Permission.EXPORT_DATA, Permission.ANALYTICS_VIEW
    },
    UserRole.USER: {
        Permission.CRAWL_READ, Permission.CRAWL_WRITE,
        Permission.SESSION_READ, Permission.SESSION_WRITE,
        Permission.EXPORT_DATA
    },
    UserRole.GUEST: {
        Permission.CRAWL_READ,
        Permission.SESSION_READ
    }
}


class TokenRequest(BaseModel):
    """Request model for token generation"""
    email: EmailStr
    password: Optional[str] = None
    role: Optional[UserRole] = UserRole.USER


class TokenResponse(BaseModel):
    """Response model for token generation"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str
    role: UserRole
    permissions: List[str]


class RefreshTokenRequest(BaseModel):
    """Request model for token refresh"""
    refresh_token: str


class TokenRevocationRequest(BaseModel):
    """Request model for token revocation"""
    token: Optional[str] = None
    user_id: Optional[str] = None
    revoke_all: bool = False


class AuditLogEntry(BaseModel):
    """Audit log entry for security events"""
    timestamp: datetime
    user_id: str
    email: str
    action: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool
    details: Optional[Dict] = None


class TokenBlacklist:
    """Redis-backed token blacklist for revocation"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.prefix = "token_blacklist:"
        self.user_tokens_prefix = "user_tokens:"
    
    async def add_token(self, token: str, user_id: str, expires_in: int):
        """Add token to blacklist"""
        key = f"{self.prefix}{token}"
        await self.redis.setex(key, expires_in, user_id)
        
        # Track tokens per user
        user_key = f"{self.user_tokens_prefix}{user_id}"
        await self.redis.sadd(user_key, token)
        await self.redis.expire(user_key, expires_in)
    
    async def is_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        key = f"{self.prefix}{token}"
        return await self.redis.exists(key) > 0
    
    async def revoke_user_tokens(self, user_id: str):
        """Revoke all tokens for a user"""
        user_key = f"{self.user_tokens_prefix}{user_id}"
        tokens = await self.redis.smembers(user_key)
        
        for token in tokens:
            await self.add_token(token.decode(), user_id, ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        
        await self.redis.delete(user_key)
        logger.info(f"Revoked {len(tokens)} tokens for user {user_id}")
    
    async def get_active_tokens_count(self, user_id: str) -> int:
        """Get count of active tokens for user"""
        user_key = f"{self.user_tokens_prefix}{user_id}"
        return await self.redis.scard(user_key)


class AuditLogger:
    """Redis-backed audit logger for security events"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.prefix = "audit_log:"
        self.max_entries = 10000
    
    async def log_event(self, entry: AuditLogEntry):
        """Log security event"""
        key = f"{self.prefix}{entry.user_id}"
        log_entry = entry.model_dump_json()
        
        await self.redis.lpush(key, log_entry)
        await self.redis.ltrim(key, 0, self.max_entries - 1)
        
        # Set expiration (90 days)
        await self.redis.expire(key, 90 * 24 * 60 * 60)
        
        logger.info(f"Audit: {entry.action} by {entry.email} - Success: {entry.success}")
    
    async def get_user_logs(self, user_id: str, limit: int = 100) -> List[AuditLogEntry]:
        """Get audit logs for user"""
        key = f"{self.prefix}{user_id}"
        logs = await self.redis.lrange(key, 0, limit - 1)
        
        return [AuditLogEntry.model_validate_json(log) for log in logs]
    
    async def get_failed_login_count(self, user_id: str, minutes: int = 15) -> int:
        """Get failed login attempts in last N minutes"""
        logs = await self.get_user_logs(user_id, 50)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        failed_logins = [
            log for log in logs 
            if log.action == "login" 
            and not log.success 
            and log.timestamp > cutoff
        ]
        
        return len(failed_logins)


def get_jwk_from_secret(secret: str):
    """Convert a secret string into a JWK object"""
    secret_bytes = secret.encode('utf-8')
    b64_secret = base64.urlsafe_b64encode(secret_bytes).rstrip(b'=').decode('utf-8')
    return jwk_from_dict({"kty": "oct", "k": b64_secret})


def create_access_token(
    data: dict, 
    expires_delta: Optional[timedelta] = None,
    role: UserRole = UserRole.USER
) -> str:
    """Create a JWT access token with RBAC"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Add role and permissions
    to_encode.update({
        "exp": get_int_from_datetime(expire),
        "type": "access",
        "role": role.value,
        "permissions": [p.value for p in ROLE_PERMISSIONS[role]],
        "jti": str(uuid.uuid4())  # JWT ID for revocation
    })
    
    signing_key = get_jwk_from_secret(SECRET_KEY)
    return instance.encode(to_encode, signing_key, alg='HS256')


def create_refresh_token(data: dict, user_id: str) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": get_int_from_datetime(expire),
        "type": "refresh",
        "user_id": user_id,
        "jti": str(uuid.uuid4())
    })
    
    signing_key = get_jwk_from_secret(REFRESH_SECRET_KEY)
    return instance.encode(to_encode, signing_key, alg='HS256')


async def verify_token(
    credentials: HTTPAuthorizationCredentials,
    blacklist: TokenBlacklist,
    token_type: str = "access"
) -> Dict:
    """Verify JWT token and check blacklist"""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="No token provided",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    
    # Check if token is blacklisted
    if await blacklist.is_blacklisted(token):
        raise HTTPException(
            status_code=401,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Verify token
    secret = SECRET_KEY if token_type == "access" else REFRESH_SECRET_KEY
    verifying_key = get_jwk_from_secret(secret)
    
    try:
        payload = instance.decode(token, verifying_key, do_time_check=True, algorithms='HS256')
        
        # Check token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=401,
                detail=f"Invalid token type. Expected {token_type}",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )


def check_permission(required_permission: Permission):
    """Decorator to check if user has required permission"""
    async def permission_checker(token_data: dict = Depends(lambda: None)) -> dict:
        if not token_data:
            raise HTTPException(status_code=403, detail="Not authenticated")
        
        user_permissions = set(token_data.get("permissions", []))
        
        if required_permission.value not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permission: {required_permission.value}"
            )
        
        return token_data
    
    return permission_checker


def check_role(required_roles: List[UserRole]):
    """Decorator to check if user has required role"""
    async def role_checker(token_data: dict = Depends(lambda: None)) -> dict:
        if not token_data:
            raise HTTPException(status_code=403, detail="Not authenticated")
        
        user_role = token_data.get("role")
        
        if user_role not in [role.value for role in required_roles]:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient privileges. Required roles: {[r.value for r in required_roles]}"
            )
        
        return token_data
    
    return role_checker


class EnhancedAuthManager:
    """Enhanced authentication manager with RBAC and audit logging"""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self.blacklist = TokenBlacklist(redis_client)
        self.audit_logger = AuditLogger(redis_client)
    
    async def create_tokens(
        self, 
        email: str, 
        role: UserRole = UserRole.USER,
        request: Optional[Request] = None
    ) -> TokenResponse:
        """Create access and refresh tokens"""
        user_id = str(uuid.uuid4())
        
        # Create tokens
        access_token = create_access_token(
            {"sub": email, "user_id": user_id},
            role=role
        )
        refresh_token = create_refresh_token(
            {"sub": email},
            user_id=user_id
        )
        
        # Log authentication event
        await self.audit_logger.log_event(AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            email=email,
            action="login",
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            success=True,
            details={"role": role.value}
        ))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user_id,
            email=email,
            role=role,
            permissions=[p.value for p in ROLE_PERMISSIONS[role]]
        )
    
    async def refresh_access_token(
        self, 
        refresh_token: str,
        request: Optional[Request] = None
    ) -> TokenResponse:
        """Refresh access token using refresh token"""
        # Verify refresh token
        payload = await verify_token(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=refresh_token),
            self.blacklist,
            token_type="refresh"
        )
        
        email = payload.get("sub")
        user_id = payload.get("user_id")
        role = UserRole(payload.get("role", UserRole.USER.value))
        
        # Create new access token
        access_token = create_access_token(
            {"sub": email, "user_id": user_id},
            role=role
        )
        
        # Log token refresh
        await self.audit_logger.log_event(AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            email=email,
            action="token_refresh",
            ip_address=request.client.host if request else None,
            success=True
        ))
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user_id,
            email=email,
            role=role,
            permissions=[p.value for p in ROLE_PERMISSIONS[role]]
        )
    
    async def revoke_token(
        self,
        token: Optional[str] = None,
        user_id: Optional[str] = None,
        revoke_all: bool = False,
        request: Optional[Request] = None
    ):
        """Revoke token(s)"""
        if revoke_all and user_id:
            await self.blacklist.revoke_user_tokens(user_id)
            
            # Log revocation
            await self.audit_logger.log_event(AuditLogEntry(
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                email="",
                action="revoke_all_tokens",
                ip_address=request.client.host if request else None,
                success=True
            ))
        elif token and user_id:
            await self.blacklist.add_token(
                token, 
                user_id, 
                ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
            
            # Log revocation
            await self.audit_logger.log_event(AuditLogEntry(
                timestamp=datetime.now(timezone.utc),
                user_id=user_id,
                email="",
                action="revoke_token",
                ip_address=request.client.host if request else None,
                success=True
            ))
    
    async def get_user_audit_logs(self, user_id: str, limit: int = 100) -> List[AuditLogEntry]:
        """Get audit logs for user"""
        return await self.audit_logger.get_user_logs(user_id, limit)
    
    async def check_rate_limit(self, user_id: str, max_attempts: int = 5, minutes: int = 15) -> bool:
        """Check if user has exceeded failed login attempts"""
        failed_count = await self.audit_logger.get_failed_login_count(user_id, minutes)
        return failed_count >= max_attempts


def get_enhanced_token_dependency(config: Dict, auth_manager: EnhancedAuthManager):
    """Return enhanced token dependency if JWT is enabled"""
    
    if config.get("security", {}).get("jwt_enabled", False):
        async def jwt_required(
            credentials: HTTPAuthorizationCredentials = Depends(security)
        ) -> Dict:
            """Enforce JWT authentication when enabled"""
            if credentials is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required. Please provide a valid Bearer token.",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            return await verify_token(credentials, auth_manager.blacklist)
        
        return jwt_required
    else:
        return lambda: None

