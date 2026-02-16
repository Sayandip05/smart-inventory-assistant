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

    @staticmethod
    def get_dashboard_stats(db: Session) -> Dict[str, Any]:
        """Get aggregated statistics for dashboard charts"""
        try:
            stock_health = get_latest_stock_health(db)
            
            # 1. Category Distribution (Pie Chart)
            category_counts = {}
            for item in stock_health:
                category_counts[item.category] = category_counts.get(item.category, 0) + 1
            
            category_data = [
                {"name": cat, "value": count} 
                for cat, count in category_counts.items()
            ]
            
            # 2. Low Stock Items (Bar Chart)
            # Filter items where current_stock < min_stock
            low_stock_items = [
                item for item in stock_health 
                if item.current_stock < item.min_stock
            ]
            # Sort by severity of shortage (percentage)
            low_stock_items.sort(key=lambda x: x.current_stock / x.min_stock if x.min_stock > 0 else 1)
            
            low_stock_data = [
                {
                    "name": item.item_name,
                    "stock": item.current_stock,
                    "min_stock": item.min_stock,
                    "shortage": item.min_stock - item.current_stock
                }
                for item in low_stock_items[:5] # Top 5
            ]
            
            # 3. Stock Value by Location (Bar Chart)
            # Assuming value = quantity for now since we don't have price
            location_stock = {}
            for item in stock_health:
                location_stock[item.location_name] = location_stock.get(item.location_name, 0) + item.current_stock
                
            location_data = [
                {"name": loc, "value": qty}
                for loc, qty in location_stock.items()
            ]

            # 4. Stock Health Status (Pie Chart)
            status_counts = {"CRITICAL": 0, "WARNING": 0, "HEALTHY": 0}
            for item in stock_health:
                status_counts[item.health_status] += 1
                
            status_data = [
                {"name": status, "value": count, "color": "#ef4444" if status == "CRITICAL" else "#f59e0b" if status == "WARNING" else "#22c55e"}
                for status, count in status_counts.items()
                if count > 0
            ]
            
            return {
                "success": True,
                "data": {
                    "category_distribution": category_data,
                    "low_stock_items": low_stock_data,
                    "location_stock": location_data,
                    "status_distribution": status_data
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }