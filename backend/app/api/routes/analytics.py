from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.get("/heatmap")
def get_heatmap(db: Session = Depends(get_db)):
    """
    Get stock health heatmap data
    
    Returns matrix of stock health status for all items across all locations
    """
    return AnalyticsService.get_heatmap(db)

@router.get("/alerts")
def get_alerts(
    severity: str = "CRITICAL",
    db: Session = Depends(get_db)
):
    """
    Get stock alerts
    
    Parameters:
    - severity: CRITICAL or WARNING (default: CRITICAL)
    
    Returns list of items requiring attention
    """
    if severity not in ["CRITICAL", "WARNING"]:
        return {
            "success": False,
            "error": "Severity must be CRITICAL or WARNING"
        }
    
    return AnalyticsService.get_alerts(db, severity)

@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """
    Get overall inventory statistics
    
    Returns summary of stock health across all locations and categories
    """
    return AnalyticsService.get_summary(db)

@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get aggregated data for admin dashboard charts
    """
    return AnalyticsService.get_dashboard_stats(db)