from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from langchain_core.tools import tool
from app.database.queries import get_latest_stock_health, get_critical_alerts
from app.database.models import Location, Item
from app.utils.calculations import calculate_reorder_quantity

# Global database session (will be set when agent is initialized)
_db_session: Optional[Session] = None

def set_db_session(db: Session):
    """Set the database session for tools to use"""
    global _db_session
    _db_session = db

@tool
def get_critical_items(location: Optional[str] = None, severity: str = "CRITICAL") -> List[Dict[str, Any]]:
    """
    Get list of items with critical or warning stock levels.
    
    Args:
        location: Optional location name to filter (e.g., "Apollo Hospital - Mumbai")
        severity: "CRITICAL" (< 3 days) or "WARNING" (3-7 days)
    
    Returns:
        List of items with low stock, sorted by urgency
    """
    if not _db_session:
        return [{"error": "Database not connected"}]
    
    try:
        alerts = get_critical_alerts(_db_session, severity)
        
        # Filter by location if specified
        if location:
            alerts = [
                item for item in alerts 
                if location.lower() in item.location_name.lower()
            ]
        
        # Format results
        results = []
        for alert in alerts[:20]:  # Limit to top 20
            results.append({
                "location": alert.location_name,
                "item": alert.item_name,
                "category": alert.category,
                "current_stock": alert.current_stock,
                "days_remaining": round(alert.days_remaining, 1) if alert.days_remaining != 999 else "N/A",
                "daily_usage": round(alert.avg_daily_usage, 1) if alert.avg_daily_usage else 0,
                "status": alert.health_status
            })
        
        return results
    except Exception as e:
        return [{"error": str(e)}]

@tool
def get_stock_health(item: Optional[str] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get current stock health status for specific items or locations.
    
    Args:
        item: Optional item name to filter (e.g., "Paracetamol")
        location: Optional location name to filter
    
    Returns:
        Stock health information including status and recommendations
    """
    if not _db_session:
        return [{"error": "Database not connected"}]
    
    try:
        stock_health = get_latest_stock_health(_db_session)
        
        # Filter by item if specified
        if item:
            stock_health = [
                s for s in stock_health 
                if item.lower() in s.item_name.lower()
            ]
        
        # Filter by location if specified
        if location:
            stock_health = [
                s for s in stock_health 
                if location.lower() in s.location_name.lower()
            ]
        
        # Format results
        results = []
        for item_data in stock_health[:30]:  # Limit to 30
            results.append({
                "location": item_data.location_name,
                "item": item_data.item_name,
                "category": item_data.category,
                "current_stock": item_data.current_stock,
                "days_remaining": round(item_data.days_remaining, 1) if item_data.days_remaining != 999 else "Plenty",
                "status": item_data.health_status,
                "daily_usage": round(item_data.avg_daily_usage, 1) if item_data.avg_daily_usage else 0
            })
        
        return results
    except Exception as e:
        return [{"error": str(e)}]

@tool
def calculate_reorder_suggestions(location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Calculate recommended reorder quantities for critical items.
    
    Args:
        location: Optional location to generate orders for
    
    Returns:
        Purchase order suggestions with quantities and reasoning
    """
    if not _db_session:
        return [{"error": "Database not connected"}]
    
    try:
        # Get critical items
        critical = get_critical_alerts(_db_session, "CRITICAL")
        
        # Filter by location if specified
        if location:
            critical = [
                item for item in critical 
                if location.lower() in item.location_name.lower()
            ]
        
        # Calculate reorder quantities
        suggestions = []
        for item in critical[:15]:  # Top 15 most urgent
            reorder_qty = calculate_reorder_quantity(
                avg_daily_usage=item.avg_daily_usage or 0,
                lead_time_days=item.lead_time_days,
                current_stock=item.current_stock
            )
            
            suggestions.append({
                "location": item.location_name,
                "item": item.item_name,
                "current_stock": item.current_stock,
                "recommended_quantity": reorder_qty,
                "urgency": "HIGH" if item.days_remaining < 1 else "MEDIUM",
                "reasoning": f"Daily usage: {round(item.avg_daily_usage, 1)} units, Lead time: {item.lead_time_days} days"
            })
        
        return suggestions
    except Exception as e:
        return [{"error": str(e)}]

@tool
def get_location_summary(location_name: str) -> Dict[str, Any]:
    """
    Get complete inventory summary for a specific location.
    
    Args:
        location_name: Name of the location (e.g., "Mumbai", "Delhi")
    
    Returns:
        Summary statistics for that location
    """
    if not _db_session:
        return {"error": "Database not connected"}
    
    try:
        stock_health = get_latest_stock_health(_db_session)
        
        # Filter by location
        location_data = [
            s for s in stock_health 
            if location_name.lower() in s.location_name.lower()
        ]
        
        if not location_data:
            return {"error": f"No data found for location: {location_name}"}
        
        # Calculate statistics
        critical = sum(1 for s in location_data if s.health_status == "CRITICAL")
        warning = sum(1 for s in location_data if s.health_status == "WARNING")
        healthy = sum(1 for s in location_data if s.health_status == "HEALTHY")
        
        return {
            "location": location_data[0].location_name,
            "total_items": len(location_data),
            "critical_items": critical,
            "warning_items": warning,
            "healthy_items": healthy,
            "status": "NEEDS_ATTENTION" if critical > 0 else "STABLE"
        }
    except Exception as e:
        return {"error": str(e)}

@tool
def get_category_analysis(category: str) -> List[Dict[str, Any]]:
    """
    Analyze stock health for a specific medicine category.
    
    Args:
        category: Category name (e.g., "antibiotic", "painkiller", "vitamin")
    
    Returns:
        Category-wide analysis across all locations
    """
    if not _db_session:
        return [{"error": "Database not connected"}]
    
    try:
        stock_health = get_latest_stock_health(_db_session)
        
        # Filter by category
        category_data = [
            s for s in stock_health 
            if category.lower() in s.category.lower()
        ]
        
        if not category_data:
            return [{"error": f"No data found for category: {category}"}]
        
        # Summarize
        results = []
        for item in category_data[:20]:
            results.append({
                "item": item.item_name,
                "location": item.location_name,
                "status": item.health_status,
                "current_stock": item.current_stock,
                "days_remaining": round(item.days_remaining, 1) if item.days_remaining != 999 else "Plenty"
            })
        
        return results
    except Exception as e:
        return [{"error": str(e)}]