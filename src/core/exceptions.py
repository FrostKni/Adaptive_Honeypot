"""
Custom exception hierarchy for the Adaptive Honeypot system.

Provides structured error handling with error codes, details, and
specific exception types for different error categories.
"""

from typing import Optional, Dict, Any


class HoneypotError(Exception):
    """
    Base exception for all honeypot-related errors.

    Attributes:
        message: Human-readable error message
        code: Error code for programmatic handling
        details: Additional context about the error
    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code or "UNKNOWN_ERROR"
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }


class DeploymentError(HoneypotError):
    """
    Exception raised when honeypot deployment operations fail.

    Used for container creation, startup, and configuration errors.
    """

    def __init__(
        self,
        message: str,
        honeypot_id: Optional[str] = None,
        container_id: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if honeypot_id:
            details["honeypot_id"] = honeypot_id
        if container_id:
            details["container_id"] = container_id

        super().__init__(
            message,
            code=kwargs.pop("code", "DEPLOYMENT_ERROR"),
            details=details,
        )
        self.honeypot_id = honeypot_id
        self.container_id = container_id


class AIProviderError(HoneypotError):
    """
    Exception raised when AI provider operations fail.

    Used for API errors, rate limits, and response parsing failures.
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if provider:
            details["provider"] = provider
        if model:
            details["model"] = model

        super().__init__(
            message,
            code=kwargs.pop("code", "AI_PROVIDER_ERROR"),
            details=details,
        )
        self.provider = provider
        self.model = model


class ConfigurationError(HoneypotError):
    """
    Exception raised when configuration is invalid or missing.

    Used for startup validation and configuration errors.
    """

    def __init__(
        self,
        message: str,
        setting_name: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if setting_name:
            details["setting_name"] = setting_name

        super().__init__(
            message,
            code=kwargs.pop("code", "CONFIGURATION_ERROR"),
            details=details,
        )
        self.setting_name = setting_name


class AuthenticationError(HoneypotError):
    """
    Exception raised when authentication fails.

    Used for invalid credentials, expired tokens, and missing auth.
    """

    def __init__(
        self,
        message: str = "Authentication failed",
        auth_type: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if auth_type:
            details["auth_type"] = auth_type

        super().__init__(
            message,
            code=kwargs.pop("code", "AUTHENTICATION_ERROR"),
            details=details,
        )
        self.auth_type = auth_type


class RateLimitError(HoneypotError):
    """
    Exception raised when rate limit is exceeded.

    Includes retry_after information for clients.
    """

    def __init__(
        self,
        retry_after: int,
        limit: int,
        window_seconds: int,
        message: str = "Rate limit exceeded",
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        details["retry_after"] = retry_after
        details["limit"] = limit
        details["window_seconds"] = window_seconds

        super().__init__(
            message,
            code=kwargs.pop("code", "RATE_LIMIT_EXCEEDED"),
            details=details,
        )
        self.retry_after = retry_after
        self.limit = limit
        self.window_seconds = window_seconds
