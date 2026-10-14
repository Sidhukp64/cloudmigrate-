import hashlib
import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.audit import AuditLog, AuditAction


def _compute_checksum(record: dict) -> str:
    """SHA-256 checksum for tamper detection."""
    payload = json.dumps(record, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def log_event(
    db: Session,
    action: AuditAction,
    actor_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditLog:
    """Write an immutable audit log entry with tamper-detection checksum."""
    record = {
        "action": action.value,
        "actor_id": str(actor_id) if actor_id else None,
        "actor_email": actor_email,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "details": details or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    checksum = _compute_checksum(record)

    log = AuditLog(
        action=action,
        actor_id=actor_id,
        actor_email=actor_email,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        checksum=checksum,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def verify_checksum(log: AuditLog) -> bool:
    """Verify an audit log entry hasn't been tampered with."""
    record = {
        "action": log.action.value,
        "actor_id": str(log.actor_id) if log.actor_id else None,
        "actor_email": log.actor_email,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "details": log.details or {},
        "timestamp": log.created_at.isoformat() if log.created_at else None,
    }
    expected = _compute_checksum(record)
    return log.checksum == expected
