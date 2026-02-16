import os
from dotenv import load_dotenv

from pathlib import Path

# Get the project root directory (current file is in backend/app/config.py)
# Root is backend/../ -> ../
root_dir = Path(__file__).resolve().parent.parent.parent
env_path = root_dir / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", "../database/smart_inventory.db")
    
    # API Keys
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # CORS
    CORS_ORIGINS = os.getenv(
        "CORS_ORIGINS", 
        "http://localhost:3000,http://localhost:5173,http://localhost:5174"
    ).split(",")
    
    # API Settings
    API_V1_PREFIX = "/api"
    PROJECT_NAME = "Smart Inventory Assistant"
    VERSION = "1.0.0"

settings = Settings()