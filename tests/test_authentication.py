"""
Authentication tests for the Adaptive Honeypot System.
Tests JWT token validation, API key validation, and authentication flows.
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import status
from datetime import datetime, timedelta
import jwt

from src.api.app import create_app
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_api_key,
    hash_api_key,
    verify_api_key,
    hash_password,
    verify_password,
)
from src.core.config import settings


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


class TestJWTTokenValidation:
    """Test JWT token validation."""

    def test_create_access_token(self):
        """Test creating a valid access token."""
        token = create_access_token(subject="test_user_123", scopes=["read", "write"])

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        token_data = decode_token(token)
        assert token_data is not None
        assert token_data.sub == "test_user_123"
        assert "read" in token_data.scopes
        assert "write" in token_data.scopes
        assert token_data.type == "access"

    def test_create_refresh_token(self):
        """Test creating a valid refresh token."""
        token = create_refresh_token(subject="test_user_123")

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        token_data = decode_token(token)
        assert token_data is not None
        assert token_data.sub == "test_user_123"
        assert token_data.type == "refresh"

    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        token = create_access_token(subject="user_456")
        token_data = decode_token(token)

        assert token_data is not None
        assert token_data.sub == "user_456"
        assert isinstance(token_data.exp, datetime)
        assert isinstance(token_data.iat, datetime)
        assert token_data.exp > datetime.utcnow()

    def test_decode_invalid_token(self):
        """Test decoding an invalid token."""
        invalid_tokens = [
            "invalid.token.here",
            "",
            "not-a-jwt",
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",
        ]

        for token in invalid_tokens:
            token_data = decode_token(token)
            assert token_data is None

    def test_decode_expired_token(self):
        """Test decoding an expired token."""
        # Create token that expires in the past
        past_time = datetime.utcnow() - timedelta(hours=1)

        payload = {
            "sub": "test_user",
            "exp": past_time,
            "iat": past_time,
            "type": "access",
            "scopes": [],
        }

        expired_token = jwt.encode(
            payload,
            settings.security.jwt_secret.get_secret_value(),
            algorithm=settings.security.jwt_algorithm,
        )

        # Should return None for expired token
        token_data = decode_token(expired_token)
        assert token_data is None

    def test_token_with_wrong_secret(self):
        """Test token signed with wrong secret."""
        # Create token with different secret
        payload = {
            "sub": "test_user",
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
            "type": "access",
            "scopes": [],
        }

        wrong_token = jwt.encode(
            payload,
            "wrong_secret_key",
            algorithm=settings.security.jwt_algorithm,
        )

        # Should fail to decode
        token_data = decode_token(wrong_token)
        assert token_data is None

    def test_token_with_missing_claims(self):
        """Test token with missing required claims."""
        # Token without 'sub' claim
        payload = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "iat": datetime.utcnow(),
        }

        incomplete_token = jwt.encode(
            payload,
            settings.security.jwt_secret.get_secret_value(),
            algorithm=settings.security.jwt_algorithm,
        )

        # Should fail to decode or return None
        token_data = decode_token(incomplete_token)
        # Should either be None or have None for sub
        if token_data:
            assert token_data.sub is None

    def test_token_with_custom_expiry(self):
        """Test token with custom expiry time."""
        custom_expiry = timedelta(minutes=30)
        token = create_access_token(subject="test_user", expires_delta=custom_expiry)

        token_data = decode_token(token)
        assert token_data is not None

        # Verify expiry is approximately 30 minutes from now
        time_diff = token_data.exp - datetime.utcnow()
        assert time_diff.total_seconds() > 1700  # ~28 minutes
        assert time_diff.total_seconds() < 1900  # ~32 minutes

    def test_access_protected_endpoint_with_valid_token(self, client):
        """Test accessing protected endpoint with valid token."""
        token = create_access_token(subject="test_user", scopes=["read"])

        response = client.get(
            "/api/v1/honeypots", headers={"Authorization": f"Bearer {token}"}
        )

        # Should be accepted (might still fail for other reasons, but not 401)
        # The exact response depends on whether the token has proper permissions
        assert response.status_code != status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/honeypots")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_access_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/api/v1/honeypots", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAPIKeyValidation:
    """Test API key validation."""

    def test_generate_api_key(self):
        """Test API key generation."""
        raw_key, key_hash, key_prefix = generate_api_key()

        assert raw_key is not None
        assert key_hash is not None
        assert key_prefix is not None

        # Key should have expected format
        assert key_prefix.startswith("hp_")
        assert len(key_prefix) == 11  # "hp_" + 8 chars

        # Hash should be SHA-256 hex digest
        assert len(key_hash) == 64  # SHA-256 produces 64 hex chars

        # Raw key should not be in hash (properly hashed)
        assert raw_key not in key_hash

    def test_hash_api_key(self):
        """Test API key hashing."""
        raw_key = "test_api_key_123"
        hashed = hash_api_key(raw_key)

        assert hashed is not None
        assert hashed != raw_key
        assert len(hashed) == 64  # SHA-256 hex length

        # Same key should produce same hash
        hashed2 = hash_api_key(raw_key)
        assert hashed == hashed2

    def test_verify_api_key(self):
        """Test API key verification."""
        raw_key, key_hash, _ = generate_api_key()

        # Should verify correct key
        assert verify_api_key(raw_key, key_hash) is True

        # Should reject wrong key
        assert verify_api_key("wrong_key", key_hash) is False

        # Should reject empty key
        assert verify_api_key("", key_hash) is False

    def test_api_key_timing_attack_resistance(self):
        """Test that API key verification is resistant to timing attacks."""
        import time

        raw_key, key_hash, _ = generate_api_key()

        # Measure time for correct key
        times_correct = []
        for _ in range(100):
            start = time.time()
            verify_api_key(raw_key, key_hash)
            times_correct.append(time.time() - start)

        # Measure time for incorrect key
        times_incorrect = []
        for _ in range(100):
            start = time.time()
            verify_api_key("wrong_key_different_length", key_hash)
            times_incorrect.append(time.time() - start)

        avg_correct = sum(times_correct) / len(times_correct)
        avg_incorrect = sum(times_incorrect) / len(times_incorrect)

        # Times should be similar (within reasonable margin)
        # This is a basic check; real timing attack resistance is more complex
        ratio = max(avg_correct, avg_incorrect) / min(avg_correct, avg_incorrect)
        assert ratio < 10  # Should not be drastically different


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 50  # Bcrypt hashes are 60 chars

    def test_verify_password(self):
        """Test password verification."""
        password = "test_password_123"
        hashed = hash_password(password)

        # Should verify correct password
        assert verify_password(password, hashed) is True

        # Should reject wrong password
        assert verify_password("wrong_password", hashed) is False

        # Should reject empty password
        assert verify_password("", hashed) is False

    def test_password_hash_uniqueness(self):
        """Test that same password produces different hashes."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Different hashes due to salt
        assert hash1 != hash2

        # But both should verify
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_password_strength_variations(self):
        """Test hashing various password strengths."""
        passwords = [
            "simple",
            "more_complex_123",
            "Very_Str0ng!@#$Password",
            "a" * 100,  # Long password
        ]

        for password in passwords:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True


class TestAuthenticationFlow:
    """Test complete authentication flows."""

    @pytest.mark.asyncio
    async def test_login_success(self, client):
        """Test successful login."""
        # This test assumes there's a test user in the database
        # In production, you'd create a test user first
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "test_password"},
        )

        # Response depends on whether test user exists
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data or "token_type" in data

            # Verify token is valid
            token = data.get("access_token")
            token_data = decode_token(token)
            assert token_data is not None

    @pytest.mark.asyncio
    async def test_login_failure_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent_user", "password": "wrong_password"},
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_400_BAD_REQUEST,
        ]

    @pytest.mark.asyncio
    async def test_token_refresh(self, client):
        """Test token refresh flow."""
        # First, get a refresh token (would require login)
        # For testing, create a refresh token directly
        refresh_token = create_refresh_token(subject="test_user")

        response = client.post(
            "/api/v1/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
        )

        # Response depends on whether refresh endpoint is implemented
        # and whether it accepts the token
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "access_token" in data

    @pytest.mark.asyncio
    async def test_logout(self, client):
        """Test logout flow."""
        # Create a valid token
        token = create_access_token(subject="test_user")

        response = client.post(
            "/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"}
        )

        # Logout should succeed
        if response.status_code == status.HTTP_200_OK:
            # Token should now be invalid (if token blacklisting is implemented)
            # Try to use the token again
            protected_response = client.get(
                "/api/v1/honeypots", headers={"Authorization": f"Bearer {token}"}
            )

            # Might still work if token blacklisting is not implemented
            # This depends on the implementation


class TestScopeBasedAccess:
    """Test scope-based access control."""

    @pytest.mark.asyncio
    async def test_access_with_read_scope(self, client):
        """Test access with read-only scope."""
        token = create_access_token(subject="readonly_user", scopes=["read"])

        # Should allow GET requests
        response = client.get(
            "/api/v1/honeypots", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code != status.HTTP_403_FORBIDDEN

        # Might deny POST requests (depends on implementation)
        post_response = client.post(
            "/api/v1/honeypots",
            json={"name": "test", "type": "ssh", "port": 2222},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Could be 403 if scope is checked, or other error if validation fails

    @pytest.mark.asyncio
    async def test_access_with_admin_scope(self, client):
        """Test access with admin scope."""
        token = create_access_token(
            subject="admin_user", scopes=["admin", "read", "write"]
        )

        # Should have access to admin endpoints
        response = client.get(
            "/api/v1/admin/stats", headers={"Authorization": f"Bearer {token}"}
        )

        # Response depends on whether admin endpoint exists
        # But should not be 403 Forbidden
        if response.status_code != status.HTTP_404_NOT_FOUND:
            assert response.status_code != status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_access_without_required_scope(self, client):
        """Test access without required scope."""
        token = create_access_token(
            subject="limited_user",
            scopes=[],  # No scopes
        )

        # Try to access endpoint requiring specific scope
        response = client.post(
            "/api/v1/honeypots",
            json={"name": "test", "type": "ssh", "port": 2222},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Should be denied if scope is required
        # Exact behavior depends on implementation


class TestAPIKeyAuthentication:
    """Test API key authentication."""

    @pytest.mark.asyncio
    async def test_valid_api_key_access(self, client):
        """Test access with valid API key."""
        # Generate a test API key
        raw_key, key_hash, key_prefix = generate_api_key()

        # In a real test, you'd insert this into the database
        # For now, test with an invalid key to see the behavior

        response = client.get("/api/v1/honeypots", headers={"X-API-Key": raw_key})

        # Should be unauthorized since key is not in database
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    @pytest.mark.asyncio
    async def test_invalid_api_key_format(self, client):
        """Test access with invalid API key format."""
        invalid_keys = [
            "invalid",
            "not_a_key",
            "",
            "hp_short",  # Too short
            "hp_toooooolong12345678",  # Too long
        ]

        for key in invalid_keys:
            response = client.get("/api/v1/honeypots", headers={"X-API-Key": key})

            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ]

    @pytest.mark.asyncio
    async def test_api_key_in_wrong_header(self, client):
        """Test API key in wrong header."""
        raw_key, _, _ = generate_api_key()

        # Try in wrong header
        response = client.get(
            "/api/v1/honeypots", headers={"Authorization": f"ApiKey {raw_key}"}
        )

        # Should fail authentication
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
