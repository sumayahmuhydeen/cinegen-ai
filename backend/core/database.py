"""
Database Configuration
=======================
Environment-aware database setup.

LOCAL DEV (Windows):  SQLite — no PostgreSQL driver required
PRODUCTION (Railway): PostgreSQL via DATABASE_URL in .env

The psycopg2 ModuleNotFoundError on Windows Python 3.14 is
prevented by detecting psycopg2 availability before connecting.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from models import Base
import logging

logger = logging.getLogger(__name__)


def _resolve_database_url() -> str:
    """
    Smart URL resolution:
    - No DATABASE_URL set       → SQLite (local dev)
    - DATABASE_URL = sqlite://  → SQLite (explicit local)
    - DATABASE_URL = postgres:// → PostgreSQL IF psycopg2 installed
                                 → SQLite fallback if not (Windows dev)
    """
    raw_url = settings.DATABASE_URL or ""

    if not raw_url:
        logger.info("No DATABASE_URL — using SQLite for local development")
        return "sqlite:///./cinegen_dev.db"

    if raw_url.startswith("sqlite"):
        return raw_url

    if "postgresql" in raw_url or "postgres" in raw_url:
        try:
            import psycopg2  # noqa: F401
            logger.info("psycopg2 available — connecting to PostgreSQL")
            return raw_url
        except ImportError:
            logger.warning(
                "DATABASE_URL is PostgreSQL but psycopg2 not installed. "
                "Falling back to SQLite. Install psycopg2-binary for PostgreSQL support."
            )
            return "sqlite:///./cinegen_dev.db"

    return raw_url


DATABASE_URL = _resolve_database_url()

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session per request, closes after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables on startup. Called from app lifespan."""
    try:
        Base.metadata.create_all(bind=engine)
        db_type = "SQLite (local)" if DATABASE_URL.startswith("sqlite") else "PostgreSQL (production)"
        logger.info(f"Database initialised — {db_type}")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
        raise
