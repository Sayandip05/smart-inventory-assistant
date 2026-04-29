"""
Admin Dashboard API — Super Admin endpoints for platform management.

Provides overview stats, user management summaries, and audit trail
access for the platform owner's dashboard.
"""

import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_db, require_admin
from app.infrastructure.database.models import User, AuditLog
from app.infrastructure.database.user_repo import UserRepository
from app.infrastructure.database.audit_repo import AuditRepository

logger = logging.getLogger("smart_inventory.admin")

router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


# ── GET /admin/overview ────────────────────────────────────────────────────


@router.get("/overview", response_model=dict)
def get_platform_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Super Admin overview — quick stats for the entire platform.
    Shows total users, active/inactive counts, role breakdown, recent activity.
    """
    user_repo = UserRepository(db)

    total_users = user_repo.count()
    active_users = user_repo.count_filtered(is_active=True)
    inactive_users = user_repo.count_filtered(is_active=False)

    # Role breakdown
    role_counts = {}
    for role in ["admin", "manager", "staff", "viewer"]:
        role_counts[role] = user_repo.count_filtered(role=role)

    # Recent signups (last 7 days)
    recent_users = user_repo.get_all_filtered(limit=5)
    recent_signups = [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": str(u.created_at) if u.created_at else None,
        }
        for u in recent_users
    ]

    # Recent audit events
    audit_repo = AuditRepository(db)
    recent_events = audit_repo.get_recent(limit=10)
    recent_activity = [
        {
            "action": e.action,
            "username": e.username,
            "resource_type": e.resource_type,
            "resource_id": e.resource_id,
            "created_at": str(e.created_at) if e.created_at else None,
            "ip_address": e.ip_address,
        }
        for e in recent_events
    ]

    return {
        "success": True,
        "data": {
            "users": {
                "total": total_users,
                "active": active_users,
                "inactive": inactive_users,
                "by_role": role_counts,
            },
            "recent_signups": recent_signups,
            "recent_activity": recent_activity,
        },
    }


# ── GET /admin/audit-logs ─────────────────────────────────────────────────


@router.get("/audit-logs", response_model=dict)
def get_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    username: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    View audit trail — filterable by user, action type, or resource.
    This is the core compliance tool for the super admin.
    """
    audit_repo = AuditRepository(db)

    if username:
        logs = audit_repo.get_by_user(username, limit=limit)
    else:
        logs = audit_repo.get_recent(limit=limit)

    # Apply additional filters in-memory (small dataset)
    if action:
        logs = [l for l in logs if l.action == action]
    if resource_type:
        logs = [l for l in logs if l.resource_type == resource_type]

    return {
        "success": True,
        "data": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "username": log.username,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "created_at": str(log.created_at) if log.created_at else None,
            }
            for log in logs
        ],
        "total": len(logs),
    }


# ── GET /admin/users/summary ──────────────────────────────────────────────


@router.get("/users/summary", response_model=dict)
def get_users_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Detailed user summary for the super admin user management section.
    """
    user_repo = UserRepository(db)
    all_users = user_repo.get_all()

    users_data = []
    for u in all_users:
        users_data.append(
            {
                "id": u.id,
                "email": u.email,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "is_verified": u.is_verified,
                "login_attempts": u.login_attempts or 0,
                "locked_until": str(u.locked_until) if u.locked_until else None,
                "last_login_at": str(u.last_login_at) if u.last_login_at else None,
                "created_at": str(u.created_at) if u.created_at else None,
                "updated_at": str(u.updated_at) if u.updated_at else None,
            }
        )

    # Identify concerns
    locked_users = [u for u in users_data if u["locked_until"] is not None]
    never_logged_in = [
        u for u in users_data if u["last_login_at"] is None and u["role"] != "admin"
    ]

    return {
        "success": True,
        "data": {
            "all_users": users_data,
            "total": len(users_data),
            "alerts": {
                "locked_accounts": locked_users,
                "never_logged_in": never_logged_in,
            },
        },
    }


# ── GET /admin/reports/generate ────────────────────────────────────────────


@router.get("/reports/generate")
def generate_pdf_report(
    date_from: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Generate a PDF inventory report.

    Includes:
      - Stock health summary (critical/warning/healthy)
      - Top critical items
      - Requisition summary
      - Generated metadata (who, when)
    """
    from io import BytesIO
    from fastapi.responses import StreamingResponse
    from app.infrastructure.database.models import (
        Location,
        Item,
        InventoryTransaction,
        Requisition,
    )

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate,
            Table,
            TableStyle,
            Paragraph,
            Spacer,
        )
        from reportlab.lib.styles import getSampleStyleSheet
    except ImportError:
        raise HTTPException(
            status_code=500, detail="reportlab is not installed on the server"
        )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph("InvIQ — Inventory Report", styles["Title"]))
    elements.append(
        Paragraph(
            f"Generated by: {current_user.username} | Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 0.3 * inch))

    # Stock health summary
    items = db.query(Item).all()
    locations = db.query(Location).all()
    critical, warning, healthy = 0, 0, 0

    critical_items = []
    for item in items:
        # Get latest transaction for this item (any location)
        latest = (
            db.query(InventoryTransaction)
            .filter(InventoryTransaction.item_id == item.id)
            .order_by(InventoryTransaction.date.desc())
            .first()
        )
        stock = latest.closing_stock if latest else 0
        if stock <= 0:
            critical += 1
            critical_items.append((item.name, stock, item.min_stock))
        elif stock <= item.min_stock:
            warning += 1
            critical_items.append((item.name, stock, item.min_stock))
        else:
            healthy += 1

    elements.append(Paragraph("Stock Health Summary", styles["Heading2"]))
    health_data = [
        ["Status", "Count"],
        ["🔴 Critical (stock = 0)", str(critical)],
        ["🟡 Warning (below min)", str(warning)],
        ["🟢 Healthy", str(healthy)],
        ["Total Items", str(len(items))],
    ]
    health_table = Table(health_data, colWidths=[3 * inch, 1.5 * inch])
    health_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(health_table)
    elements.append(Spacer(1, 0.3 * inch))

    # Top critical items
    if critical_items:
        elements.append(Paragraph("Critical / Warning Items", styles["Heading2"]))
        ci_data = [["Item Name", "Current Stock", "Min Required"]]
        for name, stock, min_s in critical_items[:15]:
            ci_data.append([name, str(stock), str(min_s)])
        ci_table = Table(ci_data, colWidths=[3 * inch, 1 * inch, 1.2 * inch])
        ci_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ]
            )
        )
        elements.append(ci_table)
        elements.append(Spacer(1, 0.3 * inch))

    # Requisition summary
    elements.append(Paragraph("Requisition Summary", styles["Heading2"]))
    total_req = db.query(Requisition).count()
    pending = db.query(Requisition).filter(Requisition.status == "PENDING").count()
    approved = db.query(Requisition).filter(Requisition.status == "APPROVED").count()
    rejected = db.query(Requisition).filter(Requisition.status == "REJECTED").count()

    req_data = [
        ["Status", "Count"],
        ["Total", str(total_req)],
        ["Pending", str(pending)],
        ["Approved", str(approved)],
        ["Rejected", str(rejected)],
    ]
    req_table = Table(req_data, colWidths=[3 * inch, 1.5 * inch])
    req_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(req_table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    filename = (
        f"inventory_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.pdf"
    )

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
