"""
Security utilities: JWT, API Key, Password hashing, Rate limiting.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from functools import wraps
import logging

from fastapi import HTTPException, Security, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from src.core.config import settings
from src.core.cache import RedisRateLimiter, get_redis_client

logger = logging.getLogger(__name__)


# ==================== Password Hashing ====================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT Token ====================


class TokenData(BaseModel):
    """JWT token payload."""

    sub: str  # Subject (user ID or API key ID)
    exp: datetime
    iat: datetime
    type: str = "access"  # access, refresh
    scopes: List[str] = []


def create_access_token(
    subject: str,
    scopes: List[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.security.jwt_expire_minutes
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "scopes": scopes or [],
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.jwt_secret.get_secret_value(),
        algorithm=settings.security.jwt_algorithm,
    )
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """Create a JWT refresh token."""
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "scopes": [],
    }
    return jwt.encode(
        to_encode,
        settings.security.jwt_secret.get_secret_value(),
        algorithm=settings.security.jwt_algorithm,
    )


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.security.jwt_secret.get_secret_value(),
            algorithms=[settings.security.jwt_algorithm],
        )
        return TokenData(
            sub=payload.get("sub"),
            exp=datetime.fromtimestamp(payload.get("exp")),
            iat=datetime.fromtimestamp(payload.get("iat")),
            type=payload.get("type", "access"),
            scopes=payload.get("scopes", []),
        )
    except JWTError:
        return None


# ==================== API Key ====================


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    Returns: (raw_key, key_hash, key_prefix)
    """
    # Generate random key
    raw_key = secrets.token_urlsafe(settings.security.api_key_length)

    # Create hash for storage
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    # Create prefix for identification
    key_prefix = f"hp_{raw_key[:8]}"

    return raw_key, key_hash, key_prefix


def hash_api_key(key: str) -> str:
    """Hash an API key."""
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    """Verify an API key against its hash."""
    return secrets.compare_digest(hash_api_key(key), key_hash)


# ==================== FastAPI Dependencies ====================

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(
    name=settings.security.api_key_header,
    auto_error=False,
)


class AuthContext:
    """Authentication context for request."""

    def __init__(
        self,
        subject: str,
        auth_type: str,  # "jwt" or "api_key"
        scopes: List[str] = None,
        is_admin: bool = False,
    ):
        self.subject = subject
        self.auth_type = auth_type
        self.scopes = scopes or []
        self.is_admin = is_admin

    def has_scope(self, scope: str) -> bool:
        """Check if user has a specific scope."""
        if self.is_admin:
            return True
        return scope in self.scopes

    def require_scope(self, scope: str):
        """Raise exception if scope not present."""
        if not self.has_scope(scope):
            raise HTTPException(
                status_code=403,
                detail=f"Missing required scope: {scope}",
            )


async def get_current_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header),
) -> AuthContext:
    """
    Get current authentication context.
    Supports both JWT and API key authentication.
    """
    from src.core.db import get_db, APIKeyRepository

    # Try JWT first
    if credentials:
        token_data = decode_token(credentials.credentials)
        if token_data:
            return AuthContext(
                subject=token_data.sub,
                auth_type="jwt",
                scopes=token_data.scopes,
            )

    # Try API key
    if api_key:
        # Extract prefix
        parts = api_key.split("_")
        if len(parts) >= 2:
            prefix = f"{parts[0]}_{parts[1]}"

            # Look up in database
            async for session in get_db():
                repo = APIKeyRepository(session)
                key_record = await repo.get_by_prefix(prefix)

                if key_record and key_record.is_active:
                    if verify_api_key(api_key, key_record.key_hash):
                        # Record usage
                        await repo.record_usage(key_record.id)

                        return AuthContext(
                            subject=str(key_record.id),
                            auth_type="api_key",
                            scopes=key_record.scopes,
                            is_admin=key_record.is_admin,
                        )

    raise HTTPException(
        status_code=401,
        detail="Invalid or missing authentication credentials",
    )


async def get_optional_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_header),
) -> Optional[AuthContext]:
    """Get optional authentication context (may be None)."""
    try:
        return await get_current_auth(request, credentials, api_key)
    except HTTPException:
        return None


def require_scopes(*required_scopes: str):
    """
    Decorator to require specific scopes.
    Usage: @require_scopes("honeypots:read", "honeypots:write")
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, auth: AuthContext = None, **kwargs):
            if auth is None:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication required",
                )

            for scope in required_scopes:
                auth.require_scope(scope)

            return await func(*args, auth=auth, **kwargs)

        return wrapper

    return decorator


# ==================== Rate Limiting ====================


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception."""

    def __init__(self, retry_after: int):
        super().__init__(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


# Global rate limiter instance
_rate_limiter: Optional[RedisRateLimiter] = None


async def init_rate_limiter() -> RedisRateLimiter:
    """
    Initialize rate limiter with Redis connection.
    Falls back to in-memory if Redis unavailable.
    """
    global _rate_limiter

    if _rate_limiter is None:
        redis_client = await get_redis_client()
        _rate_limiter = RedisRateLimiter(
            redis_client=redis_client,
            requests=settings.security.rate_limit_requests,
            window_seconds=settings.security.rate_limit_window,
            fallback_to_memory=True,
        )

        if redis_client:
            logger.info("Initialized Redis-backed rate limiter")
        else:
            logger.info("Initialized in-memory rate limiter (Redis unavailable)")

    return _rate_limiter


def get_rate_limiter() -> RedisRateLimiter:
    """
    Get the rate limiter instance.
    Must call init_rate_limiter() first during startup.
    """
    if _rate_limiter is None:
        raise RuntimeError(
            "Rate limiter not initialized. Call init_rate_limiter() first."
        )
    return _rate_limiter


async def check_rate_limit(
    request: Request, auth: AuthContext = Depends(get_current_auth)
):
    """Dependency to check rate limit."""
    limiter = get_rate_limiter()
    key = f"{auth.subject}"

    allowed, retry_after = await limiter.is_allowed(key)

    if not allowed:
        raise RateLimitExceeded(retry_after)

    return True
