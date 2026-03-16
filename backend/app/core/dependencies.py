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

from app.database.connection import get_db
from app.repositories.inventory_repo import InventoryRepository
from app.repositories.requisition_repo import RequisitionRepository
from app.services.inventory_service import InventoryService
from app.services.requisition_service import RequisitionService


def get_inventory_repo(db: Session = Depends(get_db)) -> InventoryRepository:
    """Provide an InventoryRepository bound to the current request's DB session."""
    return InventoryRepository(db)


def get_requisition_repo(db: Session = Depends(get_db)) -> RequisitionRepository:
    """Provide a RequisitionRepository bound to the current request's DB session."""
    return RequisitionRepository(db)


def get_inventory_service(
    repo: InventoryRepository = Depends(get_inventory_repo),
) -> InventoryService:
    """Provide an InventoryService wired with its repository."""
    return InventoryService(repo)


def get_requisition_service(
    repo: RequisitionRepository = Depends(get_requisition_repo),
    inv_repo: InventoryRepository = Depends(get_inventory_repo),
) -> RequisitionService:
    """Provide a RequisitionService wired with its repository + inventory repo."""
    return RequisitionService(repo, inv_repo)
