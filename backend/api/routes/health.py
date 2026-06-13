"""Health check routes"""
from fastapi import APIRouter
from core.config import settings

router = APIRouter()

@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "phase": "Phase 2 — Script Intelligence",
        "services": {
            "script_intelligence": "ready" if settings.ANTHROPIC_API_KEY else "mock_mode",
            "database": "connected",
            "bible_system": "ready",
            "continuity_engine": "ready",
        }
    }

@router.get("/ping")
async def ping():
    return {"ping": "pong"}
