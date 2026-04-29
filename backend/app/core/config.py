import os
import logging
from dotenv import load_dotenv

from pathlib import Path

# Try to find .env in multiple locations
# 1. Current directory (for running from project root)
# 2. Parent of backend folder (project root)
# 3. Backend folder itself
possible_env_paths = [
    Path(".").resolve() / ".env",  # Current directory
    Path(__file__).resolve().parent.parent.parent.parent / ".env",  # Project root (backend/../)
    Path(__file__).resolve().parent.parent.parent / ".env",  # Backend folder
]

env_loaded = False
for env_path in possible_env_paths:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        env_loaded = True
        break

if not env_loaded:
    # Try loading without explicit path (uses cwd)
    load_dotenv()

logger = logging.getLogger("smart_inventory")


class Settings:
    # ── Application ───────────────────────────────────────────────────
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    PROJECT_NAME = "Smart Inventory Assistant"
    VERSION = "2.0.0"
    API_V1_PREFIX = "/api"
    
    # ── Database ──────────────────────────────────────────────────────
    DATABASE_URL = os.getenv("DATABASE_URL", "")  # PostgreSQL (Supabase) — REQUIRED
    
    # ── Frontend ──────────────────────────────────────────────────────
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173,http://localhost:5174",
    ).split(",")
    
    # ── AI / LLM ──────────────────────────────────────────────────────
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))
    
    # ── LangSmith (Observability) ─────────────────────────────────────
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "InvIQ")
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false")
    LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    
    # ── ChromaDB (Vector Store) ───────────────────────────────────────
    CHROMADB_ENABLED = os.getenv("CHROMADB_ENABLED", "true").lower() == "true"
    CHROMADB_PATH = os.getenv("CHROMADB_PATH", "data/chromadb")
    CHROMADB_COLLECTION = os.getenv("CHROMADB_COLLECTION", "chat_memory")

    # ── Auth & Security ───────────────────────────────────────────────
    # REQUIRED: Generate a secure key with: openssl rand -hex 32
    SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ── Login Lockout ─────────────────────────────────────────────────
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))

    # ── Super Admin (platform owner) ────────────────────────────────
    SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL", "admin@example.com")

    # ── Admin Seed (first startup only) ───────────────────────────────
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@inventory.local")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
    ADMIN_FULL_NAME = os.getenv("ADMIN_FULL_NAME", "System Administrator")

    # ── Upstash Redis (Caching) ───────────────────────────────────────
    UPSTASH_REDIS_REST_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
    UPSTASH_REDIS_REST_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")
    REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"

    # ── Rate Limiting ─────────────────────────────────────────────────
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "60/minute")
    RATE_LIMIT_AUTH = os.getenv("RATE_LIMIT_AUTH", "5/minute")
    
    # ── SMTP (Email) ──────────────────────────────────────────────────
    SMTP_ENABLED = os.getenv("SMTP_ENABLED", "false").lower() == "true"
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "InvIQ Smart Inventory")
    
    # ── External APIs ─────────────────────────────────────────────────
    GOOGLE_OAUTH_VERIFY_URL = os.getenv(
        "GOOGLE_OAUTH_VERIFY_URL",
        "https://www.googleapis.com/oauth2/v3/userinfo"
    )


settings = Settings()


# ── Production safety checks ──────────────────────────────────────────────
def _validate_production_config():
    """Fail loudly if critical secrets are using insecure defaults in production."""
    if settings.ENVIRONMENT == "production":
        if settings.SECRET_KEY == "your-super-secret-key-change-in-production":
            raise ValueError(
                "FATAL: SECRET_KEY is still the insecure default! "
                "Generate a secure key with: openssl rand -hex 32"
            )
        if settings.ADMIN_PASSWORD == "":
            logger.warning(
                "⚠️  ADMIN_PASSWORD is empty. "
                "Set ADMIN_PASSWORD env var to a strong password for production."
            )
    elif settings.SECRET_KEY == "your-super-secret-key-change-in-production":
        logger.warning(
            "SECRET_KEY is using the insecure default — acceptable for local dev only. "
            "Generate a secure key for production: openssl rand -hex 32"
        )


_validate_production_config()


def configure_langsmith():
    """Configure LangSmith observability using LANGSMITH_* environment variables."""
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
        logger.info(
            "✅ LangSmith tracing enabled → project: %s", settings.LANGSMITH_PROJECT
        )
    else:
        os.environ["LANGSMITH_TRACING"] = "false"
        logger.info("LangSmith tracing disabled — LANGSMITH_API_KEY not set")


configure_langsmith()
