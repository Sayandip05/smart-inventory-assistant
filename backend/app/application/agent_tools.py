from datetime import timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from langchain_core.tools import tool
from app.infrastructure.database.queries import (
    get_latest_stock_health,
    get_critical_alerts,
)
from app.infrastructure.database.models import Location, Item, InventoryTransaction
from app.domain.calculations import calculate_reorder_quantity

_db_session: Optional[Session] = None


def set_db_session(db: Session):
    """Set the database session for tools to use"""
    global _db_session
    _db_session = db


def _no_data_message(message: str) -> List[Dict[str, Any]]:
    return [{"info": message}]


@tool
def get_inventory_overview() -> Dict[str, Any]:
    if not _db_session:
        return {"error": "Database not connected"}

    try:
        locations_count = _db_session.query(Location).count()
        items_count = _db_session.query(Item).count()
        transactions_count = _db_session.query(InventoryTransaction).count()
        min_date, max_date = _db_session.query(
            func.min(InventoryTransaction.date),
            func.max(InventoryTransaction.date),
        ).one()

        return {
            "locations": locations_count,
            "items": items_count,
            "transactions": transactions_count,
            "transaction_start_date": str(min_date) if min_date else None,
            "transaction_end_date": str(max_date) if max_date else None,
            "has_data": transactions_count > 0,
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def get_critical_items(
    location: str = "", severity: str = "CRITICAL"
) -> List[Dict[str, Any]]:
    if not _db_session:
        return [{"error": "Database not connected"}]

    try:
        if severity not in {"CRITICAL", "WARNING"}:
            return [{"error": "Severity must be CRITICAL or WARNING"}]

        alerts = get_critical_alerts(_db_session, severity)

        if location and location.strip():
            alerts = [
                item
                for item in alerts
                if location.lower() in item.location_name.lower()
            ]

        if not alerts:
            return _no_data_message("No matching low-stock alerts found.")

        results = []
        for alert in alerts[:20]:
            results.append(
                {
                    "location": alert.location_name,
                    "item": alert.item_name,
                    "category": alert.category,
                    "current_stock": alert.current_stock,
                    "days_remaining": round(alert.days_remaining, 1)
                    if alert.days_remaining != 999
                    else "N/A",
                    "daily_usage": round(alert.avg_daily_usage, 1)
                    if alert.avg_daily_usage
                    else 0,
                    "status": alert.health_status,
                }
            )

        return results
    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_stock_health(item: str = "", location: str = "") -> List[Dict[str, Any]]:
    if not _db_session:
        return [{"error": "Database not connected"}]

    try:
        stock_health = get_latest_stock_health(_db_session)

        if item and item.strip():
            stock_health = [
                s for s in stock_health if item.lower() in s.item_name.lower()
            ]

        if location and location.strip():
            stock_health = [
                s for s in stock_health if location.lower() in s.location_name.lower()
            ]

        if not stock_health:
            return _no_data_message("No stock health data found for the given filters.")

        results = []
        for item_data in stock_health[:30]:
            results.append(
                {
                    "location": item_data.location_name,
                    "item": item_data.item_name,
                    "category": item_data.category,
                    "current_stock": item_data.current_stock,
                    "days_remaining": round(item_data.days_remaining, 1)
                    if item_data.days_remaining != 999
                    else "Plenty",
                    "status": item_data.health_status,
                    "daily_usage": round(item_data.avg_daily_usage, 1)
                    if item_data.avg_daily_usage
                    else 0,
                }
            )

        return results
    except Exception as e:
        return [{"error": str(e)}]


@tool
def calculate_reorder_suggestions(location: str = "") -> List[Dict[str, Any]]:
    if not _db_session:
        return [{"error": "Database not connected"}]

    try:
        critical = get_critical_alerts(_db_session, "CRITICAL")

        if location and location.strip():
            critical = [
                item
                for item in critical
                if location.lower() in item.location_name.lower()
            ]

        if not critical:
            return _no_data_message(
                "No critical items currently require reorder suggestions."
            )

        suggestions = []
        for item in critical[:15]:
            reorder_qty = calculate_reorder_quantity(
                avg_daily_usage=item.avg_daily_usage or 0,
                lead_time_days=item.lead_time_days,
                current_stock=item.current_stock,
            )

            suggestions.append(
                {
                    "location": item.location_name,
                    "item": item.item_name,
                    "current_stock": item.current_stock,
                    "recommended_quantity": reorder_qty,
                    "urgency": "HIGH" if item.days_remaining < 1 else "MEDIUM",
                    "reasoning": f"Daily usage: {round(item.avg_daily_usage, 1)} units, Lead time: {item.lead_time_days} days",
                }
            )

        return suggestions
    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_location_summary(location_name: str) -> Dict[str, Any]:
    if not _db_session:
        return {"error": "Database not connected"}

    try:
        stock_health = get_latest_stock_health(_db_session)

        location_data = [
            s for s in stock_health if location_name.lower() in s.location_name.lower()
        ]

        if not location_data:
            return {"error": f"No data found for location: {location_name}"}

        critical = sum(1 for s in location_data if s.health_status == "CRITICAL")
        warning = sum(1 for s in location_data if s.health_status == "WARNING")
        healthy = sum(1 for s in location_data if s.health_status == "HEALTHY")

        return {
            "location": location_data[0].location_name,
            "total_items": len(location_data),
            "critical_items": critical,
            "warning_items": warning,
            "healthy_items": healthy,
            "status": "NEEDS_ATTENTION" if critical > 0 else "STABLE",
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def get_category_analysis(category: str) -> List[Dict[str, Any]]:
    if not _db_session:
        return [{"error": "Database not connected"}]

    try:
        stock_health = get_latest_stock_health(_db_session)

        category_data = [
            s for s in stock_health if category.lower() in s.category.lower()
        ]

        if not category_data:
            return [{"error": f"No data found for category: {category}"}]

        results = []
        for item in category_data[:20]:
            results.append(
                {
                    "item": item.item_name,
                    "location": item.location_name,
                    "status": item.health_status,
                    "current_stock": item.current_stock,
                    "days_remaining": round(item.days_remaining, 1)
                    if item.days_remaining != 999
                    else "Plenty",
                }
            )

        return results
    except Exception as e:
        return [{"error": str(e)}]


@tool
def get_consumption_trends(
    item: str = "", location: str = "", days: int = 14
) -> Dict[str, Any]:
    if not _db_session:
        return {"error": "Database not connected"}

    days = max(1, min(days, 90))

    try:
        latest_date = _db_session.query(func.max(InventoryTransaction.date)).scalar()
        if not latest_date:
            return {"info": "No transaction data available yet."}

        start_date = latest_date - timedelta(days=days - 1)

        query = (
            _db_session.query(
                InventoryTransaction.date.label("date"),
                func.sum(InventoryTransaction.issued).label("issued"),
            )
            .join(Location, InventoryTransaction.location_id == Location.id)
            .join(Item, InventoryTransaction.item_id == Item.id)
            .filter(InventoryTransaction.date >= start_date)
        )

        if item and item.strip():
            query = query.filter(Item.name.ilike(f"%{item.strip()}%"))

        if location and location.strip():
            query = query.filter(Location.name.ilike(f"%{location.strip()}%"))

        rows = (
            query.group_by(InventoryTransaction.date)
            .order_by(InventoryTransaction.date.asc())
            .all()
        )

        if not rows:
            return {"info": "No trend data found for the selected filters."}

        series = [{"date": str(r.date), "issued": int(r.issued or 0)} for r in rows]
        values = [point["issued"] for point in series]

        return {
            "start_date": str(start_date),
            "end_date": str(latest_date),
            "days_requested": days,
            "points": series,
            "total_issued": int(sum(values)),
            "avg_daily_issued": round(sum(values) / len(values), 2),
            "peak_daily_issued": int(max(values)),
        }
    except Exception as e:
        return {"error": str(e)}
