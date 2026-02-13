from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from typing import Dict, Any, Optional
from app.database.models import InventoryTransaction, Location, Item

class InventoryService:
    
    @staticmethod
    def add_transaction(
        db: Session,
        location_id: int,
        item_id: int,
        transaction_date: date,
        received: int,
        issued: int,
        notes: Optional[str] = None,
        entered_by: str = "staff"
    ) -> Dict[str, Any]:
        """
        Add a new inventory transaction
        
        Automatically calculates opening_stock and closing_stock
        """
        try:
            # Get previous day's closing stock as opening stock
            previous_transaction = (
                db.query(InventoryTransaction)
                .filter(
                    InventoryTransaction.location_id == location_id,
                    InventoryTransaction.item_id == item_id,
                    InventoryTransaction.date < transaction_date
                )
                .order_by(InventoryTransaction.date.desc())
                .first()
            )
            
            # If no previous record, start with 0 or use item's min_stock
            if previous_transaction:
                opening_stock = previous_transaction.closing_stock
            else:
                item = db.query(Item).filter(Item.id == item_id).first()
                opening_stock = item.min_stock if item else 0
            
            # Calculate closing stock
            closing_stock = opening_stock + received - issued
            
            # Validate closing stock
            if closing_stock < 0:
                return {
                    "success": False,
                    "error": f"Invalid transaction: closing stock cannot be negative (would be {closing_stock})"
                }
            
            # Create transaction
            new_transaction = InventoryTransaction(
                location_id=location_id,
                item_id=item_id,
                date=transaction_date,
                opening_stock=opening_stock,
                received=received,
                issued=issued,
                closing_stock=closing_stock,
                notes=notes,
                entered_by=entered_by
            )
            
            db.add(new_transaction)
            db.commit()
            db.refresh(new_transaction)
            
            return {
                "success": True,
                "message": "Transaction added successfully",
                "data": {
                    "id": new_transaction.id,
                    "opening_stock": opening_stock,
                    "received": received,
                    "issued": issued,
                    "closing_stock": closing_stock,
                    "date": str(transaction_date)
                }
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def bulk_add_transactions(
        db: Session,
        location_id: int,
        transaction_date: date,
        items_data: list,
        entered_by: str = "staff"
    ) -> Dict[str, Any]:
        """
        Add multiple transactions at once (for daily batch entry)
        
        items_data format: [
            {"item_id": 1, "received": 100, "issued": 50},
            {"item_id": 2, "received": 0, "issued": 30},
            ...
        ]
        """
        try:
            results = []
            errors = []
            
            for item_data in items_data:
                result = InventoryService.add_transaction(
                    db=db,
                    location_id=location_id,
                    item_id=item_data["item_id"],
                    transaction_date=transaction_date,
                    received=item_data.get("received", 0),
                    issued=item_data.get("issued", 0),
                    notes=item_data.get("notes"),
                    entered_by=entered_by
                )
                
                if result["success"]:
                    results.append(result["data"])
                else:
                    errors.append({
                        "item_id": item_data["item_id"],
                        "error": result["error"]
                    })
            
            return {
                "success": len(errors) == 0,
                "message": f"Processed {len(results)} transactions, {len(errors)} errors",
                "data": {
                    "successful": results,
                    "failed": errors
                }
            }
            
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_latest_stock(
        db: Session,
        location_id: int,
        item_id: int
    ) -> Optional[int]:
        """Get most recent closing stock for an item at a location"""
        latest = (
            db.query(InventoryTransaction)
            .filter(
                InventoryTransaction.location_id == location_id,
                InventoryTransaction.item_id == item_id
            )
            .order_by(InventoryTransaction.date.desc())
            .first()
        )
        
        return latest.closing_stock if latest else None
    
    @staticmethod
    def get_location_items(
        db: Session,
        location_id: int
    ) -> list:
        """Get all items for a location with their current stock"""
        # Get all items
        items = db.query(Item).all()
        
        result = []
        for item in items:
            latest_stock = InventoryService.get_latest_stock(db, location_id, item.id)
            result.append({
                "item_id": item.id,
                "item_name": item.name,
                "category": item.category,
                "unit": item.unit,
                "current_stock": latest_stock or 0
            })
        
        return result