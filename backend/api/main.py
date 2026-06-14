"""
CineGen AI — FastAPI Backend
============================
Phase 3: Video Generation Pipeline

Endpoints: http://localhost:8000/api/v1/
API Docs:  http://localhost:8000/docs
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import init_db
from api.routes import projects, characters, shots, health, generation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} — Phase 3")
    init_db()
    logger.info("Database initialised")
    # Log which services are in mock vs live mode
    logger.info(f"  Script Intelligence: {'LIVE' if settings.ANTHROPIC_API_KEY else 'MOCK'}")
    logger.info(f"  Video Generation:    {'LIVE' if settings.KLING_API_KEY else 'MOCK (Kling)'}")
    logger.info(f"  Voice Generation:    {'LIVE' if settings.ELEVENLABS_API_KEY else 'MOCK (ElevenLabs)'}")
    logger.info(f"  Music Generation:    {'LIVE' if settings.SUNO_API_KEY else 'MOCK (Suno)'}")
    yield
    logger.info("Shutting down CineGen AI backend")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Long-Form Video Creation Platform — Phase 3: Generation Pipeline",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PREFIX = settings.API_PREFIX

app.include_router(health.router,      prefix=f"{PREFIX}/health",     tags=["Health"])
app.include_router(projects.router,    prefix=f"{PREFIX}/projects",   tags=["Projects"])
app.include_router(characters.router,  prefix=f"{PREFIX}/characters", tags=["Characters"])
app.include_router(shots.router,       prefix=f"{PREFIX}/shots",      tags=["Shots"])
app.include_router(generation.router,  prefix=f"{PREFIX}/generation", tags=["Generation Pipeline"])

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "phase": "Phase 3 — Video Generation Pipeline",
        "docs": "/docs",
        "services": {
            "script_intelligence": "live" if settings.ANTHROPIC_API_KEY else "mock",
            "video_generation": "live" if settings.KLING_API_KEY else "mock",
            "voice_generation": "live" if settings.ELEVENLABS_API_KEY else "mock",
            "music_generation": "live" if settings.SUNO_API_KEY else "mock",
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )
