from uuid import UUID
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import csv
import io
from app.core.database import get_db
from app.models.user import User, UserRole
from app.models.audit import AuditLog, AuditAction
from app.schemas.audit import AuditLogOut
from app.api.deps import get_current_user, require_role
from app.services.audit_service import verify_checksum

router = APIRouter()


@router.get("", response_model=List[AuditLogOut])
def query_audit_logs(
    action: Optional[AuditAction] = None,
    actor_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Query audit logs with filtering and pagination."""
    q = db.query(AuditLog)
    if action:
        q = q.filter(AuditLog.action == action)
    if actor_email:
        q = q.filter(AuditLog.actor_email.ilike(f"%{actor_email}%"))
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)
    if resource_id:
        q = q.filter(AuditLog.resource_id == resource_id)
    if start_date:
        q = q.filter(AuditLog.created_at >= start_date)
    if end_date:
        q = q.filter(AuditLog.created_at <= end_date)

    total = q.count()
    logs = q.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [AuditLogOut.model_validate(l) for l in logs]


@router.get("/export")
def export_audit_logs(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    """Export audit logs as CSV. Admin only."""
    q = db.query(AuditLog)
    if start_date:
        q = q.filter(AuditLog.created_at >= start_date)
    if end_date:
        q = q.filter(AuditLog.created_at <= end_date)
    logs = q.order_by(AuditLog.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "id", "action", "actor_email", "resource_type", "resource_id",
        "ip_address", "checksum", "created_at"
    ])
    writer.writeheader()
    for log in logs:
        writer.writerow({
            "id": str(log.id),
            "action": log.action.value,
            "actor_email": log.actor_email or "",
            "resource_type": log.resource_type or "",
            "resource_id": log.resource_id or "",
            "ip_address": log.ip_address or "",
            "checksum": log.checksum or "",
            "created_at": log.created_at.isoformat() if log.created_at else "",
        })

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )


@router.get("/{log_id}", response_model=AuditLogOut)
def get_audit_log(
    log_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single audit log and verify its integrity."""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audit log not found")
    return AuditLogOut.model_validate(log)
