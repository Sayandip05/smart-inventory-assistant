"""
Requisition service — business logic layer.

Receives RequisitionRepository and InventoryRepository via the constructor
(injected by FastAPI DI). Contains only business rules; DB queries are
delegated to the repositories.
"""

import logging
from datetime import datetime, date, timezone
from typing import Dict, Any, Optional, List

from app.infrastructure.database.requisition_repo import RequisitionRepository
from app.infrastructure.database.inventory_repo import InventoryRepository
from app.core.exceptions import (
    ValidationError,
    NotFoundError,
    InvalidStateError,
    InsufficientStockError,
    DatabaseError,
)

logger = logging.getLogger("smart_inventory.service.requisition")


class RequisitionService:
    def __init__(self, repo: RequisitionRepository, inv_repo: InventoryRepository):
        self.repo = repo
        self.inv_repo = inv_repo

    def _generate_requisition_number(self) -> str:
        today = datetime.now().strftime("%Y%m%d")
        prefix = f"REQ-{today}-"
        count = self.repo.count_by_prefix(prefix)
        return f"{prefix}{count + 1:03d}"

    @staticmethod
    def _format_requisition(req) -> dict:
        result = {
            "id": req.id,
            "requisition_number": req.requisition_number,
            "location_id": req.location_id,
            "location_name": req.location.name if req.location else None,
            "requested_by": req.requested_by,
            "department": req.department,
            "urgency": req.urgency,
            "status": req.status,
            "approved_by": req.approved_by,
            "rejection_reason": req.rejection_reason,
            "notes": req.notes,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "updated_at": req.updated_at.isoformat() if req.updated_at else None,
            "items": [],
        }

        if req.items:
            for ri in req.items:
                result["items"].append(
                    {
                        "id": ri.id,
                        "item_id": ri.item_id,
                        "item_name": ri.item.name if ri.item else None,
                        "item_unit": ri.item.unit if ri.item else None,
                        "quantity_requested": ri.quantity_requested,
                        "quantity_approved": ri.quantity_approved,
                        "notes": ri.notes,
                    }
                )

        return result

    def create_requisition(
        self,
        location_id: int,
        requested_by: str,
        department: str,
        urgency: str,
        items: List[dict],
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            location = self.repo.get_location(location_id)
            if not location:
                raise NotFoundError("Location", location_id)

            if urgency not in ("LOW", "NORMAL", "HIGH", "EMERGENCY"):
                raise ValidationError(
                    f"Invalid urgency level: {urgency}. Must be LOW, NORMAL, HIGH, or EMERGENCY"
                )

            for item_data in items:
                item = self.repo.get_item(item_data["item_id"])
                if not item:
                    raise NotFoundError("Item", item_data["item_id"])
                if item_data.get("quantity", 0) <= 0:
                    raise ValidationError(
                        f"Quantity must be positive for item {item.name}"
                    )

            req_number = self._generate_requisition_number()
            requisition = self.repo.create(
                requisition_number=req_number,
                location_id=location_id,
                requested_by=requested_by,
                department=department,
                urgency=urgency,
                status="PENDING",
                notes=notes,
            )

            for item_data in items:
                self.repo.add_item(
                    requisition_id=requisition.id,
                    item_id=item_data["item_id"],
                    quantity_requested=item_data["quantity"],
                    notes=item_data.get("notes"),
                )

            self.repo.commit()
            self.repo.refresh(requisition)

            logger.info("Requisition %s created by %s", req_number, requested_by)
            return {
                "success": True,
                "message": f"Requisition {req_number} created successfully",
                "data": self._format_requisition(requisition),
            }

        except (NotFoundError, ValidationError, DatabaseError):
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            logger.error("Unexpected error in create_requisition: %s", str(e))
            raise DatabaseError(f"Failed to create requisition: {str(e)}")

    def list_requisitions(
        self,
        status: Optional[str] = None,
        location_id: Optional[int] = None,
        requested_by: Optional[str] = None,
    ) -> List[dict]:
        requisitions = self.repo.list_all(status, location_id, requested_by)
        return [self._format_requisition(r) for r in requisitions]

    def get_requisition(self, requisition_id: int) -> Optional[dict]:
        requisition = self.repo.get_with_full_details(requisition_id)
        if not requisition:
            return None
        return self._format_requisition(requisition)

    def approve_requisition(
        self,
        requisition_id: int,
        approved_by: str,
        item_adjustments: Optional[List[dict]] = None,
    ) -> Dict[str, Any]:
        try:
            requisition = self.repo.get_by_id(requisition_id, load_items=True)

            if not requisition:
                raise NotFoundError("Requisition", requisition_id)

            if requisition.status != "PENDING":
                raise InvalidStateError(
                    f"Cannot approve: requisition is already {requisition.status}"
                )

            adjustment_map = {}
            if item_adjustments:
                for adj in item_adjustments:
                    adjustment_map[adj["item_id"]] = adj["quantity_approved"]

            stock_errors = []
            for req_item in requisition.items:
                approved_qty = adjustment_map.get(
                    req_item.item_id, req_item.quantity_requested
                )
                req_item.quantity_approved = approved_qty

                latest = self.inv_repo.get_latest_transaction(
                    requisition.location_id, req_item.item_id
                )
                current_stock = latest.closing_stock if latest else 0

                if approved_qty > current_stock:
                    item = self.repo.get_item(req_item.item_id)
                    stock_errors.append(
                        f"{item.name}: requested {approved_qty}, available {current_stock}"
                    )

            if stock_errors:
                raise InsufficientStockError(
                    "Insufficient stock: " + "; ".join(stock_errors)
                )

            from app.application.inventory_service import InventoryService

            inv_service = InventoryService(self.inv_repo)
            today = date.today()

            # ── Atomic batch: flush each deduction, commit once at the end ──
            for req_item in requisition.items:
                if req_item.quantity_approved and req_item.quantity_approved > 0:
                    result = inv_service.add_transaction(
                        location_id=requisition.location_id,
                        item_id=req_item.item_id,
                        transaction_date=today,
                        received=0,
                        issued=req_item.quantity_approved,
                        notes=f"Stock OUT: {requisition.requisition_number} ({requisition.department})",
                        entered_by=f"system/approved-by-{approved_by}",
                        flush_only=True,  # Don't commit individual items
                    )
                    if not result["success"]:
                        raise DatabaseError(
                            f"Stock deduction failed: {result.get('error')}"
                        )

            requisition.status = "APPROVED"
            requisition.approved_by = approved_by
            requisition.approved_at = datetime.now(timezone.utc)
            self.repo.commit()  # Single atomic commit for all items

            logger.info(
                "Requisition %s approved by %s",
                requisition.requisition_number,
                approved_by,
            )
            return {
                "success": True,
                "message": f"Requisition {requisition.requisition_number} approved. Stock deducted.",
                "data": self._format_requisition(requisition),
            }

        except (
            NotFoundError,
            InvalidStateError,
            InsufficientStockError,
            DatabaseError,
        ):
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            logger.error("Unexpected error in approve_requisition: %s", str(e))
            raise DatabaseError(f"Failed to approve requisition: {str(e)}")

    def reject_requisition(
        self, requisition_id: int, rejected_by: str, reason: str
    ) -> Dict[str, Any]:
        try:
            requisition = self.repo.get_by_id(requisition_id)

            if not requisition:
                raise NotFoundError("Requisition", requisition_id)

            if requisition.status != "PENDING":
                raise InvalidStateError(
                    f"Cannot reject: requisition is already {requisition.status}"
                )

            requisition.status = "REJECTED"
            requisition.approved_by = rejected_by
            requisition.rejection_reason = reason
            requisition.rejected_at = datetime.now(timezone.utc)
            self.repo.commit()

            logger.info(
                "Requisition %s rejected by %s",
                requisition.requisition_number,
                rejected_by,
            )
            return {
                "success": True,
                "message": f"Requisition {requisition.requisition_number} rejected.",
            }

        except (NotFoundError, InvalidStateError, DatabaseError):
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            logger.error("Unexpected error in reject_requisition: %s", str(e))
            raise DatabaseError(f"Failed to reject requisition: {str(e)}")

    def cancel_requisition(
        self, requisition_id: int, cancelled_by: str
    ) -> Dict[str, Any]:
        try:
            requisition = self.repo.get_by_id(requisition_id)

            if not requisition:
                raise NotFoundError("Requisition", requisition_id)

            if requisition.status != "PENDING":
                raise InvalidStateError("Only PENDING requisitions can be cancelled")

            requisition.status = "CANCELLED"
            self.repo.commit()

            return {
                "success": True,
                "message": f"Requisition {requisition.requisition_number} cancelled.",
            }

        except (NotFoundError, InvalidStateError, DatabaseError):
            self.repo.rollback()
            raise
        except Exception as e:
            self.repo.rollback()
            logger.error("Unexpected error in cancel_requisition: %s", str(e))
            raise DatabaseError(f"Failed to cancel requisition: {str(e)}")

    def get_stats(self) -> dict:
        return {
            "total": self.repo.count_total(),
            "pending": self.repo.count_by_status("PENDING"),
            "approved_today": self.repo.count_approved_today(),
            "rejected": self.repo.count_by_status("REJECTED"),
            "emergency_pending": self.repo.count_emergency_pending(),
        }
