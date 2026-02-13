from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import engine, Base
from app.database.models import Location, Item, InventoryTransaction

# Import routers
from app.api.routes import analytics, chat  # ← Added chat

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-powered inventory management for healthcare supply chains"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analytics.router, prefix=settings.API_V1_PREFIX)
app.include_router(chat.router, prefix=settings.API_V1_PREFIX)  # ← Added

@app.get("/")
def root():
    return {
        "message": "Smart Inventory Assistant API",
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "endpoints": [
            "/api/analytics/heatmap",
            "/api/analytics/alerts",
            "/api/analytics/summary",
            "/api/chat/query",           # ← Added
            "/api/chat/suggestions"      # ← Added
        ]
    }