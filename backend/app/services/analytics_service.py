from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database.queries import (
    get_latest_stock_health,
    get_critical_alerts,
    get_heatmap_data
)
from app.utils.calculations import format_stock_item, calculate_reorder_quantity

class AnalyticsService:
    
    @staticmethod
    def get_heatmap(db: Session) -> Dict[str, Any]:
        """Generate heatmap data for dashboard"""
        try:
            data = get_heatmap_data(db)
            
            # Format details
            formatted_details = [
                format_stock_item(item) for item in data["details"]
            ]
            
            return {
                "success": True,
                "data": {
                    "locations": data["locations"],
                    "items": data["items"],
                    "matrix": data["matrix"],
                    "details": formatted_details
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_alerts(db: Session, severity: str = "CRITICAL") -> Dict[str, Any]:
        """Get critical or warning alerts"""
        try:
            alerts = get_critical_alerts(db, severity)
            
            # Format alerts with reorder suggestions
            formatted_alerts = []
            for alert in alerts:
                item_data = format_stock_item(alert)
                
                # Add reorder recommendation
                reorder_qty = calculate_reorder_quantity(
                    avg_daily_usage=alert.avg_daily_usage or 0,
                    lead_time_days=alert.lead_time_days,
                    current_stock=alert.current_stock
                )
                
                item_data["recommended_reorder"] = reorder_qty
                formatted_alerts.append(item_data)
            
            return {
                "success": True,
                "data": {
                    "severity": severity,
                    "count": len(formatted_alerts),
                    "alerts": formatted_alerts
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_summary(db: Session) -> Dict[str, Any]:
        """Get overall statistics"""
        try:
            stock_health = get_latest_stock_health(db)
            
            # Count by status
            critical_count = sum(1 for item in stock_health if item.health_status == "CRITICAL")
            warning_count = sum(1 for item in stock_health if item.health_status == "WARNING")
            healthy_count = sum(1 for item in stock_health if item.health_status == "HEALTHY")
            
            # Get unique counts
            total_locations = len(set(item.location_id for item in stock_health))
            total_items = len(set(item.item_id for item in stock_health))
            
            # Category breakdown
            categories = {}
            for item in stock_health:
                if item.category not in categories:
                    categories[item.category] = {
                        "total": 0,
                        "critical": 0,
                        "warning": 0,
                        "healthy": 0
                    }
                categories[item.category]["total"] += 1
                categories[item.category][item.health_status.lower()] += 1
            
            return {
                "success": True,
                "data": {
                    "overview": {
                        "total_locations": total_locations,
                        "total_items": total_items,
                        "total_records": len(stock_health)
                    },
                    "health_summary": {
                        "critical": critical_count,
                        "warning": warning_count,
                        "healthy": healthy_count
                    },
                    "categories": categories
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }