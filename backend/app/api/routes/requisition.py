"""
Requisition API routes.

Routes receive pre-configured RequisitionService via FastAPI's Depends() system.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.dependencies import get_requisition_service
from app.core.exceptions import NotFoundError, ValidationError
from app.services.requisition_service import RequisitionService

router = APIRouter(prefix="/requisition", tags=["Requisition"])


# ─── Request Models ───

class RequisitionItemCreate(BaseModel):
    item_id: int
    quantity: int = Field(gt=0, description="Quantity requested")
    notes: Optional[str] = None


class CreateRequisitionRequest(BaseModel):
    location_id: int
    requested_by: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=2, max_length=100)
    urgency: str = Field(default="NORMAL", pattern="^(LOW|NORMAL|HIGH|EMERGENCY)$")
    items: List[RequisitionItemCreate] = Field(min_length=1)
    notes: Optional[str] = None


class ApproveRequest(BaseModel):
    approved_by: str = Field(min_length=2, max_length=100)
    item_adjustments: Optional[List[dict]] = None


class RejectRequest(BaseModel):
    rejected_by: str = Field(min_length=2, max_length=100)
    reason: str = Field(min_length=5, max_length=500)


class CancelRequest(BaseModel):
    cancelled_by: str = Field(min_length=2, max_length=100)


# ─── Endpoints ───

@router.post("/create")
def create_requisition(
    request: CreateRequisitionRequest,
    service: RequisitionService = Depends(get_requisition_service),
):
    """Raise a new stock-out requisition (Department Staff)."""
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
    """List all requisitions (filter by status, location, or requester)."""
    data = service.list_requisitions(
        status=status, location_id=location_id, requested_by=requested_by
    )
    return {"success": True, "data": data, "count": len(data)}


@router.get("/stats")
def get_requisition_stats(
    service: RequisitionService = Depends(get_requisition_service),
):
    """Get summary counts for the requisition dashboard."""
    stats = service.get_stats()
    return {"success": True, "data": stats}


@router.get("/{requisition_id}")
def get_requisition(
    requisition_id: int,
    service: RequisitionService = Depends(get_requisition_service),
):
    """Get full details of a single requisition."""
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
    """Approve a pending requisition and auto-deduct stock (Store Manager)."""
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
    """Reject a pending requisition with a reason (Store Manager)."""
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
    """Cancel own pending requisition (Department Staff)."""
    result = service.cancel_requisition(
        requisition_id=requisition_id,
        cancelled_by=request.cancelled_by,
    )

    if not result["success"]:
        raise ValidationError(result["error"])

    return result
