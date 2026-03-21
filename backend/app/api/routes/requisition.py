"""
Requisition API routes.

Routes receive pre-configured RequisitionService via FastAPI's Depends() system.
"""

from fastapi import APIRouter, Depends
from typing import Optional

from app.core.dependencies import (
    get_requisition_service,
    get_current_user,
    require_staff,
    require_manager,
)
from app.core.exceptions import NotFoundError
from app.application.requisition_service import RequisitionService
from app.infrastructure.database.models import User
from app.api.schemas.requisition_schemas import (
    CreateRequisitionRequest,
    ApproveRequest,
    RejectRequest,
    CancelRequest,
)

router = APIRouter(prefix="/requisition", tags=["Requisition"])


@router.post("/create")
def create_requisition(
    request: CreateRequisitionRequest,
    service: RequisitionService = Depends(get_requisition_service),
    current_user: User = Depends(require_staff),
):
    items_data = [
        {"item_id": item.item_id, "quantity": item.quantity, "notes": item.notes}
        for item in request.items
    ]

    return service.create_requisition(
        location_id=request.location_id,
        requested_by=current_user.username,
        department=request.department,
        urgency=request.urgency,
        items=items_data,
        notes=request.notes,
    )


@router.get("/list")
def list_requisitions(
    status: Optional[str] = None,
    location_id: Optional[int] = None,
    requested_by: Optional[str] = None,
    service: RequisitionService = Depends(get_requisition_service),
    current_user: User = Depends(get_current_user),
):
    data = service.list_requisitions(
        status=status, location_id=location_id, requested_by=requested_by
    )
    return {"success": True, "data": data, "count": len(data)}


@router.get("/stats")
def get_requisition_stats(
    service: RequisitionService = Depends(get_requisition_service),
    current_user: User = Depends(get_current_user),
):
    stats = service.get_stats()
    return {"success": True, "data": stats}


@router.get("/{requisition_id}")
def get_requisition(
    requisition_id: int,
    service: RequisitionService = Depends(get_requisition_service),
    current_user: User = Depends(get_current_user),
):
    data = service.get_requisition(requisition_id)
    if not data:
        raise NotFoundError("Requisition", requisition_id)
    return {"success": True, "data": data}


@router.put("/{requisition_id}/approve")
def approve_requisition(
    requisition_id: int,
    request: ApproveRequest,
    service: RequisitionService = Depends(get_requisition_service),
    current_user: User = Depends(require_manager),
):
    return service.approve_requisition(
        requisition_id=requisition_id,
        approved_by=str(current_user.username),
        item_adjustments=request.item_adjustments,
    )


@router.put("/{requisition_id}/reject")
def reject_requisition(
    requisition_id: int,
    request: RejectRequest,
    service: RequisitionService = Depends(get_requisition_service),
    current_user: User = Depends(require_manager),
):
    return service.reject_requisition(
        requisition_id=requisition_id,
        rejected_by=str(current_user.username),
        reason=request.reason,
    )


@router.put("/{requisition_id}/cancel")
def cancel_requisition(
    requisition_id: int,
    request: CancelRequest,
    service: RequisitionService = Depends(get_requisition_service),
    current_user: User = Depends(require_staff),
):
    return service.cancel_requisition(
        requisition_id=requisition_id,
        cancelled_by=str(current_user.username),
    )
