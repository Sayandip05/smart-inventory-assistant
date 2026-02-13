from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime
from app.database.connection import get_db
from app.database.models import Location, Item
from app.services.inventory_service import InventoryService

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# Request models
class TransactionItem(BaseModel):
    item_id: int
    received: int = Field(ge=0, description="Quantity received (must be >= 0)")
    issued: int = Field(ge=0, description="Quantity issued/used (must be >= 0)")
    notes: Optional[str] = None

class SingleTransactionRequest(BaseModel):
    location_id: int
    item_id: int
    date: date
    received: int = Field(ge=0)
    issued: int = Field(ge=0)
    notes: Optional[str] = None
    entered_by: Optional[str] = "staff"

class BulkTransactionRequest(BaseModel):
    location_id: int
    date: date
    items: List[TransactionItem]
    entered_by: Optional[str] = "staff"

# GET endpoints
@router.get("/locations")
def get_all_locations(db: Session = Depends(get_db)):
    """Get list of all locations"""
    locations = db.query(Location).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": loc.id,
                "name": loc.name,
                "type": loc.type,
                "region": loc.region
            }
            for loc in locations
        ]
    }

@router.get("/items")
def get_all_items(db: Session = Depends(get_db)):
    """Get list of all items"""
    items = db.query(Item).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "unit": item.unit
            }
            for item in items
        ]
    }

@router.get("/location/{location_id}/items")
def get_location_items(
    location_id: int,
    db: Session = Depends(get_db)
):
    """Get all items for a specific location with current stock levels"""
    
    # Verify location exists
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    items = InventoryService.get_location_items(db, location_id)
    
    return {
        "success": True,
        "location": {
            "id": location.id,
            "name": location.name
        },
        "data": items
    }

@router.get("/stock/{location_id}/{item_id}")
def get_current_stock(
    location_id: int,
    item_id: int,
    db: Session = Depends(get_db)
):
    """Get current stock level for a specific item at a location"""
    
    stock = InventoryService.get_latest_stock(db, location_id, item_id)
    
    if stock is None:
        return {
            "success": True,
            "message": "No transaction history found",
            "current_stock": 0
        }
    
    return {
        "success": True,
        "current_stock": stock
    }

# POST endpoints
@router.post("/transaction")
def add_single_transaction(
    request: SingleTransactionRequest,
    db: Session = Depends(get_db)
):
    """
    Add a single inventory transaction
    
    Use this for updating one item at a time
    """
    
    # Validate location exists
    location = db.query(Location).filter(Location.id == request.location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Validate item exists
    item = db.query(Item).filter(Item.id == request.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    result = InventoryService.add_transaction(
        db=db,
        location_id=request.location_id,
        item_id=request.item_id,
        transaction_date=request.date,
        received=request.received,
        issued=request.issued,
        notes=request.notes,
        entered_by=request.entered_by
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result

@router.post("/bulk-transaction")
def add_bulk_transactions(
    request: BulkTransactionRequest,
    db: Session = Depends(get_db)
):
    """
    Add multiple inventory transactions at once
    
    Use this for daily batch entry (multiple items for one location on one date)
    
    Example:
    {
      "location_id": 1,
      "date": "2024-02-13",
      "entered_by": "john_doe",
      "items": [
        {"item_id": 1, "received": 100, "issued": 50},
        {"item_id": 2, "received": 0, "issued": 30},
        {"item_id": 3, "received": 200, "issued": 75}
      ]
    }
    """
    
    # Validate location exists
    location = db.query(Location).filter(Location.id == request.location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Convert to format expected by service
    items_data = [
        {
            "item_id": item.item_id,
            "received": item.received,
            "issued": item.issued,
            "notes": item.notes
        }
        for item in request.items
    ]
    
    result = InventoryService.bulk_add_transactions(
        db=db,
        location_id=request.location_id,
        transaction_date=request.date,
        items_data=items_data,
        entered_by=request.entered_by
    )
    
    return result