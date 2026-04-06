"""
FastAPI application factory and configuration.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging
import time
import uuid
import json
from datetime import datetime

from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings
from src.core.db import init_db, close_db
from src.api.v1 import router as v1_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.monitoring.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to all requests."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Track request processing time."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # Log slow requests
        if process_time > 1.0:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}s"
            )

        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""

    async def dispatch(self, request: Request, call_next):
        from src.core.exceptions import HoneypotError, RateLimitError

        try:
            return await call_next(request)
        except RateLimitError as exc:
            logger.warning(f"Rate limit exceeded: {exc}")
            return JSONResponse(
                status_code=429,
                content=exc.to_dict(),
                headers={"Retry-After": str(exc.retry_after)},
            )
        except HoneypotError as exc:
            logger.error(f"Application error: {exc}")
            status_code = 500
            if "AUTHENTICATION" in exc.code:
                status_code = 401
            elif "CONFIGURATION" in exc.code:
                status_code = 500
            return JSONResponse(
                status_code=status_code,
                content=exc.to_dict(),
            )
        except Exception as exc:
            logger.exception(f"Unhandled error: {exc}")

            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(exc) if settings.debug else "An error occurred",
                    "request_id": getattr(request.state, "request_id", None),
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager."""
    import asyncio

    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Start log collector as background task
    collector_task = None
    try:
        from src.collectors.cowrie_collector import get_collector

        collector = get_collector()
        collector_task = asyncio.create_task(collector.start(poll_interval=2))
        logger.info("Log collector started")
    except Exception as e:
        logger.warning(f"Could not start log collector: {e}")

    # Start AI monitoring service
    ai_task = None
    try:
        from src.ai.monitoring import ai_service

        await ai_service.start()
        logger.info("AI monitoring service started")
    except Exception as e:
        logger.warning(f"Could not start AI service: {e}")

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Stop AI service
    try:
        from src.ai.monitoring import ai_service

        await ai_service.stop()
        logger.info("AI monitoring service stopped")
    except Exception as e:
        logger.warning(f"Error stopping AI service: {e}")

    if collector_task:
        collector_task.cancel()
        try:
            await collector_task
        except asyncio.CancelledError:
            pass
        logger.info("Log collector stopped")
    await close_db()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="""
        Production-grade Adaptive Honeypot System API.
        
        ## Features
        - Multi-protocol honeypot support (SSH, HTTP, FTP, Telnet)
        - AI-powered attack analysis and adaptation
        - Real-time monitoring and alerting
        - Threat intelligence integration
        - Session replay and behavioral analysis
        
        ## Authentication
        Use either JWT Bearer token or API Key in the X-API-Key header.
        """,
        docs_url="/api/docs" if settings.environment != "production" else None,
        redoc_url="/api/redoc" if settings.environment != "production" else None,
        openapi_url="/api/openapi.json"
        if settings.environment != "production"
        else None,
        lifespan=lifespan,
    )

    # ==================== Middleware ====================

    # GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Request ID
    app.add_middleware(RequestIDMiddleware)

    # Timing
    app.add_middleware(TimingMiddleware)

    # Error handling
    app.add_middleware(ErrorHandlingMiddleware)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=settings.security.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
    )

    # Trusted hosts (production only)
    if settings.environment == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"],  # Configure appropriately
        )

    # ==================== Routes ====================

    # Health check
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": settings.app_version,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @app.get("/ready", tags=["Health"])
    async def readiness_check():
        """Readiness check endpoint."""
        # TODO: Check database, redis, etc.
        return {
            "status": "ready",
            "checks": {
                "database": "healthy",
                "redis": "healthy",
            },
        }

    # API v1
    app.include_router(v1_router, prefix="/api/v1")

    # WebSocket endpoint - must be on main app
    @app.websocket("/api/v1/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time updates."""
        from src.api.v1.endpoints.websocket import (
            manager as ws_manager,
            handle_client_message as ws_handle_message,
        )

        await ws_manager.connect(websocket)

        try:
            # Send welcome message
            await ws_manager.send_to(
                websocket,
                {
                    "type": "connected",
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Connected to Adaptive Honeypot real-time feed",
                },
            )

            while True:
                # Receive messages from client
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)
                    await ws_handle_message(websocket, message)
                except json.JSONDecodeError:
                    await ws_manager.send_to(
                        websocket,
                        {
                            "type": "error",
                            "message": "Invalid JSON",
                        },
                    )

        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    # Root
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/api/docs",
            "health": "/health",
        }

    return app


# Create app instance
app = create_app()
