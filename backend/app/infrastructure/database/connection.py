"""
Database connection — strictly PostgreSQL (Supabase) via DATABASE_URL.

No local SQLite fallback. Production and dev both use PostgreSQL.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

logger = logging.getLogger("smart_inventory.db")

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is required. Please set it to a valid PostgreSQL connection string.")

DATABASE_URL = settings.DATABASE_URL

# Pooling configuration optimized for Supabase/PostgreSQL
engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # auto-reconnect on stale connections
)

logger.info("Database: PostgreSQL connected")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
