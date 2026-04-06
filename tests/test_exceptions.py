"""Tests for custom exception classes."""

import pytest
from src.core.exceptions import (
    HoneypotError,
    DeploymentError,
    AIProviderError,
    ConfigurationError,
    AuthenticationError,
    RateLimitError,
)


def test_honeypot_error_base():
    """Test base exception class."""
    exc = HoneypotError("Test error", code="TEST_001")
    assert str(exc) == "Test error"
    assert exc.code == "TEST_001"
    assert exc.details == {}


def test_deployment_error():
    """Test deployment exception."""
    exc = DeploymentError(
        "Failed to deploy honeypot",
        honeypot_id="hp-001",
        details={"container": "cowrie"},
    )
    assert "Failed to deploy honeypot" in str(exc)
    assert exc.honeypot_id == "hp-001"
    assert exc.details["container"] == "cowrie"


def test_ai_provider_error():
    """Test AI provider exception."""
    exc = AIProviderError("OpenAI API rate limit", provider="openai", model="gpt-4")
    assert exc.provider == "openai"
    assert exc.model == "gpt-4"


def test_configuration_error():
    """Test configuration exception."""
    exc = ConfigurationError("Missing required setting", setting_name="JWT_SECRET")
    assert exc.setting_name == "JWT_SECRET"


def test_authentication_error():
    """Test authentication exception."""
    exc = AuthenticationError("Invalid credentials", auth_type="jwt")
    assert exc.auth_type == "jwt"


def test_rate_limit_error():
    """Test rate limit exception."""
    exc = RateLimitError(retry_after=60, limit=100, window_seconds=60)
    assert exc.retry_after == 60
    assert exc.limit == 100
