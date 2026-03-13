"""
Authentication endpoints.
"""
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    hash_api_key,
    verify_password,
    hash_password,
    get_current_auth,
    AuthContext,
)
from src.core.db import get_db, APIKeyRepository
from src.core.config import settings


router = APIRouter()


# ==================== Schemas ====================

class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str


class APIKeyCreate(BaseModel):
    """API key creation schema."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    scopes: list[str] = []
    is_admin: bool = False
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    """API key response schema."""
    id: int
    key: str  # Only shown once on creation
    name: str
    description: Optional[str]
    is_admin: bool
    scopes: list[str]
    created_at: datetime
    expires_at: Optional[datetime]


class AuthInfo(BaseModel):
    """Current auth info."""
    subject: str
    auth_type: str
    scopes: list[str]
    is_admin: bool


# ==================== Endpoints ====================

@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """Login and get JWT tokens."""
    # TODO: Implement proper user authentication
    
    # For now, check against admin credentials
    if data.username == "admin" and data.password == "admin":
        access_token = create_access_token(
            subject=data.username,
            scopes=["admin", "honeypots:read", "honeypots:write", "attacks:read", "sessions:read"],
        )
        refresh_token = create_refresh_token(data.username)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.security.jwt_expire_minutes * 60,
        )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest):
    """Refresh access token."""
    token_data = decode_token(data.refresh_token)
    
    if not token_data or token_data.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Create new tokens
    access_token = create_access_token(
        subject=token_data.sub,
        scopes=token_data.scopes,
    )
    refresh_token = create_refresh_token(token_data.sub)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.security.jwt_expire_minutes * 60,
    )


@router.get("/me", response_model=AuthInfo)
async def get_current_user(auth: AuthContext = Depends(get_current_auth)):
    """Get current authentication info."""
    return AuthInfo(
        subject=auth.subject,
        auth_type=auth.auth_type,
        scopes=auth.scopes,
        is_admin=auth.is_admin,
    )


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    data: APIKeyCreate,
    auth: AuthContext = Depends(get_current_auth),
):
    """Create a new API key."""
    auth.require_scope("admin")
    
    raw_key, key_hash, key_prefix = generate_api_key()
    
    expires_at = None
    if data.expires_days:
        expires_at = datetime.utcnow() + timedelta(days=data.expires_days)
    
    async for session in get_db():
        repo = APIKeyRepository(session)
        
        api_key = await repo.create(
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=data.name,
            description=data.description,
            is_admin=data.is_admin,
            scopes=data.scopes,
            expires_at=expires_at,
        )
        
        return APIKeyResponse(
            id=api_key.id,
            key=raw_key,  # Only time this is shown
            name=api_key.name,
            description=api_key.description,
            is_admin=api_key.is_admin,
            scopes=api_key.scopes,
            created_at=api_key.created_at,
            expires_at=api_key.expires_at,
        )


@router.get("/api-keys")
async def list_api_keys(auth: AuthContext = Depends(get_current_auth)):
    """List all API keys."""
    auth.require_scope("admin")
    
    async for session in get_db():
        repo = APIKeyRepository(session)
        keys = await repo.get_all()
        
        return [{
            "id": k.id,
            "prefix": k.key_prefix,
            "name": k.name,
            "is_active": k.is_active,
            "is_admin": k.is_admin,
            "scopes": k.scopes,
            "last_used": k.last_used,
            "created_at": k.created_at,
        } for k in keys]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    auth: AuthContext = Depends(get_current_auth),
):
    """Revoke an API key."""
    auth.require_scope("admin")
    
    async for session in get_db():
        repo = APIKeyRepository(session)
        deleted = await repo.delete(key_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="API key not found")
        
        return {"revoked": True}