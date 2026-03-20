"""
Inventory API routes.

Routes receive pre-configured services via FastAPI's Depends() system.
No direct DB queries here — everything goes through the service layer.
"""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_inventory_service, get_inventory_repo
from app.core.exceptions import (
    NotFoundError,
    DuplicateError,
    ValidationError,
    AppException,
)
from app.application.inventory_service import InventoryService
from app.infrastructure.database.inventory_repo import InventoryRepository
from app.api.schemas.inventory_schemas import (
    TransactionItem,
    SingleTransactionRequest,
    BulkTransactionRequest,
    CreateLocationRequest,
    CreateItemRequest,
    ResetDataRequest,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("/locations")
def get_all_locations(repo: InventoryRepository = Depends(get_inventory_repo)):
    locations = repo.get_all_locations()
    return {
        "success": True,
        "data": [
            {"id": loc.id, "name": loc.name, "type": loc.type, "region": loc.region}
            for loc in locations
        ],
    }


@router.get("/items")
def get_all_items(repo: InventoryRepository = Depends(get_inventory_repo)):
    items = repo.get_all_items()
    return {
        "success": True,
        "data": [
            {
                "id": item.id,
                "name": item.name,
                "category": item.category,
                "unit": item.unit,
            }
            for item in items
        ],
    }


@router.get("/location/{location_id}/items")
def get_location_items(
    location_id: int,
    repo: InventoryRepository = Depends(get_inventory_repo),
    service: InventoryService = Depends(get_inventory_service),
):
    location = repo.get_location_by_id(location_id)
    if not location:
        raise NotFoundError("Location", location_id)

    items = service.get_location_items(location_id)
    return {
        "success": True,
        "location": {"id": location.id, "name": location.name},
        "data": items,
    }


@router.get("/stock/{location_id}/{item_id}")
def get_current_stock(
    location_id: int,
    item_id: int,
    service: InventoryService = Depends(get_inventory_service),
):
    stock = service.get_latest_stock(location_id, item_id)

    if stock is None:
        return {
            "success": True,
            "message": "No transaction history found",
            "current_stock": 0,
        }

    return {"success": True, "current_stock": stock}


@router.post("/locations")
def create_location(
    request: CreateLocationRequest,
    repo: InventoryRepository = Depends(get_inventory_repo),
):
    existing = repo.get_location_by_name(request.name.strip())
    if existing:
        raise DuplicateError(f"Location '{request.name}' already exists")

    location = repo.create_location(
        name=request.name.strip(),
        type=request.type.strip().lower(),
        region=request.region.strip(),
        address=request.address.strip() if request.address else None,
    )

    return {
        "success": True,
        "message": "Location created successfully",
        "data": {
            "id": location.id,
            "name": location.name,
            "type": location.type,
            "region": location.region,
            "address": location.address,
        },
    }


@router.post("/items")
def create_item(
    request: CreateItemRequest,
    repo: InventoryRepository = Depends(get_inventory_repo),
):
    existing = repo.get_item_by_name(request.name.strip())
    if existing:
        raise DuplicateError(f"Item '{request.name}' already exists")

    item = repo.create_item(
        name=request.name.strip(),
        category=request.category.strip().lower(),
        unit=request.unit.strip().lower(),
        lead_time_days=request.lead_time_days,
        min_stock=request.min_stock,
    )

    return {
        "success": True,
        "message": "Item created successfully",
        "data": {
            "id": item.id,
            "name": item.name,
            "category": item.category,
            "unit": item.unit,
            "lead_time_days": item.lead_time_days,
            "min_stock": item.min_stock,
        },
    }


@router.post("/reset-data")
def reset_inventory_data(
    request: ResetDataRequest,
    repo: InventoryRepository = Depends(get_inventory_repo),
):
    if not request.confirm:
        raise ValidationError("Set confirm=true to reset data")

    try:
        deleted_transactions = repo.delete_all_transactions()
        deleted_items = repo.delete_all_items()
        deleted_locations = repo.delete_all_locations()
        repo.commit()
    except Exception as e:
        repo.rollback()
        raise AppException(str(e))

    return {
        "success": True,
        "message": "All inventory data cleared",
        "data": {
            "deleted_transactions": deleted_transactions,
            "deleted_items": deleted_items,
            "deleted_locations": deleted_locations,
        },
    }


@router.post("/transaction")
def add_single_transaction(
    request: SingleTransactionRequest,
    repo: InventoryRepository = Depends(get_inventory_repo),
    service: InventoryService = Depends(get_inventory_service),
):
    if not repo.get_location_by_id(request.location_id):
        raise NotFoundError("Location", request.location_id)
    if not repo.get_item_by_id(request.item_id):
        raise NotFoundError("Item", request.item_id)

    result = service.add_transaction(
        location_id=request.location_id,
        item_id=request.item_id,
        transaction_date=request.date,
        received=request.received,
        issued=request.issued,
        notes=request.notes,
        entered_by=request.entered_by or "staff",
    )

    if not result["success"]:
        raise ValidationError(result["error"])

    return result


@router.post("/bulk-transaction")
def add_bulk_transactions(
    request: BulkTransactionRequest,
    repo: InventoryRepository = Depends(get_inventory_repo),
    service: InventoryService = Depends(get_inventory_service),
):
    if not repo.get_location_by_id(request.location_id):
        raise NotFoundError("Location", request.location_id)

    items_data = [
        {
            "item_id": item.item_id,
            "received": item.received,
            "issued": item.issued,
            "notes": item.notes,
        }
        for item in request.items
    ]

    return service.bulk_add_transactions(
        location_id=request.location_id,
        transaction_date=request.date,
        items_data=items_data,
        entered_by=request.entered_by or "staff",
    )
