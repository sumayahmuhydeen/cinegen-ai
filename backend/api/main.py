"""
CineGen AI — FastAPI Backend
============================
Production-Grade AI Film Generation Platform

Phases complete:
- Phase 2: Script Intelligence (Anthropic Claude)
- Phase 3: Video + Audio Generation (Kling 3.0 + ElevenLabs)

API Docs:  http://localhost:8000/docs
Health:    http://localhost:8000/api/v1/health/
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import init_db
from api.routes import projects, characters, locations, shots, health, generation

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()

    # Log service modes on startup
    logger.info("─" * 50)
    logger.info(f"  Script Intelligence : {'LIVE (Anthropic)' if settings.ANTHROPIC_API_KEY else 'MOCK MODE'}")
    logger.info(f"  Video Generation    : {'LIVE (Kling 3.0)' if settings.KLING_API_KEY else 'MOCK MODE'}")
    logger.info(f"  Voice Generation    : {'LIVE (ElevenLabs)' if settings.ELEVENLABS_API_KEY else 'MOCK MODE'}")
    logger.info(f"  Video Fallback      : {'LIVE (Runway)' if settings.RUNWAY_API_KEY else 'MOCK MODE'}")
    logger.info("─" * 50)
    yield
    logger.info("CineGen AI backend shutting down")


app = FastAPI(
    title="CineGen AI",
    version=settings.APP_VERSION,
    description="""
## CineGen AI — AI Film Studio Backend

Transform scripts into complete long-form AI films.

### Production Pipeline
1. **Upload Script** → AI extracts scenes, shots, characters, locations
2. **Approve Characters** → Lock visual identity and voice for entire film
3. **Approve Locations** → Lock visual consistency across all scenes
4. **Generate** → Kling 3.0 generates shots, ElevenLabs generates audio
5. **Assemble** → ffmpeg stitches everything into a final MP4

### Producer's Rules
- Characters must be **approved** before generation starts
- Locations must be **approved** before generation starts
- Shot IDs are **stable** — format: `shot_001_001` (scene_shot)
- Audio runs **parallel** to video — never after
    """,
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

PREFIX = settings.API_PREFIX  # /api/v1

# ── Route Registration ────────────────────────────────────────────────────────
app.include_router(health.router,      prefix=f"{PREFIX}/health",      tags=["Health"])
app.include_router(projects.router,    prefix=f"{PREFIX}/projects",    tags=["Projects"])
app.include_router(characters.router,  prefix=f"{PREFIX}/characters",  tags=["Characters"])
app.include_router(locations.router,   prefix=f"{PREFIX}/locations",   tags=["Locations"])
app.include_router(shots.router,       prefix=f"{PREFIX}/shots",       tags=["Shots"])
app.include_router(generation.router,  prefix=f"{PREFIX}/generation",  tags=["Generation Pipeline"])


@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "CineGen AI",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{PREFIX}/health/",
        "services": {
            "script_intelligence": "live" if settings.ANTHROPIC_API_KEY else "mock",
            "video_generation":    "live" if settings.KLING_API_KEY else "mock",
            "voice_generation":    "live" if settings.ELEVENLABS_API_KEY else "mock",
        },
        "pipeline_steps": [
            "1. POST /api/v1/projects/",
            "2. POST /api/v1/projects/{id}/script",
            "3. POST /api/v1/characters/project/{id}/approve-all",
            "4. POST /api/v1/locations/project/{id}/approve-all",
            "5. POST /api/v1/generation/{id}/shot/shot_001_001  (test one shot)",
            "6. POST /api/v1/generation/{id}/audio",
            "7. POST /api/v1/generation/{id}/start",
            "8. GET  /api/v1/generation/{id}/status",
            "9. POST /api/v1/generation/{id}/assemble",
            "10. GET /api/v1/generation/{id}/export",
        ]
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )
