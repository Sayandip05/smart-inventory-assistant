"""
Database connection — PostgreSQL (Supabase) or SQLite.

Layer: Infrastructure

DATABASE_URL is REQUIRED in all environments.
For production: Set it to your Supabase PostgreSQL connection string.
For development: SQLite is supported (e.g., sqlite:///./database.db)
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
        "Set it to your database connection string. "
        "Examples: postgresql://user:pass@host/db or sqlite:///./database.db"
    )

DATABASE_URL = settings.DATABASE_URL
is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    logger.info("Database: SQLite (development mode)")
else:
    logger.info("Database: PostgreSQL (production mode)")

# ── Engine — connection pool optimized for production ─────────────────────

if is_sqlite:
    # SQLite-specific settings (no connection pooling needed)
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL production settings
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
