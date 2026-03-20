from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database.connection import get_db
from app.application.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/heatmap")
def get_heatmap(db: Session = Depends(get_db)):
    return AnalyticsService.get_heatmap(db)


@router.get("/alerts")
def get_alerts(severity: str = "CRITICAL", db: Session = Depends(get_db)):
    if severity not in ["CRITICAL", "WARNING"]:
        return {"success": False, "error": "Severity must be CRITICAL or WARNING"}

    return AnalyticsService.get_alerts(db, severity)


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return AnalyticsService.get_summary(db)


@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    return AnalyticsService.get_dashboard_stats(db)
