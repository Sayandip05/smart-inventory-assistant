from sqlalchemy import func, case
from sqlalchemy.orm import Session
from app.database.models import InventoryTransaction, Location, Item
from datetime import datetime, timedelta

def get_latest_stock_health(db: Session):
    """Get stock health for most recent date across all locations and items"""
    
    # Get the most recent date
    latest_date = db.query(func.max(InventoryTransaction.date)).scalar()
    
    if not latest_date:
        return []
    
    # Subquery for 7-day average consumption
    subq = (
        db.query(
            InventoryTransaction.location_id,
            InventoryTransaction.item_id,
            func.avg(InventoryTransaction.issued).label('avg_daily_usage')
        )
        .filter(
            InventoryTransaction.date >= (latest_date - timedelta(days=7)),
            InventoryTransaction.date <= latest_date
        )
        .group_by(InventoryTransaction.location_id, InventoryTransaction.item_id)
        .subquery()
    )
    
    # Main query
    results = (
        db.query(
            Location.id.label('location_id'),
            Location.name.label('location_name'),
            Location.type.label('location_type'),
            Item.id.label('item_id'),
            Item.name.label('item_name'),
            Item.category.label('category'),
            Item.lead_time_days,
            Item.min_stock,
            InventoryTransaction.closing_stock.label('current_stock'),
            subq.c.avg_daily_usage,
            case(
                (subq.c.avg_daily_usage > 0, 
                 InventoryTransaction.closing_stock / subq.c.avg_daily_usage),
                else_=999
            ).label('days_remaining'),
            case(
                (
                    case(
                        (subq.c.avg_daily_usage > 0, 
                         InventoryTransaction.closing_stock / subq.c.avg_daily_usage),
                        else_=999
                    ) < 3,
                    'CRITICAL'
                ),
                (
                    case(
                        (subq.c.avg_daily_usage > 0, 
                         InventoryTransaction.closing_stock / subq.c.avg_daily_usage),
                        else_=999
                    ).between(3, 7),
                    'WARNING'
                ),
                else_='HEALTHY'
            ).label('health_status'),
            InventoryTransaction.date.label('last_updated')
        )
        .join(Location, InventoryTransaction.location_id == Location.id)
        .join(Item, InventoryTransaction.item_id == Item.id)
        .outerjoin(
            subq,
            (InventoryTransaction.location_id == subq.c.location_id) &
            (InventoryTransaction.item_id == subq.c.item_id)
        )
        .filter(InventoryTransaction.date == latest_date)
        .all()
    )
    
    return results

def get_critical_alerts(db: Session, severity: str = "CRITICAL"):
    """Get items with critical or warning stock levels"""
    
    stock_health = get_latest_stock_health(db)
    
    # Filter by severity
    alerts = [
        item for item in stock_health 
        if item.health_status == severity
    ]
    
    # Sort by days remaining (most urgent first)
    alerts.sort(key=lambda x: x.days_remaining if x.days_remaining != 999 else 0)
    
    return alerts

def get_heatmap_data(db: Session):
    """Generate heatmap matrix data structure"""
    
    stock_health = get_latest_stock_health(db)
    
    # Extract unique items and locations
    locations = sorted(list(set([item.location_name for item in stock_health])))
    items = sorted(list(set([item.item_name for item in stock_health])))
    
    # Create lookup dictionary
    lookup = {
        (item.location_name, item.item_name): item.health_status
        for item in stock_health
    }
    
    # Build matrix
    matrix = []
    for item_name in items:
        row = []
        for location_name in locations:
            status = lookup.get((location_name, item_name), "UNKNOWN")
            row.append(status)
        matrix.append(row)
    
    return {
        "locations": locations,
        "items": items,
        "matrix": matrix,
        "details": stock_health
    }