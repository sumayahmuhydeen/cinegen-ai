"""
CineGen AI — FastAPI Backend
============================
Phase 2: Script Intelligence Layer

Endpoints live at: http://localhost:8000/api/v1/
API Docs at:       http://localhost:8000/docs
Health check at:   http://localhost:8000/api/v1/health/
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from core.database import init_db
from api.routes import projects, characters, shots, health

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

# ── Startup / Shutdown ───────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Database initialised")
    yield
    logger.info("Shutting down")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Long-Form Video Creation Platform — Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────
PREFIX = settings.API_PREFIX  # /api/v1

app.include_router(health.router,     prefix=f"{PREFIX}/health",     tags=["Health"])
app.include_router(projects.router,   prefix=f"{PREFIX}/projects",   tags=["Projects"])
app.include_router(characters.router, prefix=f"{PREFIX}/characters", tags=["Characters"])
app.include_router(shots.router,      prefix=f"{PREFIX}/shots",      tags=["Shots"])

# ── Root ─────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "phase": "Phase 2 — Script Intelligence",
        "docs": "/docs",
        "health": f"{PREFIX}/health",
    }

# ── Global error handler ─────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )
