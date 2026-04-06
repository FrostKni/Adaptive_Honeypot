"""Tests for secret validation on startup."""

import pytest
from unittest.mock import patch, MagicMock
from pydantic import SecretStr
from src.core.config import AppSettings, SecuritySettings, validate_production_secrets
from src.core.exceptions import ConfigurationError


def test_validate_production_secrets_passes_in_development():
    """Validation should skip in development mode."""
    settings = AppSettings(
        environment="development",
        admin_password="",
    )
    # Should not raise
    validate_production_secrets(settings)


def test_validate_production_secrets_fails_with_default_jwt():
    """Should fail if JWT secret is default in production."""
    security = SecuritySettings(jwt_secret=SecretStr("change-me-in-production"))
    settings = AppSettings(
        environment="production",
        security=security,
        admin_password="secure_password",
    )

    with pytest.raises(ConfigurationError) as exc:
        validate_production_secrets(settings)
    assert "JWT_SECRET" in str(exc.value)


def test_validate_production_secrets_fails_without_admin_password():
    """Should fail if admin password not set in production."""
    security = SecuritySettings(
        jwt_secret=SecretStr("secure_random_secret_that_is_long_enough")
    )
    settings = AppSettings(
        environment="production",
        security=security,
        admin_password="",
    )

    with pytest.raises(ConfigurationError) as exc:
        validate_production_secrets(settings)
    assert "ADMIN_PASSWORD" in str(exc.value)


def test_validate_production_secrets_passes_with_valid_config():
    """Should pass with valid production config."""
    from src.core.config import AISettings

    security = SecuritySettings(
        jwt_secret=SecretStr("secure_random_secret_key_here_at_least_32_chars")
    )
    ai = AISettings(provider="local")  # Use local provider to avoid API key requirement
    settings = AppSettings(
        environment="production",
        security=security,
        ai=ai,
        admin_password="secure_admin_password",
    )

    # Should not raise
    validate_production_secrets(settings)
