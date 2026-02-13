from typing import Dict, Any

def calculate_reorder_quantity(
    avg_daily_usage: float,
    lead_time_days: int,
    current_stock: int,
    safety_factor: float = 2.0
) -> int:
    """
    Calculate recommended reorder quantity
    
    Formula: (Daily Usage × Lead Time × Safety Factor) - Current Stock
    """
    if avg_daily_usage <= 0:
        return 0
    
    target_stock = avg_daily_usage * lead_time_days * safety_factor
    reorder_qty = max(0, int(target_stock - current_stock))
    
    return reorder_qty

def get_health_color(status: str) -> str:
    """Get color code for health status"""
    colors = {
        "CRITICAL": "#ef4444",  # Red
        "WARNING": "#f59e0b",   # Yellow
        "HEALTHY": "#10b981"    # Green
    }
    return colors.get(status, "#6b7280")  # Gray default

def format_stock_item(item: Any) -> Dict:
    """Format stock health item for API response"""
    return {
        "location_id": item.location_id,
        "location_name": item.location_name,
        "location_type": item.location_type,
        "item_id": item.item_id,
        "item_name": item.item_name,
        "category": item.category,
        "current_stock": item.current_stock,
        "avg_daily_usage": round(item.avg_daily_usage, 2) if item.avg_daily_usage else 0,
        "days_remaining": round(item.days_remaining, 1) if item.days_remaining != 999 else None,
        "health_status": item.health_status,
        "lead_time_days": item.lead_time_days,
        "last_updated": str(item.last_updated),
        "color": get_health_color(item.health_status)
    }