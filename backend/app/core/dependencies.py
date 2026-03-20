"""
FastAPI dependency injection factories.

Route handlers use Depends() to receive pre-configured service instances
instead of creating them manually. This decouples routes from implementation
details and makes testing easy (swap repos with mocks).

Usage in routes:
    from app.core.dependencies import get_inventory_service

    @router.get("/items")
    def list_items(service: InventoryService = Depends(get_inventory_service)):
        return service.get_all_items()
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.infrastructure.database.connection import get_db
from app.infrastructure.database.inventory_repo import InventoryRepository
from app.infrastructure.database.requisition_repo import RequisitionRepository
from app.application.inventory_service import InventoryService
from app.application.requisition_service import RequisitionService


def get_inventory_repo(db: Session = Depends(get_db)) -> InventoryRepository:
    return InventoryRepository(db)


def get_requisition_repo(db: Session = Depends(get_db)) -> RequisitionRepository:
    return RequisitionRepository(db)


def get_inventory_service(
    repo: InventoryRepository = Depends(get_inventory_repo),
) -> InventoryService:
    return InventoryService(repo)


def get_requisition_service(
    repo: RequisitionRepository = Depends(get_requisition_repo),
    inv_repo: InventoryRepository = Depends(get_inventory_repo),
) -> RequisitionService:
    return RequisitionService(repo, inv_repo)
