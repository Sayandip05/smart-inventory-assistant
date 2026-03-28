"""
Database connection — PostgreSQL only (Supabase).

Layer: Infrastructure

DATABASE_URL is REQUIRED in all environments.
Set it to your Supabase PostgreSQL connection string.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

logger = logging.getLogger("smart_inventory.db")

# ── Validate DATABASE_URL ─────────────────────────────────────────────────

if not settings.DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable is REQUIRED. "
        "Set it to your Supabase PostgreSQL connection string. "
        "Example: postgresql://user:pass@db.xxxx.supabase.co:5432/postgres"
    )

DATABASE_URL = settings.DATABASE_URL
logger.info("Database: PostgreSQL (Supabase)")

# ── Engine — connection pool optimized for production ─────────────────────

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # auto-reconnect on stale connections
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Yield a database session — automatically closed after request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
