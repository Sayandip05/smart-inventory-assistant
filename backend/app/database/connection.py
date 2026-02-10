from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create SQLite engine
DATABASE_URL = f"sqlite:///{settings.DATABASE_PATH}"
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite specific
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()