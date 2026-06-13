from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings
from models import Base
import logging

logger = logging.getLogger(__name__)

# Use Supabase connection string if provided, else SQLite for local dev
DATABASE_URL = settings.DATABASE_URL or "sqlite:///./cinegen_dev.db"

# SQLite needs check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=settings.DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency: yields a DB session per request"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables on startup"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Database init failed: {e}")
