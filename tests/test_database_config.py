"""Tests for database configuration."""

import pytest
from unittest.mock import patch
from src.core.config import DatabaseSettings


def test_database_url_uses_environment_variable():
    """Database URL should use environment variable if set."""
    with patch.dict(
        "os.environ",
        {
            "DB_HOST": "postgres-server",
            "DB_PORT": "5432",
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_NAME": "testdb",
        },
    ):
        db_settings = DatabaseSettings()
        # Should construct PostgreSQL URL
        assert "postgres-server" in db_settings.async_url
        assert "testdb" in db_settings.async_url


def test_database_url_fallback_to_sqlite():
    """Database URL should fallback to SQLite for development."""
    # Clear any DB_ environment variables
    import os

    env_copy = {k: v for k, v in os.environ.items() if not k.startswith("DB_")}

    with patch.dict("os.environ", env_copy, clear=True):
        db_settings = DatabaseSettings()
        # Should use SQLite by default
        assert "sqlite" in db_settings.async_url


def test_database_url_postgres_async():
    """PostgreSQL URL should use async driver."""
    with patch.dict(
        "os.environ",
        {
            "DB_HOST": "localhost",
            "DB_USER": "user",
            "DB_PASSWORD": "pass",
            "DB_NAME": "db",
        },
    ):
        db_settings = DatabaseSettings()
        assert (
            "postgresql+asyncpg" in db_settings.async_url
            or "postgres+asyncpg" in db_settings.async_url
        )


def test_database_url_sync():
    """Sync URL should use psycopg2 driver."""
    with patch.dict(
        "os.environ",
        {
            "DB_HOST": "localhost",
            "DB_USER": "user",
            "DB_PASSWORD": "pass",
            "DB_NAME": "db",
        },
    ):
        db_settings = DatabaseSettings()
        assert (
            "postgresql+psycopg2" in db_settings.sync_url
            or "postgres+psycopg2" in db_settings.sync_url
        )
