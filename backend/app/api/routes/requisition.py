"""
Requisition API routes.

Routes receive pre-configured RequisitionService via FastAPI's Depends() system.
"""

from fastapi import APIRouter, Depends
from typing import Optional

from app.core.dependencies import get_requisition_service
from app.core.exceptions import NotFoundError, ValidationError
from app.application.requisition_service import RequisitionService
from app.api.schemas.requisition_schemas import (
    RequisitionItemCreate,
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
):
    items_data = [
        {"item_id": item.item_id, "quantity": item.quantity, "notes": item.notes}
        for item in request.items
    ]

    result = service.create_requisition(
        location_id=request.location_id,
        requested_by=request.requested_by,
        department=request.department,
        urgency=request.urgency,
        items=items_data,
        notes=request.notes,
    )

    if not result["success"]:
        raise ValidationError(result["error"])

    return result


@router.get("/list")
def list_requisitions(
    status: Optional[str] = None,
    location_id: Optional[int] = None,
    requested_by: Optional[str] = None,
    service: RequisitionService = Depends(get_requisition_service),
):
    data = service.list_requisitions(
        status=status, location_id=location_id, requested_by=requested_by
    )
    return {"success": True, "data": data, "count": len(data)}


@router.get("/stats")
def get_requisition_stats(
    service: RequisitionService = Depends(get_requisition_service),
):
    stats = service.get_stats()
    return {"success": True, "data": stats}


@router.get("/{requisition_id}")
def get_requisition(
    requisition_id: int,
    service: RequisitionService = Depends(get_requisition_service),
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
):
    result = service.approve_requisition(
        requisition_id=requisition_id,
        approved_by=request.approved_by,
        item_adjustments=request.item_adjustments,
    )

    if not result["success"]:
        raise ValidationError(result["error"])

    return result


@router.put("/{requisition_id}/reject")
def reject_requisition(
    requisition_id: int,
    request: RejectRequest,
    service: RequisitionService = Depends(get_requisition_service),
):
    result = service.reject_requisition(
        requisition_id=requisition_id,
        rejected_by=request.rejected_by,
        reason=request.reason,
    )

    if not result["success"]:
        raise ValidationError(result["error"])

    return result


@router.put("/{requisition_id}/cancel")
def cancel_requisition(
    requisition_id: int,
    request: CancelRequest,
    service: RequisitionService = Depends(get_requisition_service),
):
    result = service.cancel_requisition(
        requisition_id=requisition_id,
        cancelled_by=request.cancelled_by,
    )

    if not result["success"]:
        raise ValidationError(result["error"])

    return result
