"""
API v1 Router - All endpoints.
"""
from fastapi import APIRouter

from src.api.v1.endpoints import (
    honeypots,
    sessions,
    attacks,
    adaptations,
    alerts,
    threat_intel,
    analytics,
    auth,
    admin,
    settings,
    ai_monitoring,
    cognitive,
)

router = APIRouter()

# Include all endpoint routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(honeypots.router, prefix="/honeypots", tags=["Honeypots"])
router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])
router.include_router(attacks.router, prefix="/attacks", tags=["Attacks"])
router.include_router(adaptations.router, prefix="/adaptations", tags=["Adaptations"])
router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
router.include_router(threat_intel.router, prefix="/threat-intel", tags=["Threat Intelligence"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
router.include_router(settings.router, prefix="/settings", tags=["Settings"])
router.include_router(ai_monitoring.router, prefix="/ai", tags=["AI Monitoring"])
router.include_router(cognitive.router, prefix="/cognitive", tags=["Cognitive Deception"])

# Note: WebSocket endpoint is registered directly on the app in app.py