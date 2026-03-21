from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database.connection import get_db
from app.application.analytics_service import AnalyticsService
from app.core.exceptions import ValidationError
from app.core.dependencies import get_current_user
from app.infrastructure.database.models import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/heatmap")
def get_heatmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AnalyticsService.get_heatmap(db)


@router.get("/alerts")
def get_alerts(
    severity: str = "CRITICAL",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if severity not in ["CRITICAL", "WARNING"]:
        raise ValidationError("Severity must be CRITICAL or WARNING")

    return AnalyticsService.get_alerts(db, severity)


@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AnalyticsService.get_summary(db)


@router.get("/dashboard/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AnalyticsService.get_dashboard_stats(db)
